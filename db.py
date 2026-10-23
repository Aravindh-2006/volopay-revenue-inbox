"""
Database module — SQLite schema creation and helper functions.

This module handles all database operations for the Revenue Intelligence Inbox:
- Creating tables for source records, routes, overrides, review states
- Importing JSON batch data with deduplication and revision handling
- Querying records for the dashboard and inbox views
- Managing route suggestions and manual overrides

All queries use parameterised SQL (? placeholders) to prevent SQL injection.
"""

import sqlite3
import json
import os
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Path to the SQLite database file.  It is created next to this source file
# inside the project folder so it is easy to find and delete for a reset.
# ---------------------------------------------------------------------------
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inbox.db")


def get_supabase_client():
    """Return an active Supabase client if configured in .streamlit/secrets.toml, else None."""
    try:
        import toml, supabase
        secrets_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".streamlit", "secrets.toml")
        if os.path.exists(secrets_path):
            s = toml.load(secrets_path)
            sb_cfg = s.get("supabase", {})
            if sb_cfg.get("url") and sb_cfg.get("key"):
                return supabase.create_client(sb_cfg["url"], sb_cfg["key"])
    except Exception:
        pass
    return None



def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    """Return a connection to the SQLite database with row-factory enabled."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """Create all tables if they do not already exist.

    Tables
    ------
    source_records  – one row per unique (source_type, source_id)
    route_suggestions – automated route suggestions (can be many per record)
    route_overrides – manual manager corrections (one active per record)
    import_log – tracks which batches have been imported
    """
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS source_records (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        source_type         TEXT NOT NULL,           -- 'call' or 'meeting'
        source_id           TEXT NOT NULL,            -- UUID from the data
        record_ref          TEXT,                     -- human label like B01, C03, M07
        revision            INTEGER NOT NULL DEFAULT 1,
        batch_id            TEXT,
        payload_json        TEXT NOT NULL,            -- full payload as JSON string
        transcript_json     TEXT,                     -- transcript_payload as JSON string (null = none)
        has_usable_transcript INTEGER NOT NULL DEFAULT 0,  -- 1 if transcript text exists
        rep_name            TEXT,                     -- extracted for filtering
        rep_email           TEXT,
        organizer_email     TEXT,                     -- for meetings
        direction           TEXT,                     -- for calls
        observed_outcome    TEXT,                     -- for calls
        started_at          TEXT,                     -- ISO timestamp
        duration_seconds    INTEGER,
        title               TEXT,                     -- meeting title
        review_state        TEXT NOT NULL DEFAULT 'pending',  -- pending | reviewed | stale
        analysis_fresh      INTEGER NOT NULL DEFAULT 0,       -- 1 = current, 0 = stale/not done
        imported_at         TEXT NOT NULL,
        updated_at          TEXT NOT NULL,
        UNIQUE(source_type, source_id)
    );

    CREATE TABLE IF NOT EXISTS route_suggestions (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        source_type     TEXT NOT NULL,
        source_id       TEXT NOT NULL,
        route           TEXT NOT NULL,
        reason          TEXT,
        created_at      TEXT NOT NULL,
        FOREIGN KEY (source_type, source_id) 
            REFERENCES source_records(source_type, source_id)
    );

    CREATE TABLE IF NOT EXISTS route_overrides (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        source_type     TEXT NOT NULL,
        source_id       TEXT NOT NULL,
        route           TEXT NOT NULL,
        reason          TEXT,
        created_at      TEXT NOT NULL,
        is_active       INTEGER NOT NULL DEFAULT 1,
        FOREIGN KEY (source_type, source_id) 
            REFERENCES source_records(source_type, source_id)
    );

    CREATE TABLE IF NOT EXISTS import_log (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_id    TEXT NOT NULL,
        revision    INTEGER NOT NULL,
        file_name   TEXT,
        records_in_file     INTEGER,
        records_inserted    INTEGER,
        records_updated     INTEGER,
        records_skipped     INTEGER,
        imported_at TEXT NOT NULL
    );
    """)
    conn.commit()


# ---------------------------------------------------------------------------
# Data import logic
# ---------------------------------------------------------------------------

def _extract_call_fields(payload: dict) -> dict:
    """Pull searchable fields out of a call payload."""
    return {
        "rep_name": payload.get("rep_name"),
        "rep_email": payload.get("rep_email"),
        "organizer_email": None,
        "direction": payload.get("direction"),
        "observed_outcome": payload.get("observed_outcome"),
        "started_at": payload.get("started_at"),
        "duration_seconds": payload.get("duration_seconds"),
        "title": None,
    }


def _extract_meeting_fields(payload: dict) -> dict:
    """Pull searchable fields out of a meeting payload."""
    return {
        "rep_name": None,
        "rep_email": None,
        "organizer_email": payload.get("organizer_email"),
        "direction": None,
        "observed_outcome": None,
        "started_at": payload.get("starts_at"),
        "duration_seconds": payload.get("duration_seconds"),
        "title": payload.get("title"),
    }


def _has_usable_transcript(record: dict) -> bool:
    """Return True when the record carries actual transcript content.

    For calls: the payload.transcript field must be a non-empty string.
    For meetings: transcript_payload.turns must be a non-empty list AND
                  unavailable_reason must be null.
    """
    source_type = record.get("source_type")
    if source_type == "call":
        transcript_text = record.get("payload", {}).get("transcript")
        return bool(transcript_text and isinstance(transcript_text, str) and transcript_text.strip())
    elif source_type == "meeting":
        tp = record.get("transcript_payload")
        if tp is None:
            return False
        turns = tp.get("turns", [])
        unavailable = tp.get("unavailable_reason")
        return len(turns) > 0 and unavailable is None
    return False


def import_batch(conn: sqlite3.Connection, batch_data: dict, file_name: str = "") -> dict:
    """Import a batch of records into the database.

    Rules:
    - Unique key is (source_type, source_id).
    - Only a *newer* revision replaces an existing record.
    - Same revision is skipped (deduplication).
    - When a record is updated, review_state → 'stale' and analysis_fresh → 0
      so old analysis is not presented as current.
    - Manual route overrides are PRESERVED across updates (they survive revisions).

    Returns a summary dict with counts.
    """
    batch_id = batch_data.get("batch_id", "unknown")
    batch_revision = batch_data.get("revision", 0)
    records = batch_data.get("records", [])
    now = datetime.now(timezone.utc).isoformat()

    inserted = 0
    updated = 0
    skipped = 0
    errors = []

    for rec in records:
        try:
            source_type = rec.get("source_type")
            source_id = rec.get("source_id")
            record_ref = rec.get("record_ref")
            payload = rec.get("payload", {})
            transcript_payload = rec.get("transcript_payload")

            if not source_type or not source_id:
                errors.append(f"Record missing source_type or source_id: {rec.get('record_ref', '?')}")
                skipped += 1
                continue

            # Extract searchable fields
            if source_type == "call":
                fields = _extract_call_fields(payload)
            else:
                fields = _extract_meeting_fields(payload)

            usable = 1 if _has_usable_transcript(rec) else 0

            # Check if record already exists
            existing = conn.execute(
                "SELECT revision, id FROM source_records WHERE source_type = ? AND source_id = ?",
                (source_type, source_id)
            ).fetchone()

            if existing is None:
                # INSERT new record
                conn.execute("""
                    INSERT INTO source_records 
                    (source_type, source_id, record_ref, revision, batch_id,
                     payload_json, transcript_json, has_usable_transcript,
                     rep_name, rep_email, organizer_email, direction,
                     observed_outcome, started_at, duration_seconds, title,
                     review_state, analysis_fresh, imported_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', 0, ?, ?)
                """, (
                    source_type, source_id, record_ref, batch_revision, batch_id,
                    json.dumps(payload), json.dumps(transcript_payload) if transcript_payload else None,
                    usable,
                    fields["rep_name"], fields["rep_email"], fields["organizer_email"],
                    fields["direction"], fields["observed_outcome"],
                    fields["started_at"], fields["duration_seconds"], fields["title"],
                    now, now
                ))
                inserted += 1
            elif batch_revision > existing["revision"]:
                # UPDATE — newer revision replaces payload & transcript
                # Mark analysis as stale so old analysis is flagged
                conn.execute("""
                    UPDATE source_records SET
                        record_ref = ?,
                        revision = ?,
                        batch_id = ?,
                        payload_json = ?,
                        transcript_json = ?,
                        has_usable_transcript = ?,
                        rep_name = ?,
                        rep_email = ?,
                        organizer_email = ?,
                        direction = ?,
                        observed_outcome = ?,
                        started_at = ?,
                        duration_seconds = ?,
                        title = ?,
                        review_state = 'stale',
                        analysis_fresh = 0,
                        updated_at = ?
                    WHERE source_type = ? AND source_id = ?
                """, (
                    record_ref, batch_revision, batch_id,
                    json.dumps(payload), json.dumps(transcript_payload) if transcript_payload else None,
                    usable,
                    fields["rep_name"], fields["rep_email"], fields["organizer_email"],
                    fields["direction"], fields["observed_outcome"],
                    fields["started_at"], fields["duration_seconds"], fields["title"],
                    now,
                    source_type, source_id
                ))
                updated += 1
            else:
                # Same or older revision — skip (deduplication)
                skipped += 1

        except Exception as e:
            errors.append(f"Error importing {rec.get('record_ref', '?')}: {str(e)}")
            skipped += 1

    # Log the import
    conn.execute("""
        INSERT INTO import_log (batch_id, revision, file_name, records_in_file,
                                records_inserted, records_updated, records_skipped, imported_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (batch_id, batch_revision, file_name, len(records), inserted, updated, skipped, now))

    conn.commit()

    return {
        "batch_id": batch_id,
        "revision": batch_revision,
        "total_in_file": len(records),
        "inserted": inserted,
        "updated": updated,
        "skipped": skipped,
        "errors": errors,
    }


def load_json_file(file_path: str) -> dict:
    """Safely load and validate a JSON batch file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Basic validation
    if not isinstance(data, dict):
        raise ValueError("JSON root must be an object with batch_id, revision, records")
    if "records" not in data:
        raise ValueError("JSON must contain a 'records' array")
    if not isinstance(data["records"], list):
        raise ValueError("'records' must be an array")

    return data


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

def get_all_records(conn: sqlite3.Connection) -> list[dict]:
    """Return all source records as a list of dicts."""
    rows = conn.execute("""
        SELECT * FROM source_records ORDER BY started_at DESC
    """).fetchall()
    return [dict(r) for r in rows]


def get_record(conn: sqlite3.Connection, source_type: str, source_id: str) -> dict | None:
    """Return a single source record."""
    row = conn.execute(
        "SELECT * FROM source_records WHERE source_type = ? AND source_id = ?",
        (source_type, source_id)
    ).fetchone()
    return dict(row) if row else None


def get_record_count(conn: sqlite3.Connection) -> int:
    """Return total unique record count."""
    row = conn.execute("SELECT COUNT(*) as cnt FROM source_records").fetchone()
    return row["cnt"]


def get_routes_for_record(conn: sqlite3.Connection, source_type: str, source_id: str) -> dict:
    """Return suggestions and active override for a record."""
    suggestions = conn.execute(
        "SELECT * FROM route_suggestions WHERE source_type = ? AND source_id = ? ORDER BY created_at",
        (source_type, source_id)
    ).fetchall()

    override = conn.execute(
        "SELECT * FROM route_overrides WHERE source_type = ? AND source_id = ? AND is_active = 1 ORDER BY created_at DESC LIMIT 1",
        (source_type, source_id)
    ).fetchone()

    return {
        "suggestions": [dict(s) for s in suggestions],
        "override": dict(override) if override else None,
    }


def set_route_override(conn: sqlite3.Connection, source_type: str, source_id: str,
                        route: str, reason: str = "") -> None:
    """Set a manual route override. Deactivates previous overrides."""
    now = datetime.now(timezone.utc).isoformat()

    # Deactivate old overrides
    conn.execute(
        "UPDATE route_overrides SET is_active = 0 WHERE source_type = ? AND source_id = ? AND is_active = 1",
        (source_type, source_id)
    )

    # Insert new override
    conn.execute("""
        INSERT INTO route_overrides (source_type, source_id, route, reason, created_at, is_active)
        VALUES (?, ?, ?, ?, ?, 1)
    """, (source_type, source_id, route, reason, now))

    conn.commit()

    # Sync to Supabase cloud if connected
    try:
        sb = get_supabase_client()
        if sb:
            sb.table("manual_overrides").upsert({
                "source_type": source_type,
                "source_id": source_id,
                "route_key": route,
                "reason": reason,
                "updated_at": now
            }, on_conflict="source_type,source_id").execute()
    except Exception:
        pass


def reset_route_override(conn: sqlite3.Connection, source_type: str, source_id: str) -> None:
    """Remove the active manual override, reverting to automated suggestions."""
    conn.execute(
        "UPDATE route_overrides SET is_active = 0 WHERE source_type = ? AND source_id = ? AND is_active = 1",
        (source_type, source_id)
    )
    conn.commit()

    # Sync to Supabase cloud if connected
    try:
        sb = get_supabase_client()
        if sb:
            sb.table("manual_overrides").delete().match({
                "source_type": source_type,
                "source_id": source_id
            }).execute()
    except Exception:
        pass


def set_review_state(conn: sqlite3.Connection, source_type: str, source_id: str, state: str) -> None:
    """Update the review state (pending / reviewed / stale)."""
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "UPDATE source_records SET review_state = ?, updated_at = ? WHERE source_type = ? AND source_id = ?",
        (state, now, source_type, source_id)
    )
    conn.commit()

    # Sync to Supabase cloud if connected
    try:
        sb = get_supabase_client()
        if sb:
            sb.table("source_records").update({
                "review_state": state,
                "updated_at": now
            }).match({
                "source_type": source_type,
                "source_id": source_id
            }).execute()
    except Exception:
        pass


def get_import_log(conn: sqlite3.Connection) -> list[dict]:
    """Return the import history."""
    rows = conn.execute("SELECT * FROM import_log ORDER BY imported_at DESC").fetchall()
    return [dict(r) for r in rows]
