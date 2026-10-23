"""
Automated tests for the Revenue Intelligence Inbox.

Tests cover:
1. Deduplication — importing the same batch twice does not increase record count
2. Revision handling — newer revision replaces payload/transcript
3. M07 update — the update batch adds the late transcript
4. Manual override persistence — overrides survive imports and revisions

Run with:
    pytest tests.py -v
"""

import os
import json
import tempfile
import pytest

# Adjust import path
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import get_connection, init_db, load_json_file, import_batch, get_record, get_record_count
from db import set_route_override, get_routes_for_record, reset_route_override
from routing import apply_route_suggestions, suggest_routes, refresh_routes_for_record


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
INITIAL_FILE = os.path.join(DATA_DIR, "01_initial.json")
UPDATE_FILE = os.path.join(DATA_DIR, "02_update.json")


@pytest.fixture
def db_conn():
    """Create a fresh in-memory database for each test."""
    conn = get_connection(":memory:")
    init_db(conn)
    yield conn
    conn.close()


@pytest.fixture
def initial_data():
    """Load the initial batch JSON."""
    return load_json_file(INITIAL_FILE)


@pytest.fixture
def update_data():
    """Load the update batch JSON."""
    return load_json_file(UPDATE_FILE)


# ---------------------------------------------------------------------------
# Test 1: Deduplication
# ---------------------------------------------------------------------------

class TestDeduplication:
    """Importing the initial batch repeatedly must not increase the unique-record count."""

    def test_import_initial_once(self, db_conn, initial_data):
        """First import should insert all 44 records."""
        result = import_batch(db_conn, initial_data, "01_initial.json")
        assert result["inserted"] == 44
        assert result["updated"] == 0
        assert result["skipped"] == 0
        assert get_record_count(db_conn) == 44

    def test_import_initial_twice(self, db_conn, initial_data):
        """Second import of the same batch should skip all records."""
        import_batch(db_conn, initial_data, "01_initial.json")
        result2 = import_batch(db_conn, initial_data, "01_initial.json")

        assert result2["inserted"] == 0
        assert result2["updated"] == 0
        assert result2["skipped"] == 44
        assert get_record_count(db_conn) == 44  # No increase!

    def test_import_initial_three_times(self, db_conn, initial_data):
        """Third import also should not change count."""
        import_batch(db_conn, initial_data, "01_initial.json")
        import_batch(db_conn, initial_data, "01_initial.json")
        import_batch(db_conn, initial_data, "01_initial.json")
        assert get_record_count(db_conn) == 44


# ---------------------------------------------------------------------------
# Test 2: Revision Handling
# ---------------------------------------------------------------------------

class TestRevisionHandling:
    """Only newer revisions should replace existing records."""

    def test_newer_revision_updates(self, db_conn, initial_data, update_data):
        """Update batch (revision 2) should update records from initial batch (revision 1)."""
        import_batch(db_conn, initial_data, "01_initial.json")
        result = import_batch(db_conn, update_data, "02_update.json")

        assert result["updated"] == 1  # M07
        assert result["inserted"] == 0
        assert result["skipped"] == 0

    def test_older_revision_skipped(self, db_conn, initial_data, update_data):
        """Importing initial (rev 1) after update (rev 2) should skip the overlapping record."""
        # Import update first (contains M07 at rev 2)
        import_batch(db_conn, update_data, "02_update.json")
        # Now import initial (M07 at rev 1 should be skipped)
        result = import_batch(db_conn, initial_data, "01_initial.json")

        # 43 records from initial should be inserted (they don't exist yet)
        # M07 should be skipped because it's already at revision 2
        assert result["inserted"] == 43
        assert result["skipped"] == 1  # M07
        assert get_record_count(db_conn) == 44

    def test_update_marks_stale(self, db_conn, initial_data, update_data):
        """When a record is updated, its review_state should become 'stale'."""
        import_batch(db_conn, initial_data, "01_initial.json")
        import_batch(db_conn, update_data, "02_update.json")

        m07 = get_record(db_conn, "meeting", "4f304fff-fd40-5cfc-a366-0a134c445c2a")
        assert m07 is not None
        assert m07["review_state"] == "stale"
        assert m07["analysis_fresh"] == 0


# ---------------------------------------------------------------------------
# Test 3: M07 Update Handling
# ---------------------------------------------------------------------------

class TestM07Update:
    """The update batch must apply the late transcript for M07 without creating a duplicate."""

    def test_m07_initially_has_no_transcript(self, db_conn, initial_data):
        """In the initial batch, M07 has no usable transcript."""
        import_batch(db_conn, initial_data, "01_initial.json")
        m07 = get_record(db_conn, "meeting", "4f304fff-fd40-5cfc-a366-0a134c445c2a")
        assert m07 is not None
        assert m07["has_usable_transcript"] == 0

    def test_m07_gets_transcript_after_update(self, db_conn, initial_data, update_data):
        """After the update batch, M07 should have a usable transcript."""
        import_batch(db_conn, initial_data, "01_initial.json")
        import_batch(db_conn, update_data, "02_update.json")

        m07 = get_record(db_conn, "meeting", "4f304fff-fd40-5cfc-a366-0a134c445c2a")
        assert m07 is not None
        assert m07["has_usable_transcript"] == 1
        assert m07["revision"] == 2

    def test_m07_no_duplicate(self, db_conn, initial_data, update_data):
        """M07 should remain one record, not two."""
        import_batch(db_conn, initial_data, "01_initial.json")
        import_batch(db_conn, update_data, "02_update.json")
        assert get_record_count(db_conn) == 44  # Still 44, not 45

    def test_m07_transcript_has_turns(self, db_conn, initial_data, update_data):
        """The updated M07 transcript should have actual turn data."""
        import_batch(db_conn, initial_data, "01_initial.json")
        import_batch(db_conn, update_data, "02_update.json")

        m07 = get_record(db_conn, "meeting", "4f304fff-fd40-5cfc-a366-0a134c445c2a")
        tp = json.loads(m07["transcript_json"])
        turns = tp.get("turns", [])
        assert len(turns) > 0
        assert turns[0]["speaker"] == "Team member A"


# ---------------------------------------------------------------------------
# Test 4: Manual Override Persistence
# ---------------------------------------------------------------------------

class TestManualOverridePersistence:
    """A manual route override must survive browser refreshes, app restarts, and newer revisions."""

    def test_override_is_stored(self, db_conn, initial_data):
        """Setting an override should be retrievable."""
        import_batch(db_conn, initial_data, "01_initial.json")
        apply_route_suggestions(db_conn)

        set_route_override(db_conn, "call", "2ec4404c-beee-5377-a63c-aab701da08ed",
                          "partnership", "Manager decision")

        routing = get_routes_for_record(db_conn, "call", "2ec4404c-beee-5377-a63c-aab701da08ed")
        assert routing["override"] is not None
        assert routing["override"]["route"] == "partnership"
        assert routing["override"]["reason"] == "Manager decision"

    def test_override_survives_reimport(self, db_conn, initial_data):
        """Re-importing the same batch should not remove the manual override."""
        import_batch(db_conn, initial_data, "01_initial.json")
        apply_route_suggestions(db_conn)

        set_route_override(db_conn, "call", "2ec4404c-beee-5377-a63c-aab701da08ed",
                          "partnership", "Manager decision")

        # Re-import
        import_batch(db_conn, initial_data, "01_initial.json")

        routing = get_routes_for_record(db_conn, "call", "2ec4404c-beee-5377-a63c-aab701da08ed")
        assert routing["override"] is not None
        assert routing["override"]["route"] == "partnership"

    def test_override_survives_revision_update(self, db_conn, initial_data, update_data):
        """A newer revision should not remove the manual override."""
        import_batch(db_conn, initial_data, "01_initial.json")
        apply_route_suggestions(db_conn)

        # Set override on M07
        set_route_override(db_conn, "meeting", "4f304fff-fd40-5cfc-a366-0a134c445c2a",
                          "existing_customer", "This is actually a support call")

        # Import update (which updates M07)
        import_batch(db_conn, update_data, "02_update.json")

        routing = get_routes_for_record(db_conn, "meeting", "4f304fff-fd40-5cfc-a366-0a134c445c2a")
        assert routing["override"] is not None
        assert routing["override"]["route"] == "existing_customer"
        assert routing["override"]["reason"] == "This is actually a support call"

    def test_override_reset(self, db_conn, initial_data):
        """Explicitly resetting an override should remove it."""
        import_batch(db_conn, initial_data, "01_initial.json")
        apply_route_suggestions(db_conn)

        set_route_override(db_conn, "call", "2ec4404c-beee-5377-a63c-aab701da08ed",
                          "partnership", "Manager decision")
        reset_route_override(db_conn, "call", "2ec4404c-beee-5377-a63c-aab701da08ed")

        routing = get_routes_for_record(db_conn, "call", "2ec4404c-beee-5377-a63c-aab701da08ed")
        assert routing["override"] is None


# ---------------------------------------------------------------------------
# Test 5: Route suggestion generation
# ---------------------------------------------------------------------------

class TestRouteSuggestions:
    """Route suggestions should be generated correctly."""

    def test_voicemail_call_gets_no_conversation_route(self, db_conn, initial_data):
        """A brief voicemail call should be routed as 'no_conversation'."""
        import_batch(db_conn, initial_data, "01_initial.json")
        apply_route_suggestions(db_conn)

        routing = get_routes_for_record(db_conn, "call", "4868e5cd-5ab8-581c-a0e4-acc37385f0cf")
        routes = [s["route"] for s in routing["suggestions"]]
        assert "no_conversation" in routes

    def test_conversation_call_gets_meaningful_route(self, db_conn, initial_data):
        """A conversation call (C01) should get a non-trivial route."""
        import_batch(db_conn, initial_data, "01_initial.json")
        apply_route_suggestions(db_conn)

        routing = get_routes_for_record(db_conn, "call", "2ec4404c-beee-5377-a63c-aab701da08ed")
        routes = [s["route"] for s in routing["suggestions"]]
        assert len(routes) > 0
        assert "no_conversation" not in routes


# ---------------------------------------------------------------------------
# Test 6: Malformed input handling
# ---------------------------------------------------------------------------

class TestMalformedInput:
    """Import should handle malformed data gracefully."""

    def test_empty_records_array(self, db_conn):
        """An empty records array should not crash."""
        data = {"batch_id": "empty", "revision": 1, "records": []}
        result = import_batch(db_conn, data, "empty.json")
        assert result["total_in_file"] == 0
        assert result["inserted"] == 0

    def test_missing_source_fields(self, db_conn):
        """Records missing source_type or source_id should be skipped with error."""
        data = {
            "batch_id": "bad",
            "revision": 1,
            "records": [
                {"record_ref": "X01", "payload": {}, "transcript_payload": None}
            ]
        }
        result = import_batch(db_conn, data, "bad.json")
        assert result["skipped"] == 1
        assert len(result["errors"]) > 0

    def test_file_not_found(self):
        """Loading a non-existent file should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_json_file("/nonexistent/path.json")
