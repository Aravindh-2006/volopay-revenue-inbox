"""
Routing module — taxonomy and automated route assignment.

Defines a small, understandable routing taxonomy and assigns routes
to source records based on their content.  Keeps automated suggestions
separate from manual overrides.
"""

import json
from datetime import datetime, timezone
import sqlite3

# ---------------------------------------------------------------------------
# Routing Taxonomy
# ---------------------------------------------------------------------------
# Each route has a short code, a human-readable label, and a description.

ROUTE_TAXONOMY = {
    "deal_next_steps": {
        "label": "Deal Next Steps",
        "description": "Commercial proposals, pricing terms, contract reviews, and closing discussions.",
    },
    "customer_followup": {
        "label": "Customer Follow-up",
        "description": "Continued engagement with interested leads, demos, and pipeline advancement.",
    },
    "sales_coaching": {
        "label": "Sales Coaching",
        "description": "Call or meeting requiring managerial coaching, objection handling review, or connect rate feedback.",
    },
    "internal_vendor": {
        "label": "Internal / Vendor Note",
        "description": "Internal team syncs, supplier evaluations, or vendor architecture discussions.",
    },
    "support_engineering": {
        "label": "Technical Support / Engineering",
        "description": "Technical integration, physical card migration, API onboarding, or bug reports.",
    },
    "human_review": {
        "label": "Human Review",
        "description": "Records with customer churn threat, missing context, or high risk requiring managerial intervention.",
    },
    "new_prospect": {
        "label": "New Prospect Outreach",
        "description": "Cold outreach to a potential customer who has not previously engaged.",
    },
    "follow_up": {
        "label": "Follow-Up / Nurture",
        "description": "Continued conversation with a lead who showed some interest or requested information.",
    },
    "partnership": {
        "label": "Partnership / Channel",
        "description": "Discussion about referral partnerships, channel arrangements, or reseller agreements.",
    },
    "existing_customer": {
        "label": "Existing Customer Management",
        "description": "Support, onboarding, migration, or account management for a current customer.",
    },
    "vendor_evaluation": {
        "label": "Vendor / Supplier Evaluation",
        "description": "Revenue Intelligence Inbox evaluating an external vendor or supplier for its own product needs.",
    },
    "internal": {
        "label": "Internal / Training",
        "description": "Internal meetings, training sessions, or process walkthroughs (not customer-facing).",
    },
    "no_conversation": {
        "label": "No Conversation",
        "description": "Call did not result in a conversation (voicemail, unresponsive, very short duration).",
    },
    "unclassified": {
        "label": "Unclassified",
        "description": "Insufficient information to determine a route; needs manual review.",
    },
}


def get_taxonomy() -> dict:
    """Return the full routing taxonomy."""
    return ROUTE_TAXONOMY


def suggest_routes(record: dict) -> list[dict]:
    """Generate automated route suggestions for a source record.

    Returns a list of dicts: [{"route": "...", "reason": "..."}]
    Multiple routes may be returned if justified.
    """
    source_type = record.get("source_type", "")
    payload = json.loads(record.get("payload_json", "{}"))
    transcript_json = record.get("transcript_json")
    has_transcript = record.get("has_usable_transcript", 0)
    
    routes = []

    if source_type == "call":
        routes = _suggest_call_routes(payload, has_transcript, transcript_json)
    elif source_type == "meeting":
        routes = _suggest_meeting_routes(payload, has_transcript, transcript_json)

    if not routes:
        routes = [{"route": "unclassified", "reason": "Insufficient information to classify."}]

    return routes


def _suggest_call_routes(payload: dict, has_transcript: int, transcript_json: str | None) -> list[dict]:
    """Route a call record."""
    outcome = payload.get("observed_outcome", "")
    is_conversation = payload.get("is_conversation", False)
    is_connected = payload.get("is_connected", False)
    is_campaign = payload.get("is_campaign_call", False)
    duration = payload.get("duration_seconds", 0)
    first_dial = payload.get("first_dial_ever", True)
    transcript_text = payload.get("transcript", "") or ""

    # Short calls with no conversation
    if not is_conversation and duration < 30:
        return [{"route": "no_conversation",
                 "reason": f"Brief call ({duration}s), outcome: {outcome}. No conversation took place."}]

    # Voicemail / unresponsive with no real conversation
    if outcome in ("voicemail", "unresponsive") and not is_conversation:
        return [{"route": "no_conversation",
                 "reason": f"Call outcome is '{outcome}' with no conversation recorded."}]

    # If there is transcript text, try keyword-based routing
    if has_transcript and transcript_text:
        text_lower = transcript_text.lower()

        routes = []

        # Check for partnership signals
        if any(w in text_lower for w in ["partner", "referral", "commission", "reseller", "channel"]):
            routes.append({"route": "partnership",
                           "reason": "Transcript mentions partnership/referral/commission terms."})

        # Check for existing customer signals
        if any(w in text_lower for w in ["migration", "existing account", "current cards", "our account", "login issue"]):
            routes.append({"route": "existing_customer",
                           "reason": "Transcript suggests interaction with an existing customer."})

        # Follow-up signals
        if outcome == "follow_up" or any(w in text_lower for w in ["follow up", "send email", "call back", "monday", "next week"]):
            routes.append({"route": "follow_up",
                           "reason": f"Outcome '{outcome}' and/or transcript indicates a follow-up was agreed."})

        # Cold outreach / new prospect
        if is_campaign and first_dial:
            if outcome == "uninterested":
                routes.append({"route": "new_prospect",
                               "reason": "First campaign dial; prospect declined interest."})
            elif outcome == "referred":
                routes.append({"route": "new_prospect",
                               "reason": "First campaign dial; prospect referred to another contact."})
                routes.append({"route": "follow_up",
                               "reason": "Referral was given — follow-up with the referred contact is needed."})
            elif not routes:  # Don't double up
                routes.append({"route": "new_prospect",
                               "reason": f"Campaign call, first dial. Outcome: {outcome}."})

        # OOO
        if outcome == "ooo":
            routes.append({"route": "follow_up",
                           "reason": "Contact was out of office; needs rescheduling."})

        if routes:
            return routes

    # Fallback based on metadata
    if is_campaign and first_dial:
        return [{"route": "new_prospect",
                 "reason": "Campaign call, first dial ever. No transcript to refine routing."}]

    if outcome == "follow_up":
        return [{"route": "follow_up",
                 "reason": f"Outcome is 'follow_up'. Prior connects: {payload.get('prior_connects_ever', 0)}."}]

    return []


def _suggest_meeting_routes(payload: dict, has_transcript: int, transcript_json: str | None) -> list[dict]:
    """Route a meeting record."""
    title = (payload.get("title", "") or "").lower()
    recording_status = payload.get("recording_status", "")
    
    routes = []

    # Parse transcript turns for keyword analysis
    transcript_text = ""
    if has_transcript and transcript_json:
        try:
            tp = json.loads(transcript_json)
            turns = tp.get("turns", [])
            transcript_text = " ".join(t.get("text", "") for t in turns).lower()
        except (json.JSONDecodeError, TypeError):
            pass

    # No recording at all
    if recording_status in ("cancelled", "not_scheduled"):
        return [{"route": "unclassified",
                 "reason": f"Meeting recording was {recording_status}. No content to analyse."}]

    # Nobody spoke
    if not has_transcript and recording_status == "recorded":
        return [{"route": "unclassified",
                 "reason": "Meeting was recorded but has no usable transcript (nobody spoke or transcript unavailable)."}]

    # Use title + transcript for classification
    if transcript_text:
        # Internal / training
        if any(w in title for w in ["internal", "training", "walkthrough", "billing", "setup"]) or \
           any(w in transcript_text for w in ["training session", "back-office", "billing cycle", "invoice generation"]):
            if "customer" not in title.lower() or "internal" in title.lower():
                routes.append({"route": "internal",
                               "reason": "Meeting title and/or transcript indicate an internal training or process session."})

        # Partnership
        if any(w in transcript_text for w in ["partner", "referral", "commission", "memorandum"]):
            routes.append({"route": "partnership",
                           "reason": "Transcript discusses partnership terms, referrals, or commission structures."})

        # Vendor evaluation
        if any(w in transcript_text for w in ["vendor", "supplier", "proposal", "pricing model", "setup charge"]):
            if "revenue intelligence inbox" in transcript_text and any(w in transcript_text for w in ["your api", "your platform", "your service"]):
                pass  # This is about selling Revenue Intelligence Inbox, not evaluating a vendor
            elif any(w in title for w in ["ledgerbridge", "supplier"]) or \
                 any(w in transcript_text for w in ["ledgerbridge", "our integration", "your sandbox"]):
                routes.append({"route": "vendor_evaluation",
                               "reason": "Revenue Intelligence Inbox appears to be evaluating an external vendor/supplier for integration."})

        # Existing customer
        if any(w in transcript_text for w in ["migration", "existing cards", "current programme", 
                                                "login", "account setup", "department", "your account"]):
            routes.append({"route": "existing_customer",
                           "reason": "Discussion involves an existing customer's account, migration, or support issue."})

        # New prospect / demo
        if any(w in title for w in ["demonstration", "demo", "discussion"]) and \
           any(w in transcript_text for w in ["proposal", "pricing", "considering"]):
            if not any(r["route"] in ("existing_customer", "internal", "vendor_evaluation") for r in routes):
                routes.append({"route": "new_prospect",
                               "reason": "Meeting appears to be a product demonstration or sales discussion with a prospect."})

        # Follow-up signals
        if any(w in transcript_text for w in ["follow-up", "next week", "send the details", "come back"]):
            if not any(r["route"] == "follow_up" for r in routes):
                routes.append({"route": "follow_up",
                               "reason": "Transcript indicates follow-up actions were agreed."})

    if routes:
        return routes

    # Title-based fallback
    if "setup" in title:
        return [{"route": "existing_customer",
                 "reason": "Meeting title suggests customer setup/onboarding."}]
    if "demo" in title or "demonstration" in title:
        return [{"route": "new_prospect",
                 "reason": "Meeting title suggests a product demonstration."}]

    return []


def apply_route_suggestions(conn: sqlite3.Connection) -> int:
    """Generate and store route suggestions for all records that lack them.

    Returns the number of records that received new suggestions.
    """
    now = datetime.now(timezone.utc).isoformat()
    records = conn.execute("""
        SELECT sr.* FROM source_records sr
        WHERE NOT EXISTS (
            SELECT 1 FROM route_suggestions rs 
            WHERE rs.source_type = sr.source_type AND rs.source_id = sr.source_id
        )
    """).fetchall()

    count = 0
    for rec in records:
        rec_dict = dict(rec)
        suggestions = suggest_routes(rec_dict)
        for s in suggestions:
            conn.execute("""
                INSERT INTO route_suggestions (source_type, source_id, route, reason, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (rec_dict["source_type"], rec_dict["source_id"], s["route"], s["reason"], now))
        count += 1

    conn.commit()
    return count


def refresh_routes_for_record(conn: sqlite3.Connection, source_type: str, source_id: str) -> None:
    """Re-generate route suggestions for a specific record (e.g., after an update).

    Does NOT touch manual overrides — those persist.
    """
    now = datetime.now(timezone.utc).isoformat()

    # Remove old suggestions
    conn.execute(
        "DELETE FROM route_suggestions WHERE source_type = ? AND source_id = ?",
        (source_type, source_id)
    )

    rec = conn.execute(
        "SELECT * FROM source_records WHERE source_type = ? AND source_id = ?",
        (source_type, source_id)
    ).fetchone()

    if rec:
        suggestions = suggest_routes(dict(rec))
        for s in suggestions:
            conn.execute("""
                INSERT INTO route_suggestions (source_type, source_id, route, reason, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (source_type, source_id, s["route"], s["reason"], now))

    conn.commit()
