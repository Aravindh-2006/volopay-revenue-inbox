# Data Contract

## 1. Overview

This document specifies the data contract for the **Revenue Intelligence Inbox Revenue Intelligence Inbox**. It defines the record identification schema, ingestion semantics, deduplication rules, revision handling, and data integrity guarantees for incoming batches of sales calls and meetings.

---

## 2. Source Record Identification

Each incoming record is uniquely identified by the compound primary key:
$$\text{Record Key} = (\texttt{source\_type}, \texttt{source\_id})$$

- `source_type`: String enum, exactly one of `call` or `meeting`.
- `source_id`: String identifier unique within its `source_type` (e.g., `B01`–`B20`, `C01`–`C04` for calls; `M01`–`M20` for meetings).
- In the application and UI, records are formatted as `<source_type>:<source_id>` (e.g. `call:C01`, `meeting:M07`).

---

## 3. Batch Structure

Batches are delivered as JSON documents with the following top-level structure:

```json
{
  "batch_id": "string",
  "generated_at": "ISO-8601 UTC timestamp",
  "records": [
    {
      "source_type": "call | meeting",
      "source_id": "string",
      "revision": 1,
      "source_payload": { ... },
      "transcript_payload": { ... }
    }
  ]
}
```

### Invariants:
1. `records` is an array of record objects.
2. Each record MUST contain `source_type`, `source_id`, `revision`, `source_payload`, and `transcript_payload`.
3. `revision` is a strictly positive integer ($\ge 1$).

---

## 4. Revision & Ingestion Semantics

1. **New Records**: If `(source_type, source_id)` does not exist in the database, the record is inserted with its `revision`, `source_payload`, and `transcript_payload`.
2. **Duplicate Detection (Idempotency)**: If `(source_type, source_id)` exists with `incoming.revision <= existing.revision`, the record is **skipped** as duplicate/stale.
3. **Newer Revisions**: If `incoming.revision > existing.revision`:
   - `source_payload` and `transcript_payload` are updated to incoming values.
   - `revision` is updated to `incoming.revision`.
   - `analysis_fresh` is marked `0` (stale).
   - `review_state` is set to `stale` (unless preserved as `reviewed`).
   - Any manual route override previously applied to this record is **retained** and not overwritten.

---

## 5. Payloads Specification

### 5.1 Call Record
- `source_payload`:
  - `call_id` (string): Identical to `source_id`.
  - `caller_id` (string): User ID of the rep (e.g., `U101`).
  - `direction` (string): `outbound` or `inbound`.
  - `duration_seconds` (integer): Call duration in seconds.
  - `observed_outcome` (string): Outcome tag, e.g. `connected_conversation`, `voicemail`, `busy`, `no_answer`.
  - `is_campaign_call` (boolean): Flag for automated/campaign dialer.
  - `is_conversation` (boolean): Whether a real conversation took place.
- `transcript_payload`:
  - `call_id` (string): Identical to `source_id`.
  - `transcript` (string | null): Raw transcript string if recorded, or `null`.

### 5.2 Meeting Record
- `source_payload`:
  - `meeting_id` (string): Identical to `source_id`.
  - `title` (string): Meeting title.
  - `scheduled_start` (ISO-8601 string): Scheduled start time.
  - `scheduled_end` (ISO-8601 string): Scheduled end time.
  - `host_user_id` (string): User ID of the host rep.
  - `participants` (array of strings): Participant names/emails.
- `transcript_payload`:
  - `meeting_id` (string): Identical to `source_id`.
  - `unavailable_reason` (string | null): Reason if transcript is missing (e.g., `recording_disabled`, `processing_pending`), or `null` if available.
  - `turns` (array of objects | null): Dialogue turns with `speaker` (string), `offset_seconds` (integer), and `text` (string).

---

## 6. Transcript Usability Rule

A record is counted as having a **usable transcript** if and only if:
- For `call`: `transcript_payload.transcript` is non-null and non-empty.
- For `meeting`: `transcript_payload.turns` is a non-empty array AND `unavailable_reason` is null.

All metrics reporting transcript coverage must explicitly use:
$$\text{Coverage Rate} = \frac{\text{Records with Usable Transcript}}{\text{Total Records}}$$
