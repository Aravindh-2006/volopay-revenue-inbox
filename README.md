# Revenue Intelligence Inbox Revenue Intelligence Inbox

A Streamlit application that ingests sales call and meeting records, classifies them into routing categories, and provides a manager with an evidence-based daily brief.

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the application

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

### 3. Run tests

```bash
pytest tests.py -v
```

---

## Project Structure

```
volopay-revenue-inbox/
├── data/
│   ├── 01_initial.json     # Initial batch (44 records, revision 1)
│   └── 02_update.json      # Update batch (M07 transcript, revision 2)
├── app.py                  # Main Streamlit application
├── db.py                   # SQLite database module (schema, import, queries)
├── routing.py              # Routing taxonomy and automated classification
├── findings.py             # Evidence-backed findings and manager brief
├── exports.py              # ZIP export and manifest generation
├── tests.py                # Automated pytest tests
├── requirements.txt        # Python dependencies
├── README.md               # This file
└── inbox.db                # SQLite database (created at runtime)
```

---

## How It Works

### Data Model

The application uses `(source_type, source_id)` as the unique key for each record. Records come in two types:
- **Calls** — outbound/inbound phone calls with optional inline transcript text
- **Meetings** — Google Meet sessions with optional structured transcript turns

### Pages

| Page | Purpose |
|------|---------|
| **Dashboard** | KPI metrics: record counts, transcript coverage, routing distribution, activity by person. Includes source-type and person filters. |
| **Inbox** | Table of all source records showing ref, type, revision, transcript status, routes, review state, and analysis freshness. Click a record to see full details and correct routes. |
| **Replay Panel** | Step-by-step import controls. Import initial batch, repeat import (test deduplication), import update batch, inspect M07, reset database. |
| **Findings & Brief** | Three evidence-backed findings with exact quotes and source references, plus a manager brief for 21 August 2026. |
| **Exports** | Preview and download the manifest (JSON/CSV) and a full ZIP archive containing per-record output files, findings, and the manager brief. |

### Import & Deduplication

- First import inserts all 44 records.
- Repeat imports of the same batch skip all records (no duplicates).
- The update batch (revision 2) replaces M07's payload and transcript without creating a duplicate.

### Revision Handling

- Only a **newer** revision replaces an existing record.
- When updated, `review_state` → `stale` and `analysis_fresh` → `0`.
- Old analysis is never presented as current.

### Routing

Eight-category taxonomy:

| Route | Description |
|-------|-------------|
| New Prospect Outreach | Cold outreach to potential customers |
| Follow-Up / Nurture | Continued conversation with interested leads |
| Partnership / Channel | Referral partnerships and channel arrangements |
| Existing Customer Management | Support, onboarding, migration for current customers |
| Vendor / Supplier Evaluation | Revenue Intelligence Inbox evaluating external vendors |
| Internal / Training | Internal meetings and training sessions |
| No Conversation | Voicemail, unresponsive, very short calls |
| Unclassified | Insufficient information; needs manual review |

- **Automated suggestions** are generated from metadata and transcript keywords.
- **Manual overrides** are set by a manager and persist across imports, revisions, and app restarts.
- Each route includes a reason explaining the classification.

### Persistence (SQLite)

All data is stored in `inbox.db`:
- Source records with extracted metadata
- Automated route suggestions
- Manual route overrides (survive everything except explicit reset)
- Review states and analysis freshness
- Import history log

### Findings

Three evidence-backed findings are generated from actual transcript passages:
1. Partnership negotiation with Harborpath Advisory (M01)
2. Card migration churn risk with Cedarwave Distribution (M04)
3. Low outbound campaign connect rate (B01–B20)

Each finding includes exact quotes, source references, and clearly labelled uncertainty.

### Manager Brief

A fixed brief for **21 August 2026** (Asia/Kolkata timezone) summarising activity, key findings, and items requiring attention. Based only on supplied data.

### Exports

The ZIP archive contains:
- `manifest.json` / `manifest.csv` — all records with routes, states, override flags
- `output/<route>/<record_ref>.json` — per-record structured output
- `findings.json` — the three findings
- `manager_brief.md` — the formatted brief

---

## Replay Test Steps

1. Open the **Replay Panel** page.
2. Click **Import 01_initial.json** → should show 44 inserted, 0 skipped.
3. Click **Import 01_initial.json** again → should show 0 inserted, 44 skipped. Record count stays 44.
4. Go to **Inbox** → select record C01 → set route override to "Partnership / Channel" → click Apply Override.
5. Return to **Replay Panel** → click **Import 02_update.json** → should show 1 updated, 0 skipped.
6. Check M07 Inspection section → should show ✅ transcript with actual turns.
7. Verify record count is still 44.
8. Go to **Inbox** → check C01 → override should still be "Partnership / Channel".
9. Go to **Exports** → download ZIP and verify manifest contents.

---

## Metric Definitions

| Metric | Definition |
|--------|------------|
| Total Records | Count of unique `(source_type, source_id)` pairs in the database |
| Calls | Records where `source_type = 'call'` |
| Meetings | Records where `source_type = 'meeting'` |
| With Transcript | Records with usable transcript text (calls with non-null transcript field, meetings with non-empty turns and no unavailable_reason) |
| Transcript Coverage | `With Transcript / Total Records` |
| Fresh Analysis | Records where `analysis_fresh = 1` (not stale after updates) |
| Manual Override | Records with an active `route_overrides` entry |

---

## Output Locations

| File | Location |
|------|----------|
| SQLite database | `inbox.db` (project root, created at runtime) |
| Exported ZIP | Downloaded via the Exports page |
| Data files | `data/01_initial.json`, `data/02_update.json` (read-only, never modified) |

---

## AI Approach

- **No LLM calls** — all classification is rule-based using metadata and keyword matching.
- **No fabricated content** — findings use only actual transcript passages with exact quotes.
- **Deterministic routing** — same input always produces the same route suggestions.
- Keyword-based routing examines `observed_outcome`, `is_campaign_call`, `is_conversation`, and transcript text for terms like "partner", "migration", "follow up".

---

## Limitations

1. **No NLP/ML** — routing uses keyword matching, not semantic understanding. Edge cases may be misclassified.
2. **Single-user** — no authentication or multi-user support.
3. **No real-time updates** — data must be imported manually via the Replay Panel.
4. **SQLite concurrency** — WAL mode helps, but heavy concurrent writes are not tested.
5. **No deployment** — designed for local use. Add deployment configuration if needed.

---

## Hours Spent

| Phase | Hours |
|-------|-------|
| Data inspection and understanding | ___ |
| Architecture and design | ___ |
| Implementation | ___ |
| Testing and debugging | ___ |
| Documentation | ___ |
| **Total** | ___ |

*Fill in your actual hours above before submission.*
