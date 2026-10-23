# Revenue Intelligence Inbox

A modern enterprise SaaS dashboard for sales leaders and revenue managers. Ingests calls and Google Meet sessions, classifies them into an 8-category routing taxonomy, surfaces evidence-backed churn and revenue findings, and synchronizes live with **Supabase Cloud**.

---

## 🚀 Live Cloud Deployment (Render)

When deploying this project as a **Web Service** on **[Render](https://render.com/)**, use the following configuration:

### 1. Render Build & Start Commands

| Setting | Value |
|---|---|
| **Environment** | `Python 3` |
| **Region** | Oregon (US West) or closest to your database |
| **Branch** | `main` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true` |

### 2. Environment Variables on Render
Under the **Environment** tab in your Render dashboard, add:

| Key | Value | Purpose |
|---|---|---|
| `PYTHON_VERSION` | `3.11.9` | Ensures modern Python 3.11+ runtime |
| `SUPABASE_URL` | `https://thamyuugypckgmkqkdjz.supabase.co` | Live Supabase cloud database URL |
| `SUPABASE_KEY` | *(your Supabase anon/service key)* | Authenticates live database sync |

---

## ☁️ Streamlit Community Cloud Deployment

1. Push your repository to GitHub: `https://github.com/Aravindh-2006/volopay-revenue-inbox.git`.
2. Go to **[share.streamlit.io](https://share.streamlit.io)** and click **New App**.
3. Select your repository, branch (`main`), and main file path (`app.py`).
4. In **Advanced Settings** → **Secrets**, add your Supabase credentials:
   ```toml
   [supabase]
   url = "https://thamyuugypckgmkqkdjz.supabase.co"
   key = "your-supabase-key"
   ```
5. Click **Deploy**.

---

## 💻 Local Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the application
```bash
streamlit run app.py
```
Open **[http://localhost:8501](http://localhost:8501)** in your browser.

### 3. Run automated test suite
```bash
pytest tests.py -v
```

---

## 📁 Project Structure

```text
volopay-revenue-inbox/
├── .streamlit/
│   ├── config.toml         # Theme settings (Light SaaS theme, indigo primary)
│   └── secrets.toml        # Supabase URL & Key (protected from Git)
├── data/
│   ├── 01_initial.json     # Initial batch (44 records, revision 1)
│   └── 02_update.json      # Update batch (M07 transcript update, revision 2)
├── app.py                  # Main Streamlit web application
├── db.py                   # SQLite + Supabase cloud synchronization layer
├── routing.py              # Rule-based 8-category routing classification
├── findings.py             # Evidence-backed findings & manager brief generator
├── exports.py              # Manifest generation and ZIP archive exporter
├── styles.py               # Enterprise SaaS design system, CSS & widgets
├── tests.py                # 19 automated pytest tests
├── requirements.txt        # Production dependencies (streamlit, supabase, plotly, pandas)
└── README.md               # Project documentation
```

---

## ⚙️ Architecture & Features

### Dual Database Backend (SQLite + Supabase Cloud)
- **Primary / Cloud**: Live sync to **Supabase PostgreSQL** (`source_records`, `automated_routes`, `manual_overrides`, `import_log`).
- **Local Fallback**: Embedded SQLite (`inbox.db`) with Write-Ahead Logging (WAL) for offline testing and local demo execution.
- **Composite Key**: Records use `(source_type, source_id)` to prevent collisions between calls and meetings.

### Routing Taxonomy (8 Categories)
1. **New Prospect Outreach** — Cold outreach to potential customers
2. **Follow-Up / Nurture** — Continued conversation with interested leads
3. **Partnership / Channel** — Referral partnerships and channel arrangements
4. **Existing Customer Management** — Support, onboarding, migration for current customers
5. **Vendor / Supplier Evaluation** — Evaluating external vendors/suppliers
6. **Internal / Training** — Internal operational meetings and training sessions
7. **No Conversation** — Voicemails, unresponsive attempts, very short calls
8. **Unclassified** — Insufficient information; flagged for human manager triage

### Human-in-the-Loop Override Persistence
- Automated route suggestions are generated with explanatory reasons.
- Managers can override classifications from the **Routing & Review** triage queue.
- Overrides persist across batch re-imports, newer revision updates, and app restarts.

### Evidence-Backed Findings
1. **Harborpath Advisory (M01)**: Active partnership and commercial referral negotiations.
2. **Cedarwave Distribution (M04)**: High churn risk regarding prepaid card migration.
3. **Outbound Campaign Efficiency (B01–B20)**: Low connect rate analysis across cold outreach calls.

---

## 🧪 Replay Verification Steps

1. Open the **Import & Replay Controls** page.
2. Click **Ingest 01_initial.json** → inserts all 44 records.
3. Click **Ingest 01_initial.json** again → 0 inserted, 44 skipped (tests deduplication).
4. Go to **Routing & Review** → apply an override to any record.
5. Ingest **02_update.json** → updates M07 to revision 2, marks it `stale` for re-analysis, and preserves your manual override.
6. Go to **Exports & Downloads** → download the complete ZIP bundle and verify `manifest.json`.
