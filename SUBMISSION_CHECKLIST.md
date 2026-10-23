# Submission Checklist & Verification

This checklist verifies all 16 requirements and constraints specified for the Revenue Intelligence Inbox Revenue Intelligence Inbox assignment.

---

## 1. Functional Requirements

- [x] **Requirement 1: Dashboard**
  - Source-record counts (total, calls, meetings).
  - Usable transcript coverage with explicit denominator ($N / \text{Total}$).
  - Activity breakdown by person and by source type.
  - Routing category breakdown.
  - Review states summary (`new`, `reviewed`, `stale`, `escalated`).
  - Working source-type filter and rep filter.

- [x] **Requirement 2: Inbox**
  - Displays all source records in a clear table/list.
  - Identifiers (`<type>:<id>`), revisions, transcript status, assigned routes, review states, and freshness.
  - Detailed record view on selection.

- [x] **Requirement 3: Conversation Details & Route Correction**
  - Displays actual call transcripts or meeting turns with speaker names.
  - Provides an interactive manager form to correct/override the assigned route.
  - Allows entering an override reason and applies immediately.

- [x] **Requirement 4: Data Import**
  - Supports both `data/01_initial.json` and `data/02_update.json`.
  - Uses `(source_type, source_id)` as the unique key.
  - Strictly applies newer revisions (`incoming.revision > current.revision`).
  - Newer revision cleanly replaces source and transcript payloads.

- [x] **Requirement 5: Duplicate Handling**
  - Repeatedly importing `01_initial.json` inserts 0 new records and skips 44 records.
  - Unique record count remains constant at 44.

- [x] **Requirement 6: Update Handling (M07)**
  - Applying `02_update.json` updates `meeting:M07` with its late transcript.
  - Does NOT create a duplicate record.
  - Increments M07 revision to 2.

- [x] **Requirement 7: Persistence (SQLite)**
  - Uses `inbox.db` with WAL mode and parameterized queries.
  - Persists records, route suggestions, manual overrides, review states, freshness.
  - Manual route overrides survive browser refreshes, application restarts, and reimports.

- [x] **Requirement 8: Stale Analysis Handling**
  - When a record is updated with a newer revision, `analysis_fresh` is set to `0` and state is marked `stale`.
  - Old analyses are flagged as stale until re-evaluated.

- [x] **Requirement 9: Findings & Manager Daily Brief**
  - Generates 3 evidence-backed findings strictly grounded in transcript quotes.
  - Quotes actual speaker lines from M01, M04, and campaign dialer results.
  - Never fabricates facts or hallucinated details.
  - Fixed brief for 21 August 2026.

- [x] **Requirement 10: Multi-Format Exports**
  - Generates download-ready ZIP archives.
  - Includes `manifest.json` and `manifest.csv`.
  - Includes per-record JSON files under route folders: `output/<route>/<record_ref>.json`.
  - Includes `findings.json` and `manager_brief.md`.

- [x] **Requirement 11: Replay Panel**
  - Interactive UI controls to step through:
    1. Import initial batch.
    2. Repeat initial batch (verify dedup).
    3. Apply manual override.
    4. Import update batch.
    5. Inspect M07 status and turns.
    6. Reset database.

- [x] **Requirement 12: Documentation**
  - Complete `README.md` with setup, run commands, metric definitions, replay steps, output locations, AI approach, limitations, and hours spent table.
  - Supplementary documentation: `DATA_CONTRACT.md`, `DATA_DICTIONARY.md`, `CONVERSATIONS.md`.

- [x] **Requirement 13: Automated Tests**
  - 19 automated tests in `tests.py` covering:
    - Deduplication (1x, 2x, 3x imports).
    - Revision handling (newer updates, older skipped, staleness marked).
    - M07 update (missing transcript $\rightarrow$ turns populated, no duplicates).
    - Manual override persistence across imports and revisions.
    - Route suggestions and malformed inputs.
  - All 19 tests pass (`pytest tests.py -v`).

---

## 2. Implementation Rules & Quality

- [x] Data files in `data/` preserved untouched.
- [x] Parameterized SQL statements used for all database queries (no SQL injection).
- [x] Clean modular architecture (`db.py`, `routing.py`, `findings.py`, `exports.py`, `app.py`).
- [x] Runs locally with standard commands (`streamlit run app.py`).
