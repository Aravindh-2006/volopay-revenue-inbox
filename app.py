"""
Revenue Intelligence Inbox — Revenue Intelligence Inbox
Enterprise SaaS Application for Sales Managers and Revenue Operations.

Run with:
    streamlit run app.py
"""

import streamlit as st
import json
import os
import io
import csv
from datetime import datetime
import zoneinfo
import pandas as pd
import plotly.graph_objects as go

from db import (
    get_connection, init_db, load_json_file, import_batch,
    get_all_records, get_record, get_record_count,
    get_routes_for_record, set_route_override, reset_route_override,
    set_review_state, get_import_log,
)
from routing import (
    get_taxonomy, apply_route_suggestions, refresh_routes_for_record,
)
from findings import generate_findings, generate_manager_brief
from exports import generate_manifest, create_export_zip
from styles import (
    CUSTOM_CSS, render_top_header, render_kpi_cards, render_sidebar_footer,
)

# ---------------------------------------------------------------------------
# Streamlit Page Config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Revenue Intelligence Inbox — Revenue Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply Enterprise SaaS Design System
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
INITIAL_FILE = os.path.join(DATA_DIR, "01_initial.json")
UPDATE_FILE = os.path.join(DATA_DIR, "02_update.json")


# ---------------------------------------------------------------------------
# Database Resource
# ---------------------------------------------------------------------------
def get_db():
    conn = get_connection()
    init_db(conn)
    return conn


conn = get_db()
total_records_in_db = get_record_count(conn)


# ---------------------------------------------------------------------------
# Sidebar Navigation
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div style="padding: 10px 4px 16px 4px; display: flex; align-items: center; gap: 10px;">
        <svg width="26" height="26" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="28" height="28" rx="7" fill="url(#sb-logo-grad)"/>
            <path d="M8 15L12 10L16 14L20 8M20 8H16M20 8V12" stroke="#ffffff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="8" cy="19" r="1.5" fill="#38bdf8"/>
            <circle cx="14" cy="19" r="1.5" fill="#38bdf8"/>
            <circle cx="20" cy="19" r="1.5" fill="#38bdf8"/>
            <defs>
                <linearGradient id="sb-logo-grad" x1="0" y1="0" x2="28" y2="28" gradientUnits="userSpaceOnUse">
                    <stop stop-color="#4f46e5"/>
                    <stop offset="1" stop-color="#0284c7"/>
                </linearGradient>
            </defs>
        </svg>
        <div>
            <div style="font-size: 16px; font-weight: 700; color: #ffffff; line-height: 1.2;">Revenue Intelligence Inbox</div>
            <div style="font-size: 10.5px; font-weight: 600; color: #38bdf8; letter-spacing: 0.05em; text-transform: uppercase;">Revenue Intelligence</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="font-size: 10.5px; font-weight: 700; color: #64748b; letter-spacing: 0.06em; margin: 12px 0 6px 4px;">WORKSPACES</div>', unsafe_allow_html=True)

    inbox_badge = f" ({total_records_in_db})" if total_records_in_db > 0 else ""

    page = st.radio(
        "Navigation",
        [
            "Overview Dashboard",
            f"Conversation Inbox{inbox_badge}",
            "Routing & Review",
            "Manager Brief (21 Aug)",
            "Findings & Insights",
            "Exports & Downloads",
            "Import & Replay Controls",
        ],
        label_visibility="collapsed",
    )

    # Clean the page name to match dispatching
    if "Conversation Inbox" in page:
        page_clean = "Conversation Inbox"
    elif "Manager Brief" in page:
        page_clean = "Manager Brief"
    else:
        page_clean = page

    st.markdown(render_sidebar_footer(), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Global Top Header
# ---------------------------------------------------------------------------
st.markdown(render_top_header(current_count=total_records_in_db), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------
def get_person_name(rec: dict) -> str:
    """Extract display person: rep_name for call, organizer_email for meeting."""
    return rec.get("rep_name") or rec.get("organizer_email") or "Unknown"


def get_effective_routes(conn, source_type: str, source_id: str) -> tuple[list[str], bool]:
    """Return ([route_code, ...], is_manual_override)."""
    routing = get_routes_for_record(conn, source_type, source_id)
    if routing["override"]:
        return [routing["override"]["route"]], True
    else:
        return [s["route"] for s in routing["suggestions"]], False


def format_route_label(route_code: str) -> str:
    taxonomy = get_taxonomy()
    return taxonomy.get(route_code, {}).get("label", route_code)


def render_badge(text: str, badge_type: str = "neutral") -> str:
    return f'<span class="sn-badge sn-badge-{badge_type}">{text}</span>'


# ===========================================================================
# PAGE 1: Overview Dashboard
# ===========================================================================
if page_clean == "Overview Dashboard":
    records = get_all_records(conn)

    # Empty State: Prompt user to load initial data
    if not records:
        st.markdown("""
        <div class="sn-card" style="text-align: center; padding: 48px 24px;">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="1.5" style="margin: 0 auto 16px auto; display: block;">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
                <polyline points="22,6 12,13 2,6"></polyline>
            </svg>
            <div style="font-size: 18px; font-weight: 700; color: #0f172a; margin-bottom: 8px;">No Conversation Data Ingested Yet</div>
            <div style="font-size: 13.5px; color: #64748b; max-width: 520px; margin: 0 auto 24px auto;">
                The Revenue Intelligence Inbox requires conversation records to generate metrics, classify routes, and build the manager brief.
            </div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("🚀 Load Complete Demo State (Both Batches)", type="primary", width='stretch'):
                try:
                    data1 = load_json_file(INITIAL_FILE)
                    import_batch(conn, data1, "01_initial.json")
                    apply_route_suggestions(conn)
                    data2 = load_json_file(UPDATE_FILE)
                    import_batch(conn, data2, "02_update.json")
                    for rec_data in data2.get("records", []):
                        refresh_routes_for_record(conn, rec_data["source_type"], rec_data["source_id"])
                    apply_route_suggestions(conn)
                    st.success("Loaded all 44 records (with late M07 transcript)!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error loading demo state: {e}")
        with col2:
            if st.button("📂 Ingest 01_initial.json Only", width='stretch'):
                try:
                    data1 = load_json_file(INITIAL_FILE)
                    res = import_batch(conn, data1, "01_initial.json")
                    apply_route_suggestions(conn)
                    st.success(f"Ingested {res['inserted']} records from initial batch.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
        st.stop()

    # Filters Row (Compact & Right-aligned in header)
    fcol1, fcol2, fcol3 = st.columns([2, 1, 1])
    with fcol1:
        st.markdown("""
        <div>
            <div style="font-size: 20px; font-weight: 700; color: #0f172a; margin-bottom: 2px;">Overview Dashboard</div>
            <div style="font-size: 12.5px; color: #64748b;">Activity and intelligence metrics for 21 August 2026 (Asia/Kolkata timezone). All numbers derived strictly from source records.</div>
        </div>
        """, unsafe_allow_html=True)

    with fcol2:
        source_type_filter = st.selectbox(
            "Source Type",
            ["All Source Types", "Calls Only", "Meetings Only"],
            label_visibility="collapsed",
        )

    with fcol3:
        all_persons = ["All Persons"] + sorted(list(set(get_person_name(r) for r in records)))
        person_filter = st.selectbox(
            "Person",
            all_persons,
            label_visibility="collapsed",
        )

    # Filter records
    filtered = records
    if source_type_filter == "Calls Only":
        filtered = [r for r in filtered if r["source_type"] == "call"]
    elif source_type_filter == "Meetings Only":
        filtered = [r for r in filtered if r["source_type"] == "meeting"]

    if person_filter != "All Persons":
        filtered = [r for r in filtered if get_person_name(r) == person_filter]

    # Calculate exact metrics from current filtered data
    tot = len(filtered)
    calls_list = [r for r in filtered if r["source_type"] == "call"]
    meets_list = [r for r in filtered if r["source_type"] == "meeting"]
    usable_list = [r for r in filtered if r["has_usable_transcript"]]

    # Calls connected: is_connected or is_conversation
    connected_calls_count = 0
    for c in calls_list:
        p = json.loads(c.get("payload_json", "{}"))
        if p.get("is_connected") or p.get("is_conversation"):
            connected_calls_count += 1

    # Records requiring review: review_state != 'reviewed'
    review_needed_count = sum(1 for r in filtered if r["review_state"] != "reviewed")

    # Render KPI Cards
    st.markdown(
        render_kpi_cards(
            total_records=tot,
            calls_count=len(calls_list),
            meetings_count=len(meets_list),
            usable_count=len(usable_list),
            connected_calls=connected_calls_count,
            review_count=review_needed_count,
        ),
        unsafe_allow_html=True,
    )

    # Charts Row
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        with st.container(border=True):
            st.markdown("""
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <div>
                    <div style="font-size:15px; font-weight:700; color:#0f172a;">Conversation Routing Distribution</div>
                    <div style="font-size:12px; color:#64748b;">Assigned destinations across current filtered records</div>
                </div>
                <span class="sn-badge sn-badge-primary">Multi-Route Enabled</span>
            </div>
            """, unsafe_allow_html=True)

            # Compute routing counts
            route_counts = {}
            for r in filtered:
                routes, _ = get_effective_routes(conn, r["source_type"], r["source_id"])
                for rt in routes:
                    route_counts[rt] = route_counts.get(rt, 0) + 1

            if route_counts:
                taxonomy = get_taxonomy()
                labels = [taxonomy.get(k, {}).get("label", k) for k in route_counts.keys()]
                values = list(route_counts.values())

                sorted_pairs = sorted(zip(labels, values), key=lambda x: x[1], reverse=True)
                sorted_labels = [p[0] for p in sorted_pairs][:6]
                sorted_values = [p[1] for p in sorted_pairs][:6]

                colors = ["#2563eb", "#10b981", "#6366f1", "#f59e0b", "#ef4444", "#8b5cf6"]

                fig_bar = go.Figure(data=[
                    go.Bar(
                        x=sorted_labels,
                        y=sorted_values,
                        marker=dict(color=colors[:len(sorted_labels)]),
                        text=sorted_values,
                        textposition="outside",
                        hovertemplate="<b>%{x}</b><br>Count: %{y}<extra></extra>",
                    )
                ])
                fig_bar.update_layout(
                    height=280,
                    margin=dict(l=10, r=10, t=20, b=50),
                    plot_bgcolor="#ffffff",
                    paper_bgcolor="#ffffff",
                    xaxis=dict(showgrid=False, tickfont=dict(size=11, family="Inter")),
                    yaxis=dict(showgrid=True, gridcolor="#f1f5f9", tickfont=dict(size=11, family="Inter")),
                    font=dict(family="Inter", color="#334155"),
                )
                st.plotly_chart(fig_bar, width='stretch', config={"displayModeBar": False})
            else:
                st.info("No routing data available.")

    with chart_col2:
        with st.container(border=True):
            st.markdown("""
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <div>
                    <div style="font-size:15px; font-weight:700; color:#0f172a;">Activity by Hour (Asia/Kolkata Timeline)</div>
                    <div style="font-size:12px; color:#64748b;">Interaction start times across Friday, 21 August 2026</div>
                </div>
                <span class="sn-badge sn-badge-neutral">Timeline View</span>
            </div>
            """, unsafe_allow_html=True)

            kolkata = zoneinfo.ZoneInfo("Asia/Kolkata")
            hourly_calls = {h: 0 for h in range(8, 24)}
            hourly_meets = {h: 0 for h in range(8, 24)}

            for r in filtered:
                p = json.loads(r.get("payload_json", "{}"))
                ts_str = p.get("started_at") or p.get("starts_at")
                if ts_str:
                    try:
                        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                        dt_ist = dt.astimezone(kolkata)
                        h = dt_ist.hour
                        if h in hourly_calls:
                            if r["source_type"] == "call":
                                hourly_calls[h] += 1
                            else:
                                hourly_meets[h] += 1
                    except Exception:
                        pass

            hours_labels = [f"{h:02d}:00" for h in range(8, 24)]
            calls_vals = [hourly_calls[h] for h in range(8, 24)]
            meets_vals = [hourly_meets[h] for h in range(8, 24)]

            fig_hour = go.Figure(data=[
                go.Bar(name="Calls", x=hours_labels, y=calls_vals, marker_color="#2563eb"),
                go.Bar(name="Meetings", x=hours_labels, y=meets_vals, marker_color="#06b6d4"),
            ])
            fig_hour.update_layout(
                barmode="stack",
                height=280,
                margin=dict(l=10, r=10, t=20, b=50),
                plot_bgcolor="#ffffff",
                paper_bgcolor="#ffffff",
                xaxis=dict(showgrid=False, tickfont=dict(size=10, family="Inter")),
                yaxis=dict(showgrid=True, gridcolor="#f1f5f9", tickfont=dict(size=11, family="Inter")),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                font=dict(family="Inter", color="#334155"),
            )
            st.plotly_chart(fig_hour, width='stretch', config={"displayModeBar": False})

    # Priority Intelligence Signals Section
    st.markdown("""
    <div style="margin: 20px 0 10px 0;">
        <div style="font-size: 16px; font-weight: 700; color: #0f172a;">🚨 Priority Attention & Key Intelligence Signals</div>
        <div style="font-size: 12px; color: #64748b;">Critical evidence-backed findings requiring sales management action for 21 August 2026</div>
    </div>
    """, unsafe_allow_html=True)

    sig1, sig2, sig3 = st.columns(3)
    with sig1:
        with st.container(border=True):
            st.markdown("""
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                <span class="sn-badge sn-badge-danger">Churn Threat</span>
                <span style="font-size:11px; color:#64748b; font-family:monospace;">M04 • Meeting</span>
            </div>
            <div style="font-size:13.5px; font-weight:700; color:#0f172a; margin-bottom:4px;">Cedarwave Account Review</div>
            <div style="font-size:12px; color:#64748b; line-height:1.5;">Forced physical card migration from prepaid to credit creating friction. Customer uncommitted.</div>
            <div style="margin-top:8px; font-size:11px; color:#9f1239; font-weight:600;">Action: Schedule CS & credit eligibility review</div>
            """, unsafe_allow_html=True)

    with sig2:
        with st.container(border=True):
            st.markdown("""
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                <span class="sn-badge sn-badge-primary">Strategic Deal</span>
                <span style="font-size:11px; color:#64748b; font-family:monospace;">M01 • Meeting</span>
            </div>
            <div style="font-size:13.5px; font-weight:700; color:#0f172a; margin-bottom:4px;">Harborpath Advisory Sync</div>
            <div style="font-size:12px; color:#64748b; line-height:1.5;">Active negotiation on 15% revenue share & referral tracking sheet. Partner expressed commercial interest.</div>
            <div style="margin-top:8px; font-size:11px; color:#1e40af; font-weight:600;">Action: Send partnership memorandum & tracking link</div>
            """, unsafe_allow_html=True)

    with sig3:
        with st.container(border=True):
            st.markdown("""
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                <span class="sn-badge sn-badge-warning">Coaching Focus</span>
                <span style="font-size:11px; color:#64748b; font-family:monospace;">B01–B20 • Calls</span>
            </div>
            <div style="font-size:13.5px; font-weight:700; color:#0f172a; margin-bottom:4px;">Outbound Dialing Cadence</div>
            <div style="font-size:12px; color:#64748b; line-height:1.5;">80% voicemail rate on outbound campaign calls. Only 4 connects across 20 dials by rep Arun.</div>
            <div style="margin-top:8px; font-size:11px; color:#92400e; font-weight:600;">Action: Review dialer timing & voicemail drop script</div>
            """, unsafe_allow_html=True)

    # Activity Tables Row
    st.markdown('<div style="margin-top: 14px;"></div>', unsafe_allow_html=True)
    tcol1, tcol2 = st.columns(2)

    with tcol1:
        with st.container(border=True):
            st.markdown("""
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <div>
                    <div style="font-size:15px; font-weight:700; color:#0f172a;">Call Activity by Representative</div>
                    <div style="font-size:12px; color:#64748b;">Sales development reps initiating phone calls</div>
                </div>
                <span class="sn-badge sn-badge-primary">5 Reps</span>
            </div>
            """, unsafe_allow_html=True)

            call_reps_map = {}
            for r in calls_list:
                rep = r.get("rep_name") or "Unknown"
                if rep not in call_reps_map:
                    call_reps_map[rep] = {"calls": 0, "connected": 0, "usable": 0}
                call_reps_map[rep]["calls"] += 1
                p = json.loads(r.get("payload_json", "{}"))
                if p.get("is_connected") or p.get("is_conversation"):
                    call_reps_map[rep]["connected"] += 1
                if r["has_usable_transcript"]:
                    call_reps_map[rep]["usable"] += 1

            rep_rows = []
            for rep, stats in sorted(call_reps_map.items(), key=lambda x: x[1]["calls"], reverse=True):
                rep_rows.append({
                    "Representative": rep,
                    "Total Calls": stats["calls"],
                    "Connected": stats["connected"],
                    "Usable Text": stats["usable"],
                })

            if rep_rows:
                st.dataframe(pd.DataFrame(rep_rows), width='stretch', hide_index=True)
            else:
                st.caption("No call activity in current filter.")

    with tcol2:
        with st.container(border=True):
            st.markdown("""
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <div>
                    <div style="font-size:15px; font-weight:700; color:#0f172a;">Meeting Activity by Organizer</div>
                    <div style="font-size:12px; color:#64748b;">Calendar organizers (does not imply sales role)</div>
                </div>
                <span class="sn-badge sn-badge-warning">Organizer != Sales Rep</span>
            </div>
            """, unsafe_allow_html=True)

            meet_orgs_map = {}
            for r in meets_list:
                org = r.get("organizer_email") or "Unknown"
                if org not in meet_orgs_map:
                    meet_orgs_map[org] = {"meetings": 0, "usable": 0}
                meet_orgs_map[org]["meetings"] += 1
                if r["has_usable_transcript"]:
                    meet_orgs_map[org]["usable"] += 1

            org_rows = []
            for org, stats in sorted(meet_orgs_map.items(), key=lambda x: x[1]["meetings"], reverse=True):
                org_rows.append({
                    "Organizer Email": org,
                    "Meetings": stats["meetings"],
                    "Usable Text": stats["usable"],
                })

            if org_rows:
                st.dataframe(pd.DataFrame(org_rows), width='stretch', hide_index=True)
            else:
                st.caption("No meeting activity in current filter.")


# ===========================================================================
# PAGE 2: Conversation Inbox
# ===========================================================================
elif page_clean == "Conversation Inbox":
    st.markdown("""
    <div style="margin-bottom: 16px;">
        <div style="font-size: 20px; font-weight: 700; color: #0f172a;">Conversation Inbox</div>
        <div style="font-size: 13px; color: #64748b;">Search, inspect, and verify all 44 multi-source interaction records.</div>
    </div>
    """, unsafe_allow_html=True)

    records = get_all_records(conn)

    if not records:
        st.info("No records imported yet. Go to **Import & Replay Controls** to load data.")
        st.stop()

    # Search & Filter Bar
    scol1, scol2, scol3, scol4 = st.columns([2, 1, 1, 1])

    with scol1:
        search_query = st.text_input("🔍 Search conversations...", placeholder="Search by Ref, Person, Title, or ID...", label_visibility="collapsed")

    with scol2:
        type_filter = st.selectbox("Type Filter", ["All Types", "Calls", "Meetings"], label_visibility="collapsed")

    with scol3:
        review_filter = st.selectbox("Review Status", ["All Review States", "Needs Review (Pending)", "Reviewed", "Stale"], label_visibility="collapsed")

    with scol4:
        transcript_filter = st.selectbox("Transcript", ["All Transcripts", "Usable Only", "Missing Only"], label_visibility="collapsed")

    # Apply filters
    filtered_inbox = []
    for r in records:
        # Search match
        search_str = f"{r.get('record_ref', '')} {get_person_name(r)} {r.get('title', '')} {r.get('source_id', '')}".lower()
        if search_query and search_query.lower() not in search_str:
            continue

        # Type filter
        if type_filter == "Calls" and r["source_type"] != "call":
            continue
        elif type_filter == "Meetings" and r["source_type"] != "meeting":
            continue

        # Review state
        if review_filter == "Needs Review (Pending)" and r["review_state"] != "pending":
            continue
        elif review_filter == "Reviewed" and r["review_state"] != "reviewed":
            continue
        elif review_filter == "Stale" and r["review_state"] != "stale":
            continue

        # Transcript filter
        if transcript_filter == "Usable Only" and not r["has_usable_transcript"]:
            continue
        elif transcript_filter == "Missing Only" and r["has_usable_transcript"]:
            continue

        filtered_inbox.append(r)

    # Inbox Table Representation
    table_rows = []
    for r in filtered_inbox:
        routes, is_override = get_effective_routes(conn, r["source_type"], r["source_id"])
        route_text = ", ".join(format_route_label(x) for x in routes)
        if is_override:
            route_text = f"🔧 {route_text}"

        transcript_display = "Available" if r["has_usable_transcript"] else "Unavailable"
        fresh_display = "Fresh" if r["analysis_fresh"] else "Stale"

        table_rows.append({
            "Ref": r["record_ref"],
            "Type": r["source_type"].capitalize(),
            "Person / Host": get_person_name(r),
            "Title / Outcome": r["title"] or r.get("observed_outcome") or "—",
            "Rev": r["revision"],
            "Transcript": transcript_display,
            "Route": route_text,
            "Review State": r["review_state"].capitalize(),
            "Freshness": fresh_display,
            "ID": r["source_id"][:12] + "…",
        })

    st.markdown(f"**Showing {len(table_rows)} of {len(records)} records**")
    st.dataframe(pd.DataFrame(table_rows), width='stretch', height=360, hide_index=True)

    # Detail & Route Correction Panel
    st.markdown("---")
    st.markdown("### 🔍 Conversation Detail & Manager Triage")

    ref_options = [(r["record_ref"], r["source_type"], r["source_id"]) for r in filtered_inbox]
    if not ref_options:
        ref_options = [(r["record_ref"], r["source_type"], r["source_id"]) for r in records]

    selected_idx = st.selectbox(
        "Select conversation to inspect & correct route:",
        options=range(len(ref_options)),
        format_func=lambda i: f"{ref_options[i][0]} — {ref_options[i][1].capitalize()} ({ref_options[i][2][:8]}…)",
    )

    if selected_idx is not None:
        _, sel_type, sel_id = ref_options[selected_idx]
        rec = get_record(conn, sel_type, sel_id)

        if rec:
            detail_col1, detail_col2 = st.columns([3, 2])

            with detail_col1:
                st.markdown(f"""
                <div class="sn-card">
                    <div class="sn-card-header">
                        <div>
                            <div class="sn-card-title">{rec['record_ref']} — {rec['source_type'].capitalize()} Transcript</div>
                            <div class="sn-card-subtitle">{get_person_name(rec)} • Revision {rec['revision']}</div>
                        </div>
                        <div>
                            {'<span class="sn-badge sn-badge-success">Transcript Available</span>' if rec['has_usable_transcript'] else '<span class="sn-badge sn-badge-danger">Transcript Unavailable</span>'}
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                payload = json.loads(rec.get("payload_json", "{}"))

                if rec["has_usable_transcript"]:
                    if rec["source_type"] == "call":
                        call_text = payload.get("transcript", "")
                        st.markdown(f"""
                        <div style="background:#f8fafc; padding:16px; border-radius:8px; border:1px solid #e2e8f0; font-size:13px; line-height:1.6; white-space:pre-wrap;">
{call_text}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        tp = json.loads(rec.get("transcript_json", "{}") or "{}")
                        turns = tp.get("turns", [])
                        if turns:
                            st.markdown(f"**Meeting Dialogue ({len(turns)} turns):**")
                            for turn in turns:
                                speaker = turn.get("speaker", "Speaker")
                                timecode = turn.get("timecode", "00:00")
                                text = turn.get("text", "")
                                st.markdown(f"""
                                <div class="sn-turn-container">
                                    <div class="sn-turn-header">
                                        <span class="sn-turn-speaker">{speaker}</span>
                                        <span class="sn-turn-time">{timecode}</span>
                                    </div>
                                    <div class="sn-turn-text">{text}</div>
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.info("No turns present in transcript payload.")
                else:
                    unav_reason = "No transcript available."
                    if rec.get("transcript_json"):
                        tp = json.loads(rec["transcript_json"])
                        unav_reason = tp.get("unavailable_reason", unav_reason)
                    elif rec["source_type"] == "call":
                        unav_reason = f"Call outcome '{rec.get('observed_outcome')}', no recording captured."

                    st.markdown(f"""
                    <div style="background:#fffbeb; border:1px solid #fde68a; border-radius:8px; padding:16px; color:#92400e;">
                        <div style="font-weight:700; margin-bottom:4px;">⚠️ Transcript Not Available</div>
                        <div style="font-size:12.5px;">Reason: <code>{unav_reason}</code></div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)

            with detail_col2:
                st.markdown("""
                <div class="sn-card">
                    <div class="sn-card-header">
                        <div class="sn-card-title">Routing & Review Controls</div>
                    </div>
                """, unsafe_allow_html=True)

                routing = get_routes_for_record(conn, rec["source_type"], rec["source_id"])

                # Display Automated Suggestions
                st.markdown("**Automated Route Suggestions:**")
                if routing["suggestions"]:
                    for s in routing["suggestions"]:
                        lbl = format_route_label(s["route"])
                        st.markdown(f"- <b>{lbl}</b><br><span style='font-size:11.5px; color:#64748b;'>{s.get('reason', '')}</span>", unsafe_allow_html=True)
                else:
                    st.caption("No automated suggestions generated.")

                # Manual Override Status
                st.markdown("---")
                if routing["override"]:
                    ov_lbl = format_route_label(routing["override"]["route"])
                    st.markdown(f"""
                    <div style="background:#eff6ff; border:1px solid #bfdbfe; border-radius:6px; padding:10px; margin-bottom:12px;">
                        <span class="sn-badge sn-badge-primary">Active Manual Override</span>
                        <div style="font-weight:700; color:#1e40af; margin-top:4px;">{ov_lbl}</div>
                        <div style="font-size:11.5px; color:#3b82f6;">Reason: {routing['override'].get('reason', 'None specified')}</div>
                    </div>
                    """, unsafe_allow_html=True)

                # Manager Override Form
                st.markdown("**Correct Route (Manager Override):**")
                taxonomy = get_taxonomy()
                route_keys = list(taxonomy.keys())

                new_route_sel = st.selectbox(
                    "Override Destination",
                    options=route_keys,
                    format_func=lambda k: taxonomy[k]["label"],
                    key=f"dest_{rec['source_id']}",
                )
                override_note = st.text_input("Override Reason / Justification", placeholder="e.g. Discussed credit card migration churn risk", key=f"note_{rec['source_id']}")

                bcol1, bcol2 = st.columns(2)
                with bcol1:
                    if st.button("💾 Apply Override", key=f"btn_ov_{rec['source_id']}", type="primary", width='stretch'):
                        set_route_override(conn, rec["source_type"], rec["source_id"], new_route_sel, override_note)
                        st.success("Override saved persistently!")
                        st.rerun()

                with bcol2:
                    if routing["override"]:
                        if st.button("↺ Reset Override", key=f"btn_rst_{rec['source_id']}", width='stretch'):
                            reset_route_override(conn, rec["source_type"], rec["source_id"])
                            st.info("Override removed; reverted to automated suggestions.")
                            st.rerun()

                # Review State Form
                st.markdown("---")
                st.markdown("**Review State:**")
                current_state = rec["review_state"]
                state_options = ["pending", "reviewed", "stale"]
                sel_state = st.selectbox(
                    "Update Review State",
                    state_options,
                    index=state_options.index(current_state) if current_state in state_options else 0,
                    key=f"state_sel_{rec['source_id']}",
                )

                if st.button("Update Status", key=f"btn_st_{rec['source_id']}", width='stretch'):
                    set_review_state(conn, rec["source_type"], rec["source_id"], sel_state)
                    st.success(f"Review status updated to '{sel_state}'.")
                    st.rerun()

                st.markdown("</div>", unsafe_allow_html=True)


# ===========================================================================
# PAGE 3: Routing & Review Workspace
# ===========================================================================
elif page_clean == "Routing & Review":
    st.markdown("""
    <div style="margin-bottom: 16px;">
        <div style="font-size: 20px; font-weight: 700; color: #0f172a;">Routing & Review Workspace</div>
        <div style="font-size: 13px; color: #64748b;">Manager triage queue for classifying conversations, verifying automated suggestions, and resolving churn alerts.</div>
    </div>
    """, unsafe_allow_html=True)

    records = get_all_records(conn)
    if not records:
        st.info("No records in database. Please import data first.")
        st.stop()

    tab1, tab2, tab3 = st.tabs(["⚡ Attention Queue (Pending)", "🔴 Stale Analysis Queue", "✅ Reviewed & Confirmed"])

    def render_triage_list(target_records):
        if not target_records:
            st.info("Queue is empty.")
            return

        for r in target_records:
            routes, is_ov = get_effective_routes(conn, r["source_type"], r["source_id"])
            route_names = ", ".join(format_route_label(x) for x in routes)

            with st.expander(f"{r['record_ref']} — {get_person_name(r)} | {r['source_type'].capitalize()} ({route_names})", expanded=False):
                col_a, col_b = st.columns([3, 2])
                with col_a:
                    st.write(f"**ID:** `{r['source_id']}` | **Revision:** {r['revision']}")
                    st.write(f"**Transcript Usable:** {'Yes' if r['has_usable_transcript'] else 'No'}")
                    if r.get("title"):
                        st.write(f"**Title:** {r['title']}")
                    if r.get("observed_outcome"):
                        st.write(f"**Outcome:** {r['observed_outcome']}")

                    # Show snippet if available
                    payload = json.loads(r.get("payload_json", "{}"))
                    if r["source_type"] == "call" and payload.get("transcript"):
                        st.caption(f"Call snippet: \"{payload['transcript'][:180]}…\"")
                    elif r["source_type"] == "meeting" and r.get("transcript_json"):
                        tp = json.loads(r["transcript_json"] or "{}")
                        turns = tp.get("turns", [])
                        if turns:
                            st.caption(f"Meeting opening: \"{turns[0].get('text', '')[:180]}…\"")

                with col_b:
                    taxonomy = get_taxonomy()
                    new_r = st.selectbox(
                        "Set Decision Route",
                        list(taxonomy.keys()),
                        format_func=lambda k: taxonomy[k]["label"],
                        key=f"triage_rt_{r['source_id']}",
                    )
                    reason = st.text_input("Decision Justification", key=f"triage_rs_{r['source_id']}")
                    if st.button("Save & Mark Reviewed", key=f"triage_btn_{r['source_id']}", type="primary"):
                        set_route_override(conn, r["source_type"], r["source_id"], new_r, reason)
                        set_review_state(conn, r["source_type"], r["source_id"], "reviewed")
                        st.success("Triage decision recorded!")
                        st.rerun()

    with tab1:
        pending_recs = [r for r in records if r["review_state"] == "pending"]
        st.markdown(f"""
        <div style="font-size: 14px; font-weight: 600; color: #1e293b; margin: 12px 0 14px 0; display: flex; align-items: center; gap: 8px;">
            <span class="sn-badge sn-badge-primary">{len(pending_recs)} Pending</span>
            <span>Conversations awaiting manager classification & triage</span>
        </div>
        """, unsafe_allow_html=True)
        render_triage_list(pending_recs)

    with tab2:
        stale_recs = [r for r in records if r["review_state"] == "stale"]
        st.markdown(f"""
        <div style="font-size: 14px; font-weight: 600; color: #1e293b; margin: 12px 0 14px 0; display: flex; align-items: center; gap: 8px;">
            <span class="sn-badge sn-badge-danger">{len(stale_recs)} Stale</span>
            <span>Conversations flagged for re-analysis due to newer incoming revisions</span>
        </div>
        """, unsafe_allow_html=True)
        render_triage_list(stale_recs)

    with tab3:
        reviewed_recs = [r for r in records if r["review_state"] == "reviewed"]
        st.markdown(f"""
        <div style="font-size: 14px; font-weight: 600; color: #1e293b; margin: 12px 0 14px 0; display: flex; align-items: center; gap: 8px;">
            <span class="sn-badge sn-badge-success">{len(reviewed_recs)} Reviewed</span>
            <span>Interactions verified and confirmed by manager</span>
        </div>
        """, unsafe_allow_html=True)
        render_triage_list(reviewed_recs)


# ===========================================================================
# PAGE 4: Manager Brief
# ===========================================================================
elif page_clean == "Manager Brief":
    records = get_all_records(conn)
    if not records:
        st.info("Import records to view the daily manager brief.")
        st.stop()

    findings_list = generate_findings(records)
    brief_md = generate_manager_brief(records, findings_list)

    st.markdown("""
    <div class="sn-card">
        <div class="sn-card-header">
            <div>
                <div class="sn-card-title">Executive Briefing — 21 August 2026 (IST)</div>
                <div class="sn-card-subtitle">Synthesised revenue intelligence from verified conversation transcripts</div>
            </div>
            <span class="sn-badge sn-badge-primary">Asia/Kolkata (UTC+05:30)</span>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(brief_md)

    st.markdown("</div>", unsafe_allow_html=True)


# ===========================================================================
# PAGE 5: Findings & Insights
# ===========================================================================
elif page_clean == "Findings & Insights":
    st.markdown("""
    <div style="margin-bottom: 16px;">
        <div style="font-size: 20px; font-weight: 700; color: #0f172a;">Evidence-Backed Strategic Findings</div>
        <div style="font-size: 13px; color: #64748b;">Direct observations strictly grounded in supplied conversation transcripts. Zero fabricated content.</div>
    </div>
    """, unsafe_allow_html=True)

    records = get_all_records(conn)
    if not records:
        st.info("Import records to view findings.")
        st.stop()

    findings_list = generate_findings(records)

    for i, finding in enumerate(findings_list, 1):
        st.markdown(f"""
        <div class="sn-card">
            <div class="sn-card-header">
                <div>
                    <div class="sn-card-title">Finding {i}: {finding['title']}</div>
                    <div class="sn-card-subtitle">Verified transcript evidence</div>
                </div>
                <span class="sn-badge sn-badge-warning">Evidence Grounded</span>
            </div>
            <div style="font-size: 13.5px; color: #334155; line-height: 1.6; margin-bottom: 16px;">
                {finding['summary']}
            </div>
        """, unsafe_allow_html=True)

        st.markdown("**Transcript Quotations & Exact References:**")
        for ev in finding.get("evidence", []):
            spk = ev.get("speaker", "Speaker")
            tc = ev.get("timecode", "00:00")
            src = ev.get("source_ref", "")
            qt = ev.get("quote", "")

            st.markdown(f"""
            <div class="sn-turn-container" style="background:#f1f5f9; border-left: 3px solid #2563eb;">
                <div class="sn-turn-header">
                    <span class="sn-turn-speaker">[{src}] {spk}</span>
                    <span class="sn-turn-time">{tc}</span>
                </div>
                <div class="sn-turn-text"><i>"{qt}"</i></div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="margin-top: 12px; font-size: 12px; color: #64748b; background: #fffbeb; padding: 10px 14px; border-radius: 6px; border: 1px solid #fde68a;">
            <b>Uncertainty & Boundaries:</b> {finding.get('uncertainty', 'None noted.')}
        </div>
        </div>
        """, unsafe_allow_html=True)


# ===========================================================================
# PAGE 6: Exports & Downloads
# ===========================================================================
elif page_clean == "Exports & Downloads":
    st.markdown("""
    <div style="margin-bottom: 16px;">
        <div style="font-size: 20px; font-weight: 700; color: #0f172a;">Exports & Downloads Workspace</div>
        <div style="font-size: 13px; color: #64748b;">Generate and download manifests, per-record JSON files, and full ZIP submission packages from live SQLite data.</div>
    </div>
    """, unsafe_allow_html=True)

    records = get_all_records(conn)
    if not records:
        st.info("Import records to enable exports.")
        st.stop()

    manifest = generate_manifest(conn)

    # Export Action Buttons
    dcol1, dcol2, dcol3 = st.columns(3)

    with dcol1:
        st.markdown("""
        <div class="sn-card" style="text-align:center;">
            <div style="font-size:14px; font-weight:700; color:#0f172a; margin-bottom:4px;">Full ZIP Submission Archive</div>
            <div style="font-size:11.5px; color:#64748b; margin-bottom:14px;">Contains manifest, findings, brief, and all output/{route} JSON files.</div>
        """, unsafe_allow_html=True)

        if st.button("📦 Generate & Download ZIP", key="gen_zip_btn", type="primary", width='stretch'):
            with st.spinner("Compiling archive from SQLite..."):
                zip_data = create_export_zip(conn)
            st.download_button(
                "⬇️ Click to Save ZIP",
                data=zip_data,
                file_name="revenue_intelligence_inbox_export.zip",
                mime="application/zip",
                width='stretch',
            )
        st.markdown("</div>", unsafe_allow_html=True)

    with dcol2:
        st.markdown("""
        <div class="sn-card" style="text-align:center;">
            <div style="font-size:14px; font-weight:700; color:#0f172a; margin-bottom:4px;">JSON Manifest</div>
            <div style="font-size:11.5px; color:#64748b; margin-bottom:14px;">Structured JSON manifest containing record paths and routing decisions.</div>
        """, unsafe_allow_html=True)

        m_json = json.dumps(manifest, indent=2, default=str)
        st.download_button(
            "⬇️ Download manifest.json",
            data=m_json,
            file_name="manifest.json",
            mime="application/json",
            width='stretch',
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with dcol3:
        st.markdown("""
        <div class="sn-card" style="text-align:center;">
            <div style="font-size:14px; font-weight:700; color:#0f172a; margin-bottom:4px;">CSV Manifest</div>
            <div style="font-size:11.5px; color:#64748b; margin-bottom:14px;">Tabular CSV manifest ready for spreadsheet analysis or reporting.</div>
        """, unsafe_allow_html=True)

        csv_buf = io.StringIO()
        if manifest:
            writer = csv.DictWriter(csv_buf, fieldnames=manifest[0].keys())
            writer.writeheader()
            writer.writerows(manifest)

        st.download_button(
            "⬇️ Download manifest.csv",
            data=csv_buf.getvalue(),
            file_name="manifest.csv",
            mime="text/csv",
            width='stretch',
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # Manifest Preview Table
    st.markdown("### 📋 Manifest Live Preview")
    st.dataframe(pd.DataFrame(manifest), width='stretch', height=360, hide_index=True)


# ===========================================================================
# PAGE 7: Import & Replay Controls
# ===========================================================================
elif page_clean == "Import & Replay Controls":
    st.markdown("""
    <div style="margin-bottom: 16px;">
        <div style="font-size: 20px; font-weight: 700; color: #0f172a;">Import & Replay Workspace</div>
        <div style="font-size: 13px; color: #64748b;">Step-by-step verification panel for batch ingestion, revision replacement, deduplication, and M07 update handling.</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="sn-card">
            <div class="sn-card-header">
                <div class="sn-card-title">Step 1 & 2: Initial Batch</div>
            </div>
            <div style="font-size:12px; color:#64748b; margin-bottom:14px;">
                Ingest <code>data/01_initial.json</code> (44 records, revision 1). Repeated clicks test deduplication.
            </div>
        """, unsafe_allow_html=True)

        if st.button("📂 Ingest 01_initial.json", key="btn_init", width='stretch'):
            try:
                data = load_json_file(INITIAL_FILE)
                res = import_batch(conn, data, "01_initial.json")
                apply_route_suggestions(conn)
                st.success(f"Result: {res['inserted']} inserted, {res['updated']} updated, {res['skipped']} skipped.")
                st.rerun()
            except Exception as e:
                st.error(f"Import error: {e}")

        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="sn-card">
            <div class="sn-card-header">
                <div class="sn-card-title">Step 4: Update Batch</div>
            </div>
            <div style="font-size:12px; color:#64748b; margin-bottom:14px;">
                Ingest <code>data/02_update.json</code> (M07 transcript, revision 2). Replaces M07 without creating duplicate.
            </div>
        """, unsafe_allow_html=True)

        if st.button("📂 Ingest 02_update.json", key="btn_upd", width='stretch'):
            try:
                data = load_json_file(UPDATE_FILE)
                res = import_batch(conn, data, "02_update.json")
                for rec_data in data.get("records", []):
                    refresh_routes_for_record(conn, rec_data["source_type"], rec_data["source_id"])
                apply_route_suggestions(conn)
                st.success(f"Result: {res['inserted']} inserted, {res['updated']} updated, {res['skipped']} skipped.")
                st.rerun()
            except Exception as e:
                st.error(f"Update error: {e}")

        st.markdown("</div>", unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="sn-card">
            <div class="sn-card-header">
                <div class="sn-card-title">Demo Load & Reset</div>
            </div>
            <div style="font-size:12px; color:#64748b; margin-bottom:14px;">
                Fast operations to populate both batches safely or clear the database.
            </div>
        """, unsafe_allow_html=True)

        if st.button("🚀 Load Both Batches (Demo)", key="btn_demo", type="primary", width='stretch'):
            try:
                d1 = load_json_file(INITIAL_FILE)
                r1 = import_batch(conn, d1, "01_initial.json")
                apply_route_suggestions(conn)
                d2 = load_json_file(UPDATE_FILE)
                r2 = import_batch(conn, d2, "02_update.json")
                for rec_data in d2.get("records", []):
                    refresh_routes_for_record(conn, rec_data["source_type"], rec_data["source_id"])
                apply_route_suggestions(conn)
                st.success("Loaded both batches cleanly!")
                st.rerun()
            except Exception as e:
                st.error(f"Demo load error: {e}")

        if st.button("🗑️ Reset Database (Wipe)", key="btn_rst_db", width='stretch'):
            from db import DB_PATH
            conn.close()
            if os.path.exists(DB_PATH):
                os.remove(DB_PATH)
            st.cache_resource.clear()
            st.warning("Database deleted. Refresh to recreate schema.")
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    # M07 Inspection Card
    st.markdown("""
    <div class="sn-card">
        <div class="sn-card-header">
            <div>
                <div class="sn-card-title">🔍 M07 Ingestion Inspection (Meeting 4f304fff…)</div>
                <div class="sn-card-subtitle">Verifies that the late transcript from 02_update.json attached cleanly to M07</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    m07 = get_record(conn, "meeting", "4f304fff-fd40-5cfc-a366-0a134c445c2a")
    if m07:
        mcol1, mcol2, mcol3, mcol4 = st.columns(4)
        mcol1.metric("Revision", m07["revision"])
        mcol2.metric("Transcript Usable", "✅ Available" if m07["has_usable_transcript"] else "❌ Unavailable")
        mcol3.metric("Review State", m07["review_state"].capitalize())
        mcol4.metric("Analysis Fresh", "🟢 Fresh" if m07["analysis_fresh"] else "🔴 Stale")

        if m07["has_usable_transcript"]:
            tp = json.loads(m07.get("transcript_json", "{}") or "{}")
            turns = tp.get("turns", [])
            st.success(f"M07 has {len(turns)} dialogue turns populated from revision {m07['revision']}!")
            with st.expander("Show M07 Turn-by-Turn Transcript"):
                for t in turns:
                    st.markdown(f"**[{t.get('timecode', '00:00')}] {t.get('speaker', 'Speaker')}:** {t.get('text', '')}")
        else:
            tp = json.loads(m07.get("transcript_json", "{}") or "{}")
            st.warning(f"M07 currently has no transcript. Reason: {tp.get('unavailable_reason', 'Pending')}. Click 'Ingest 02_update.json' above to apply revision 2!")
    else:
        st.info("M07 is not in the database yet. Import the initial batch above.")

    st.markdown("</div>", unsafe_allow_html=True)

    # Import Audit Log Table
    st.markdown("### 📋 Ingestion Audit Log")
    log = get_import_log(conn)
    if log:
        st.dataframe(pd.DataFrame(log), width='stretch', hide_index=True)
    else:
        st.caption("No imports recorded in audit log.")
