"""
Styles module — Enterprise SaaS Design System for Revenue Intelligence Inbox / Revenue Intelligence Inbox.

Provides CSS styles, layout components, badges, KPI cards, and custom HTML widgets
inspired by modern fintech platforms.
"""

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* Global Reset & Typography */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
}

/* Light Background for Main Workspace */
.stApp {
    background-color: #f8fafc !important;
    color: #0f172a !important;
}

[data-testid="stMain"], .main, section.main {
    background-color: #f8fafc !important;
    color: #0f172a !important;
}

/* Ensure all text in main content is crisp dark */
[data-testid="stMain"] p, [data-testid="stMain"] span, [data-testid="stMain"] label,
[data-testid="stMain"] h1, [data-testid="stMain"] h2, [data-testid="stMain"] h3, [data-testid="stMain"] h4,
[data-testid="stMain"] [data-testid="stMarkdownContainer"] p, [data-testid="stMain"] [data-testid="stMarkdownContainer"] span {
    color: #0f172a !important;
}

/* Tabs styling - High Contrast */
div[data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: 8px !important;
    border-bottom: 2px solid #e2e8f0 !important;
}

div[data-testid="stTabs"] button[data-baseweb="tab"] {
    color: #475569 !important;
    font-weight: 600 !important;
    font-size: 13.5px !important;
    padding: 8px 16px !important;
    background-color: transparent !important;
    border-radius: 6px 6px 0 0 !important;
}

div[data-testid="stTabs"] button[data-baseweb="tab"] p,
div[data-testid="stTabs"] button[data-baseweb="tab"] span,
div[data-testid="stTabs"] button[data-baseweb="tab"] div {
    color: #475569 !important;
    font-weight: 600 !important;
}

div[data-testid="stTabs"] button[data-baseweb="tab"]:hover p,
div[data-testid="stTabs"] button[data-baseweb="tab"]:hover span {
    color: #0f172a !important;
}

div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] {
    color: #2563eb !important;
    border-bottom-color: #2563eb !important;
}

div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] p,
div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] span {
    color: #2563eb !important;
    font-weight: 700 !important;
}

/* Streamlit Expander Styling - Clean White Cards with Crisp Dark Text */
div[data-testid="stExpander"] {
    background-color: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 10px !important;
    margin-bottom: 12px !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
}

div[data-testid="stExpander"] details {
    background-color: #ffffff !important;
    border-radius: 10px !important;
}

div[data-testid="stExpander"] summary {
    color: #0f172a !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    padding: 12px 16px !important;
    background-color: #ffffff !important;
    border-radius: 10px !important;
    transition: background-color 0.15s ease !important;
}

div[data-testid="stExpander"] summary:hover {
    background-color: #f1f5f9 !important;
    color: #1e40af !important;
}

div[data-testid="stExpander"] summary p,
div[data-testid="stExpander"] summary span,
div[data-testid="stExpander"] summary div {
    color: #0f172a !important;
    font-weight: 600 !important;
}

div[data-testid="stExpander"] summary svg {
    fill: #475569 !important;
    stroke: #475569 !important;
}

div[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
    padding: 16px 20px !important;
    border-top: 1px solid #f1f5f9 !important;
    background-color: #ffffff !important;
}

div[data-testid="stExpander"] [data-testid="stExpanderDetails"] * {
    color: #334155 !important;
}

div[data-testid="stExpander"] [data-testid="stExpanderDetails"] strong,
div[data-testid="stExpander"] [data-testid="stExpanderDetails"] b {
    color: #0f172a !important;
}

div[data-testid="stExpander"] [data-testid="stExpanderDetails"] code {
    background-color: #f1f5f9 !important;
    color: #2563eb !important;
    padding: 2px 6px !important;
    border-radius: 4px !important;
    border: 1px solid #e2e8f0 !important;
    font-family: monospace !important;
}

/* Widget Labels & Captions in Main */
[data-testid="stMain"] [data-testid="stWidgetLabel"] label,
[data-testid="stMain"] [data-testid="stWidgetLabel"] p {
    color: #1e293b !important;
    font-weight: 600 !important;
}

[data-testid="stMain"] .stCaption, [data-testid="stMain"] [data-testid="stCaptionContainer"] {
    color: #64748b !important;
}

/* Clean up Streamlit header, footer, & deploy button */
#MainMenu {visibility: hidden !important;}
footer {visibility: hidden !important;}
.stDeployButton, [data-testid="stDeployButton"], [data-testid="stStatusWidget"], [data-testid="stToolbar"] {
    display: none !important;
    visibility: hidden !important;
}
header[data-testid="stHeader"] {
    background: transparent !important;
}

/* Ensure the sidebar open/close toggle button is always visible and accessible */
[data-testid="collapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    background-color: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 8px !important;
    color: #0f172a !important;
    top: 12px !important;
    left: 12px !important;
    z-index: 99999 !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08) !important;
}

[data-testid="collapsedControl"] svg {
    fill: #0f172a !important;
    stroke: #0f172a !important;
}

/* Sidebar Styling: Deep Navy Enterprise Fintech */
section[data-testid="stSidebar"],
[data-testid="stSidebar"] {
    background-color: #0f172a !important;
    border-right: 1px solid #1e293b !important;
}

section[data-testid="stSidebar"] * {
    color: #e2e8f0;
}

/* Sidebar Navigation Header Label */
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"],
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] label,
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] span {
    color: #94a3b8 !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}

/* Sidebar Radio Options */
section[data-testid="stSidebar"] div[data-testid="stRadio"] label {
    font-size: 13.5px !important;
    font-weight: 500 !important;
    padding: 8px 12px !important;
    border-radius: 8px !important;
    margin-bottom: 2px !important;
    transition: all 0.15s ease-in-out !important;
    background-color: transparent !important;
    display: flex !important;
    align-items: center !important;
}

section[data-testid="stSidebar"] div[data-testid="stRadio"] label p,
section[data-testid="stSidebar"] div[data-testid="stRadio"] label span,
section[data-testid="stSidebar"] div[data-testid="stRadio"] label div,
section[data-testid="stSidebar"] div[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p,
section[data-testid="stSidebar"] div[data-testid="stRadio"] [data-testid="stMarkdownContainer"] span {
    color: #cbd5e1 !important;
    font-weight: 500 !important;
    font-size: 13.5px !important;
}

section[data-testid="stSidebar"] div[data-testid="stRadio"] label:hover {
    background-color: #1e293b !important;
}

section[data-testid="stSidebar"] div[data-testid="stRadio"] label:hover p,
section[data-testid="stSidebar"] div[data-testid="stRadio"] label:hover span {
    color: #ffffff !important;
}

/* Selected Radio Item in Sidebar */
section[data-testid="stSidebar"] div[data-testid="stRadio"] div[aria-checked="true"] label,
section[data-testid="stSidebar"] div[data-testid="stRadio"] label[data-checked="true"] {
    background-color: #1e293b !important;
    border-left: 3px solid #38bdf8 !important;
}

section[data-testid="stSidebar"] div[data-testid="stRadio"] div[aria-checked="true"] label p,
section[data-testid="stSidebar"] div[data-testid="stRadio"] label[data-checked="true"] p,
section[data-testid="stSidebar"] div[data-testid="stRadio"] div[aria-checked="true"] label span,
section[data-testid="stSidebar"] div[data-testid="stRadio"] label[data-checked="true"] span {
    color: #38bdf8 !important;
    font-weight: 600 !important;
}

/* Modern Header Bar */
.sn-header-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 12px 20px;
    margin-bottom: 24px;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.04);
}

.sn-brand-title {
    font-size: 18px;
    font-weight: 700;
    color: #0f172a;
    display: flex;
    align-items: center;
    gap: 8px;
}

.sn-brand-badge {
    font-size: 11px;
    font-weight: 600;
    background: #eff6ff;
    color: #2563eb;
    padding: 2px 8px;
    border-radius: 9999px;
    border: 1px solid #bfdbfe;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.sn-header-subtitle {
    font-size: 12px;
    color: #64748b;
    margin-top: 2px;
}

.sn-header-meta {
    display: flex;
    align-items: center;
    gap: 12px;
}

.sn-meta-chip {
    font-size: 12px;
    font-weight: 500;
    padding: 6px 12px;
    border-radius: 8px;
    background: #f1f5f9;
    color: #334155;
    border: 1px solid #e2e8f0;
    display: flex;
    align-items: center;
    gap: 6px;
}

.sn-status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: #10b981;
    display: inline-block;
}

/* KPI Card Grid */
.sn-kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 24px;
}

.sn-kpi-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 18px 20px;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.03);
    position: relative;
    overflow: hidden;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.sn-kpi-card:hover {
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.06);
}

.sn-kpi-blue { border-left: 4px solid #2563eb; }
.sn-kpi-green { border-left: 4px solid #10b981; }
.sn-kpi-purple { border-left: 4px solid #6366f1; }
.sn-kpi-amber { border-left: 4px solid #f59e0b; }

.sn-kpi-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
}

.sn-kpi-title {
    font-size: 11px;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

.sn-kpi-value-row {
    display: flex;
    align-items: baseline;
    gap: 8px;
    margin-bottom: 6px;
}

.sn-kpi-value {
    font-size: 28px;
    font-weight: 700;
    color: #0f172a;
    line-height: 1.1;
}

.sn-kpi-subvalue {
    font-size: 13px;
    font-weight: 500;
    color: #64748b;
}

.sn-kpi-desc {
    font-size: 11.5px;
    color: #94a3b8;
    line-height: 1.4;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* Card Containers */
.sn-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.03);
}

.sn-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid #f1f5f9;
}

.sn-card-title {
    font-size: 15px;
    font-weight: 700;
    color: #0f172a;
}

.sn-card-subtitle {
    font-size: 12px;
    color: #64748b;
}

/* Status Badges */
.sn-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 11.5px;
    font-weight: 600;
    padding: 3px 9px;
    border-radius: 6px;
    line-height: 1.3;
}

.sn-badge-success {
    background-color: #ecfdf5;
    color: #065f46;
    border: 1px solid #a7f3d0;
}

.sn-badge-warning {
    background-color: #fffbeb;
    color: #92400e;
    border: 1px solid #fde68a;
}

.sn-badge-danger {
    background-color: #fff1f2;
    color: #9f1239;
    border: 1px solid #fecdd3;
}

.sn-badge-primary {
    background-color: #eff6ff;
    color: #1e40af;
    border: 1px solid #bfdbfe;
}

.sn-badge-purple {
    background-color: #f5f3ff;
    color: #5b21b6;
    border: 1px solid #ddd6fe;
}

.sn-badge-neutral {
    background-color: #f1f5f9;
    color: #334155;
    border: 1px solid #cbd5e1;
}

/* Sidebar Contract Card */
.sn-sidebar-card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 12px;
    margin-top: 24px;
    font-size: 11px;
    color: #94a3b8;
    line-height: 1.5;
}

.sn-sidebar-card-title {
    font-weight: 700;
    color: #e2e8f0;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 6px;
}

.sn-sidebar-card code, section[data-testid="stSidebar"] code {
    background-color: #0f172a !important;
    color: #38bdf8 !important;
    padding: 2px 6px !important;
    border-radius: 4px !important;
    border: 1px solid #334155 !important;
    font-family: monospace !important;
    font-size: 11px !important;
    font-weight: 600 !important;
}


/* Timeline Turns for Conversations */
.sn-turn-container {
    margin-bottom: 12px;
    padding: 10px 14px;
    border-radius: 8px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
}

.sn-turn-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 4px;
}

.sn-turn-speaker {
    font-size: 12px;
    font-weight: 700;
    color: #1e293b;
}

.sn-turn-time {
    font-size: 11px;
    font-family: monospace;
    color: #64748b;
}

.sn-turn-text {
    font-size: 13px;
    color: #334155;
    line-height: 1.5;
}

/* Tables styling */
div[data-testid="stDataFrame"] {
    border-radius: 10px !important;
    border: 1px solid #e2e8f0 !important;
    overflow: hidden !important;
}

/* Streamlit Button System - High Contrast Modern SaaS */
div.stButton > button,
div[data-testid="stDownloadButton"] > button,
button[data-testid="baseButton-secondary"],
button[data-testid="baseButton-primary"] {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 13.5px !important;
    padding: 8px 16px !important;
    transition: all 0.15s ease-in-out !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
}

/* Secondary / Default Buttons: Clean White with Crisp Dark Text */
div.stButton > button[kind="secondary"],
div[data-testid="stDownloadButton"] > button[kind="secondary"],
div.stButton > button:not([kind="primary"]),
button[data-testid="baseButton-secondary"] {
    background-color: #ffffff !important;
    border: 1.5px solid #cbd5e1 !important;
    color: #0f172a !important;
}

div.stButton > button[kind="secondary"]:hover,
div[data-testid="stDownloadButton"] > button[kind="secondary"]:hover,
div.stButton > button:not([kind="primary"]):hover,
button[data-testid="baseButton-secondary"]:hover {
    background-color: #f1f5f9 !important;
    border-color: #94a3b8 !important;
    color: #0f172a !important;
}

div.stButton > button:not([kind="primary"]) p,
div.stButton > button:not([kind="primary"]) span,
div.stButton > button:not([kind="primary"]) div,
div.stButton > button[kind="secondary"] p,
div.stButton > button[kind="secondary"] span,
div.stButton > button[kind="secondary"] div,
button[data-testid="baseButton-secondary"] p,
button[data-testid="baseButton-secondary"] span,
div[data-testid="stDownloadButton"] > button:not([kind="primary"]) p,
div[data-testid="stDownloadButton"] > button:not([kind="primary"]) span {
    color: #0f172a !important;
    font-weight: 600 !important;
}

/* Primary Buttons: Indigo Gradient with Crisp Pure White Text */
div.stButton > button[kind="primary"],
div[data-testid="stDownloadButton"] > button[kind="primary"],
button[data-testid="baseButton-primary"] {
    background: linear-gradient(135deg, #4f46e5 0%, #2563eb 100%) !important;
    border: 1px solid #3730a3 !important;
    color: #ffffff !important;
    box-shadow: 0 1px 3px rgba(79, 70, 229, 0.3) !important;
}

div.stButton > button[kind="primary"]:hover,
div[data-testid="stDownloadButton"] > button[kind="primary"]:hover,
button[data-testid="baseButton-primary"]:hover {
    background: linear-gradient(135deg, #4338ca 0%, #1d4ed8 100%) !important;
    border-color: #312e81 !important;
    color: #ffffff !important;
}

div.stButton > button[kind="primary"] p,
div.stButton > button[kind="primary"] span,
div.stButton > button[kind="primary"] div,
button[data-testid="baseButton-primary"] p,
button[data-testid="baseButton-primary"] span,
button[data-testid="baseButton-primary"] div {
    color: #ffffff !important;
    font-weight: 600 !important;
}
</style>
"""

def render_top_header(current_count: int = 44):
    """Render the top enterprise navigation bar."""
    html = f"""
    <div class="sn-header-bar">
        <div>
            <div class="sn-brand-title">
                <svg width="26" height="26" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect width="28" height="28" rx="7" fill="url(#th-logo-grad)"/>
                    <path d="M8 15L12 10L16 14L20 8M20 8H16M20 8V12" stroke="#ffffff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
                    <circle cx="8" cy="19" r="1.5" fill="#bae6fd"/>
                    <circle cx="14" cy="19" r="1.5" fill="#bae6fd"/>
                    <circle cx="20" cy="19" r="1.5" fill="#bae6fd"/>
                    <defs>
                        <linearGradient id="th-logo-grad" x1="0" y1="0" x2="28" y2="28" gradientUnits="userSpaceOnUse">
                            <stop stop-color="#4338ca"/>
                            <stop offset="1" stop-color="#0284c7"/>
                        </linearGradient>
                    </defs>
                </svg>
                <span>Revenue Intelligence Inbox</span>
                <span class="sn-brand-badge">Inbox</span>
            </div>
            <div class="sn-header-subtitle">Sales Manager Inbox & Analysis — Daily Operational Workspace</div>
        </div>
        <div class="sn-header-meta">
            <div class="sn-meta-chip">
                <span>📅 21 Aug 2026</span>
                <span style="color:#94a3b8">|</span>
                <span>Asia/Kolkata (UTC+05:30)</span>
            </div>
            <div class="sn-meta-chip">
                <span class="sn-status-dot"></span>
                <span><b>Supabase Cloud:</b> {current_count} records</span>
            </div>
        </div>
    </div>
    """
    return "".join(line.strip() for line in html.splitlines())

def render_kpi_cards(total_records: int, calls_count: int, meetings_count: int,
                     usable_count: int, connected_calls: int, review_count: int):
    """Render the 4 prominent KPI metric cards in a grid."""
    coverage_pct = (usable_count / total_records * 100) if total_records else 0.0
    connected_pct = (connected_calls / calls_count * 100) if calls_count else 0.0

    html = f"""
    <div class="sn-kpi-grid">
        <div class="sn-kpi-card sn-kpi-blue">
            <div class="sn-kpi-top">
                <span class="sn-kpi-title">TOTAL UNIQUE RECORDS</span>
                <div style="background:#eff6ff; width:32px; height:32px; border-radius:8px; display:flex; align-items:center; justify-content:center;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg>
                </div>
            </div>
            <div class="sn-kpi-value-row">
                <span class="sn-kpi-value">{total_records}</span>
                <span class="sn-kpi-subvalue">({calls_count} calls, {meetings_count} meetings)</span>
            </div>
            <div class="sn-kpi-desc">Distinct (source_type, source_id) in database</div>
        </div>

        <div class="sn-kpi-card sn-kpi-green">
            <div class="sn-kpi-top">
                <span class="sn-kpi-title">TRANSCRIPT COVERAGE</span>
                <div style="background:#ecfdf5; width:32px; height:32px; border-radius:8px; display:flex; align-items:center; justify-content:center;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
                </div>
            </div>
            <div class="sn-kpi-value-row">
                <span class="sn-kpi-value">{coverage_pct:.1f}%</span>
                <span class="sn-kpi-subvalue">{usable_count} / {total_records} records</span>
            </div>
            <div class="sn-kpi-desc">Conversational text available for analysis</div>
        </div>

        <div class="sn-kpi-card sn-kpi-purple">
            <div class="sn-kpi-top">
                <span class="sn-kpi-title">CALLS CONNECTED RATE</span>
                <div style="background:#f5f3ff; width:32px; height:32px; border-radius:8px; display:flex; align-items:center; justify-content:center;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6366f1" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg>
                </div>
            </div>
            <div class="sn-kpi-value-row">
                <span class="sn-kpi-value">{connected_pct:.1f}%</span>
                <span class="sn-kpi-subvalue">{connected_calls} / {calls_count} calls</span>
            </div>
            <div class="sn-kpi-desc">Calls with real buyer conversations</div>
        </div>

        <div class="sn-kpi-card sn-kpi-amber">
            <div class="sn-kpi-top">
                <span class="sn-kpi-title">RECORDS REQUIRING REVIEW</span>
                <div style="background:#fffbeb; width:32px; height:32px; border-radius:8px; display:flex; align-items:center; justify-content:center;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
                </div>
            </div>
            <div class="sn-kpi-value-row">
                <span class="sn-kpi-value">{review_count}</span>
                <span class="sn-kpi-subvalue">action items</span>
            </div>
            <div class="sn-kpi-desc">Awaiting human review or missing text</div>
        </div>
    </div>
    """
    return "".join(line.strip() for line in html.splitlines())

def render_sidebar_footer():
    """Render bottom contract rules card in the sidebar."""
    html = """
    <div class="sn-sidebar-card">
        <div class="sn-sidebar-card-title">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
            <span>Data Contract Rules</span>
        </div>
        Identity is composite <code style="background-color: #0f172a !important; color: #38bdf8 !important; padding: 2px 6px; border-radius: 4px; border: 1px solid #334155; font-family: monospace; font-size: 11px; font-weight: 600;">(source_type, source_id)</code>. Revisions overwrite payload but preserve candidate analysis and manual overrides.
        <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid #334155; font-size: 10px; color: #64748b;">
            Revenue Intelligence Inbox Revenue Intel • v2.0
        </div>
    </div>
    """
    return "".join(line.strip() for line in html.splitlines())


