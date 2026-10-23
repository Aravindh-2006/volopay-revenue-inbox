# Data Dictionary

## 1. Core Source Records Table (`source_records`)

| Column Name | SQLite Type | Nullable | Description |
|-------------|-------------|----------|-------------|
| `source_type` | `TEXT` | No | Record source discriminator: `'call'` or `'meeting'` (Part of PK). |
| `source_id` | `TEXT` | No | Unique identifier within source type (Part of PK). |
| `revision` | `INTEGER` | No | Monotonically increasing revision counter ($\ge 1$). |
| `person_id` | `TEXT` | Yes | Extracted rep / user ID (`caller_id` or `host_user_id`). |
| `title` | `TEXT` | Yes | Extracted display title (meeting title or call summary). |
| `timestamp` | `TEXT` | Yes | Scheduled or recorded start timestamp. |
| `duration` | `INTEGER` | Yes | Duration in seconds. |
| `has_transcript`| `INTEGER` | No | Boolean flag (`1` or `0`) indicating usable transcript. |
| `source_payload` | `TEXT` | No | Raw source JSON payload preserved verbatim. |
| `transcript_payload` | `TEXT` | Yes | Raw transcript JSON payload preserved verbatim. |
| `review_state` | `TEXT` | No | State machine status: `'new'`, `'reviewed'`, `'stale'`, or `'escalated'`. |
| `analysis_fresh` | `INTEGER` | No | Boolean flag (`1` = fresh, `0` = stale after newer revision). |
| `created_at` | `TEXT` | No | ISO-8601 timestamp when first ingested. |
| `updated_at` | `TEXT` | No | ISO-8601 timestamp when last modified. |

---

## 2. Route Suggestions Table (`route_suggestions`)

| Column Name | SQLite Type | Nullable | Description |
|-------------|-------------|----------|-------------|
| `id` | `INTEGER PRIMARY KEY` | No | Auto-incrementing identifier. |
| `source_type` | `TEXT` | No | Foreign key component referencing `source_records`. |
| `source_id` | `TEXT` | No | Foreign key component referencing `source_records`. |
| `route_id` | `TEXT` | No | Category from 8-route taxonomy (e.g., `'New Prospect Outreach'`). |
| `confidence` | `REAL` | No | Heuristic confidence score ($0.0$ to $1.0$). |
| `reason` | `TEXT` | No | Human-readable explanation of why this route was suggested. |
| `created_at` | `TEXT` | No | Timestamp when suggestion was computed. |

---

## 3. Manual Route Overrides Table (`route_overrides`)

| Column Name | SQLite Type | Nullable | Description |
|-------------|-------------|----------|-------------|
| `source_type` | `TEXT` | No | Foreign key component (Part of PK). |
| `source_id` | `TEXT` | No | Foreign key component (Part of PK). |
| `route_id` | `TEXT` | No | Manually selected category chosen by manager. |
| `override_reason`| `TEXT` | Yes | Reason entered by manager for making the correction. |
| `applied_by` | `TEXT` | No | User/manager identifier who performed the override. |
| `applied_at` | `TEXT` | No | Timestamp when override was recorded. |

---

## 4. Import History Table (`import_history`)

| Column Name | SQLite Type | Nullable | Description |
|-------------|-------------|----------|-------------|
| `id` | `INTEGER PRIMARY KEY` | No | Auto-incrementing import event ID. |
| `filename` | `TEXT` | No | File name or descriptor of ingested batch. |
| `batch_id` | `TEXT` | Yes | Identifier from batch JSON. |
| `records_inserted` | `INTEGER` | No | Number of novel records inserted. |
| `records_updated` | `INTEGER` | No | Number of existing records updated by newer revision. |
| `records_skipped` | `INTEGER` | No | Number of duplicate or stale records ignored. |
| `imported_at` | `TEXT` | No | Timestamp when import completed. |

---

## 5. Routing Taxonomy Values

1. **`New Prospect Outreach`**: Cold outreach to prospective buyers.
2. **`Follow-Up / Nurture`**: Ongoing pipeline advancement with evaluated prospects.
3. **`Partnership / Channel`**: Discussions with advisors, brokers, and channel partners.
4. **`Existing Customer Management`**: Onboarding, renewal, card migration, and account health.
5. **`Vendor / Supplier Evaluation`**: Revenue Intelligence Inbox evaluating incoming third-party software/services.
6. **`Internal / Training`**: Team standups, training, 1-on-1s.
7. **`No Conversation`**: Voicemail, gatekeeper rejection, short unanswered attempts.
8. **`Unclassified`**: Inconclusive context requiring human attention.
