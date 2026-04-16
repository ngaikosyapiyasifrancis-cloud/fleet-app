# app.py — SparklingBlu Moto | Weekly Driver Performance Tracker
# Views: admin | drivers | fleet | team

import streamlit as st
import pandas as pd
import json
from datetime import datetime
from engine import (
    calculate_performance_score, get_coaching_message,
    get_week_progress, get_remaining_targets,
    kpi_fully_met, WEEKLY_TARGETS,
)
from teams import TEAMS, SBV_DRIVERS, match_drivers_to_teams, mark_sbv_drivers
from storage import save_fleet_data, load_fleet_data, is_storage_configured

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="SparklingBlu — Driver Performance",
                   page_icon="🚛", layout="wide")

st.markdown("""
<style>
[data-testid="stAppViewContainer"],[data-testid="stMain"],.main{background:#f0f4f8!important;}
[data-testid="stAppViewContainer"] p,[data-testid="stAppViewContainer"] span,
[data-testid="stAppViewContainer"] div,[data-testid="stAppViewContainer"] label,
[data-testid="stMarkdownContainer"] p,[data-testid="stMarkdownContainer"] span,
[data-testid="stMarkdownContainer"] li{color:#0f2027!important;}
h1,h2,h3{color:#0f2027!important;}
[data-testid="stMetric"]{background:white!important;border-radius:14px!important;
  padding:18px 22px!important;text-align:center!important;
  box-shadow:0 2px 10px rgba(0,0,0,.10)!important;}
[data-testid="stMetricLabel"]>div{font-size:12px!important;font-weight:800!important;
  color:#203a43!important;text-transform:uppercase!important;letter-spacing:.6px!important;}
[data-testid="stMetricValue"]>div{font-size:32px!important;font-weight:900!important;
  color:#0f2027!important;}
[data-testid="stAlert"] p,[data-testid="stAlert"] span{color:#0f2027!important;}
[data-testid="stTextInput"] input{background:white!important;color:#0f2027!important;
  border:1.5px solid #2c5364!important;border-radius:8px!important;}
[data-testid="stTextInput"] label,[data-testid="stNumberInput"] label,
[data-testid="stSelectbox"] label,[data-testid="stFileUploader"] label{
  color:#0f2027!important;font-weight:600!important;}
[data-testid="stCaptionContainer"] p{color:#555!important;font-size:13px!important;}
[data-testid="stDataFrame"]{background:white!important;border-radius:10px!important;}
[data-testid="stExpander"] summary p{color:#0f2027!important;font-weight:600!important;}
</style>
""", unsafe_allow_html=True)

# ── CONSTANTS ─────────────────────────────────────────────────────────────────
BASE_URL   = "https://fleet-app-v25cphks3psbb94zeedjfq.streamlit.app"
SBV_TOTAL  = len(SBV_DRIVERS)

# ── HELPERS ───────────────────────────────────────────────────────────────────
def fmt_rate(v):
    try:    return f"{round(float(v)*100)}%"
    except: return str(v)

def fmt_bool(v):
    if v in [True,1,"True","YES"]: return "YES"
    if v in [False,0,"False","NO"]: return "NO"
    return str(v)

def date_only():
    return datetime.now().strftime("%d %b %Y")

def make_link(view, team=None):
    if team:
        return f"{BASE_URL}/?view={view}&team={team.replace(' ','+')}"
    return f"{BASE_URL}/?view={view}"

def banner_html(text):
    return (
        f'<div style="background:linear-gradient(90deg,#0f2027,#203a43,#2c5364);'
        f'color:white;padding:14px 22px;border-radius:12px;margin-bottom:18px;font-size:14px;">'
        f'{text}</div>'
    )

def sbv_bar_html(line1, line2=""):
    return (
        f'<div style="background:white;border-radius:12px;padding:16px 22px;'
        f'border-left:5px solid #2c5364;margin-bottom:16px;color:#0f2027;">'
        f'{line1}'
        + (f'<br><span style="color:#0f2027;font-size:13px;">{line2}</span>' if line2 else "")
        + '</div>'
    )

def insight_html(text):
    return (
        f'<div style="background:white;border-radius:12px;padding:14px 18px;'
        f'box-shadow:0 2px 8px rgba(0,0,0,.07);margin-bottom:10px;'
        f'font-size:15px;color:#0f2027;">{text}</div>'
    )

def link_html(url):
    return (
        f'<div style="background:#0f2027;border-left:5px solid #25D366;'
        f'border-radius:8px;padding:12px 16px;font-family:monospace;'
        f'font-size:13px;word-break:break-all;color:#25D366;'
        f'margin-top:6px;display:block;letter-spacing:0.3px;">{url}</div>'
    )

# ── PROCESS CSV ───────────────────────────────────────────────────────────────
def process_dataframe(raw, report_days, week_info):
    scores, statuses, coachings = [], [], []
    hrs_needed, trps_needed     = [], []
    ar_ok, cr_ok, hrs_ok, trps_ok = [], [], [], []
    hrs_weekly, trps_weekly     = [], []
    kpi_met_list                = []

    for _, row in raw.iterrows():
        rem = get_remaining_targets(
            row["Hours Online"], row["Trips Taken"],
            row["Confirmation Rate"], row["Cancellation Rate"],
            week_info["progress"], report_days
        )
        score = calculate_performance_score(
            row["Confirmation Rate"], row["Cancellation Rate"],
            row["Hours Online"], row["Trips Taken"], report_days
        )
        status, coaching = get_coaching_message(score, rem, week_info)
        kpi = kpi_fully_met(
            row["Hours Online"], row["Trips Taken"],
            row["Confirmation Rate"], row["Cancellation Rate"], report_days
        )
        scores.append(score);    statuses.append(status);   coachings.append(coaching)
        hrs_needed.append(rem["hours_needed"]); trps_needed.append(rem["trips_needed"])
        ar_ok.append(rem["ar_on_track"]);       cr_ok.append(rem["cr_on_track"])
        hrs_ok.append(rem["hours_on_track"]);   trps_ok.append(rem["trips_on_track"])
        hrs_weekly.append(rem["hours_weekly"]); trps_weekly.append(rem["trips_weekly"])
        kpi_met_list.append(kpi)

    df = raw.copy()
    df["Score"]                = scores
    df["Status"]               = statuses
    df["Coaching"]             = coachings
    df["Hours Needed"]         = hrs_needed
    df["Trips Needed"]         = trps_needed
    df["AR On Track"]          = ar_ok
    df["CR On Track"]          = cr_ok
    df["Hours On Track"]       = hrs_ok
    df["Trips On Track"]       = trps_ok
    df["Hours Online (weekly)"]= hrs_weekly
    df["Trips (weekly)"]       = trps_weekly
    df["KPI Met"]              = kpi_met_list
    return df

# ── ROUTE ─────────────────────────────────────────────────────────────────────
params     = st.query_params
view       = params.get("view", "admin")
team_param = params.get("team", None)
week_info  = get_week_progress()


# ════════════════════════════════════════════════════════
# ADMIN VIEW
# ════════════════════════════════════════════════════════
if view == "admin":
    st.markdown("# 🚛 SparklingBlu — Admin Panel")
    st.caption("Upload CSV → process → publish links")

    if not is_storage_configured():
        st.warning("⚙️ One-time GitHub Gist setup needed. See Setup Guide below.")

    st.markdown(banner_html(
        f'Today: <strong style="color:white;">{week_info["day_name"]}, {date_only()}</strong>'
        f' &nbsp;|&nbsp; Week: <strong style="color:white;">{round(week_info["progress"]*100,1)}%</strong> complete'
        f' &nbsp;|&nbsp; <strong style="color:white;">{week_info["days_left"]} day(s)</strong> left'
        f' &nbsp;|&nbsp; Shift: <strong style="color:white;">5:00am – 7:30pm</strong>'
        f' &nbsp;|&nbsp; Targets: <strong style="color:white;">10h/day | 5 trips/day | 80% AR | 5% CR | 50h/week</strong>'
    ), unsafe_allow_html=True)

    col_a, col_b = st.columns([3, 1])
    with col_a:
        uploaded = st.file_uploader("Upload Uber CSV", type=["csv"])
        sbv_file = st.file_uploader(
            "Update SBV Driver List (optional — upload new Vehicle_List.xlsx)",
            type=["xlsx"]
        )
    with col_b:
        report_days = st.number_input(
            "Days this CSV covers", min_value=1, max_value=7, value=1,
            help="e.g. Mon–Thu = 4"
        )
        week_label = st.text_input("Week label", value=date_only())

    # SBV list override from Excel
    if sbv_file is not None:
        try:
            sbv_xl = pd.read_excel(sbv_file)
            if "Driver" in sbv_xl.columns:
                st.session_state["sbv_override"] = sbv_xl["Driver"].dropna().str.strip().tolist()
                st.success(f"SBV list updated: {len(st.session_state['sbv_override'])} drivers loaded.")
            else:
                st.warning("Excel must have a 'Driver' column.")
        except Exception as e:
            st.error(f"Could not read Excel: {e}")

    if uploaded is None:
        st.info("Upload your Uber driver CSV file to get started.")
        st.stop()

    # ── Load & process ────────────────────────────────────
    raw = pd.read_csv(uploaded)
    raw["Driver"] = raw["Driver first name"] + " " + raw["Driver surname"]
    raw = match_drivers_to_teams(raw)

    if "sbv_override" in st.session_state:
        from teams import is_sbv_driver_dynamic
        override = st.session_state["sbv_override"]
        raw["Is SBV"] = raw["Driver"].apply(lambda n: is_sbv_driver_dynamic(n, override))
        active_sbv_list = override
    else:
        raw = mark_sbv_drivers(raw)
        active_sbv_list = SBV_DRIVERS

    df = process_dataframe(raw, report_days, week_info)

    # ── SBV counts — derived ONLY from CSV ───────────────
    sbv_df      = df[df["Is SBV"] == True]
    sbv_in_csv  = len(sbv_df)
    sbv_kpi     = int(sbv_df["KPI Met"].apply(lambda x: x in [True,1,"True","YES"]).sum())
    sbv_pct     = round((sbv_kpi / sbv_in_csv) * 100) if sbv_in_csv else 0

    st.markdown(sbv_bar_html(
        f'🚛 <strong style="color:#0f2027;">SBV Drivers in this report:</strong>'
        f' <span style="font-size:22px;font-weight:900;color:#0f2027;">'
        f'&nbsp;{sbv_in_csv} / {SBV_TOTAL}</span>'
        f'&nbsp;&nbsp;|&nbsp;&nbsp;'
        f'<span style="color:#0f2027;">SBV KPI Compliant: <strong>{sbv_kpi} / {sbv_in_csv}</strong>'
        f'&nbsp;&nbsp;|&nbsp;&nbsp;SBV Compliance Rate: <strong>{sbv_pct}%</strong></span>'
    ), unsafe_allow_html=True)

    # ── Fleet overview metrics ────────────────────────────
    st.subheader("Fleet Overview")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Drivers",          len(df))
    c2.metric("Top Performers",         len(df[df["Score"] >= 85]))
    c3.metric("Needs Attention",        len(df[(df["Score"] >= 50) & (df["Score"] < 70)]))
    c4.metric("Needs Urgent Attention", len(df[df["Score"] < 50]))

    st.divider()

    # ── SBV Exploration expanders ─────────────────────────
    # A: SBV drivers NOT in CSV
    csv_names_lower = set(df["Driver"].str.strip().str.lower().tolist())
    missing_from_csv = []
    for sbv_name in active_sbv_list:
        sbv_lower = sbv_name.strip().lower()
        parts = sbv_lower.split()
        found = False
        for csv_name in csv_names_lower:
            if len(parts) >= 2 and parts[0] in csv_name and parts[-1] in csv_name:
                found = True; break
            if sbv_lower in csv_name or csv_name in sbv_lower:
                found = True; break
        if not found:
            missing_from_csv.append(sbv_name)

    with st.expander(f"🔴 SBV Drivers NOT ONLINE this period ({len(missing_from_csv)} drivers)"):
        if missing_from_csv:
            miss_df = pd.DataFrame({"Driver": sorted(missing_from_csv)})
            miss_df.index += 1
            st.dataframe(miss_df, use_container_width=True)
        else:
            st.success("All SBV drivers appeared in the CSV.")

    # B: SBV drivers in CSV but not assigned to a team
    unassigned_sbv = df[(df["Is SBV"] == True) & (df["Team"] == "Unassigned")]
    with st.expander(f"🟡 SBV Drivers NOT assigned to any team ({len(unassigned_sbv)} drivers)"):
        if not unassigned_sbv.empty:
            ua_df = unassigned_sbv[["Driver","Hours Online (weekly)","Trips (weekly)",
                                     "Confirmation Rate","Cancellation Rate","Score","Status"]].copy()
            ua_df["Confirmation Rate"] = ua_df["Confirmation Rate"].apply(fmt_rate)
            ua_df["Cancellation Rate"] = ua_df["Cancellation Rate"].apply(fmt_rate)
            st.dataframe(ua_df.sort_values("Score", ascending=False),
                         use_container_width=True, hide_index=True)
        else:
            st.success("All SBV drivers in the CSV are assigned to a team.")

    st.divider()

    # ── Preview table ─────────────────────────────────────
    with st.expander("Preview Full Driver Table"):
        prev = df[["Driver","Team","Is SBV","Hours Online (weekly)","Trips (weekly)",
                   "Confirmation Rate","Cancellation Rate","Score","Status","KPI Met"]].copy()
        prev["Confirmation Rate"] = prev["Confirmation Rate"].apply(fmt_rate)
        prev["Cancellation Rate"] = prev["Cancellation Rate"].apply(fmt_rate)
        prev["KPI Met"]           = prev["KPI Met"].apply(fmt_bool)
        st.dataframe(prev.sort_values("Score", ascending=False),
                     use_container_width=True, hide_index=True)

    st.divider()

    # ── Save & publish ────────────────────────────────────
    encode_cols = [
        "Driver","Team","Is SBV",
        "Hours Online (weekly)","Trips (weekly)",
        "Confirmation Rate","Cancellation Rate",
        "Score","Status","Coaching",
        "Hours Needed","Trips Needed",
        "AR On Track","CR On Track","Hours On Track","Trips On Track","KPI Met"
    ]
    payload = {
        "fleet":        df[encode_cols].to_dict(orient="records"),
        "week_info":    week_info,
        "week_label":   week_label,
        "report_days":  int(report_days),
        "updated_at":   date_only(),
        "sbv_in_csv":   sbv_in_csv,
        "sbv_total":    SBV_TOTAL,
        "sbv_kpi":      sbv_kpi,
        "missing_sbv":  missing_from_csv,
    }

    st.subheader("Publish & Share Links")

    if is_storage_configured():
        if st.button("📤 Publish Data & Update All Links", type="primary",
                     use_container_width=True):
            with st.spinner("Saving to GitHub Gist..."):
                ok = save_fleet_data(payload)
            if ok:
                st.success("✅ Data published! All links now show the latest data.")
            else:
                st.error("Failed. Check GITHUB_TOKEN and GIST_ID in Streamlit Secrets.")
    else:
        st.info("Complete the one-time setup below to enable auto-updating links.")

    st.divider()

    # ── Display links ─────────────────────────────────────
    st.markdown("#### Your Permanent Links")
    st.caption("These never change. Drivers bookmark once — they always see the latest data.")

    l1, l2 = st.columns(2)
    with l1:
        st.markdown("**📱 Drivers Link** — share in your whole driver group")
        st.markdown(link_html(make_link("drivers")), unsafe_allow_html=True)
    with l2:
        st.markdown("**📊 Management Link** — share with management")
        st.markdown(link_html(make_link("fleet")), unsafe_allow_html=True)

    st.markdown("**👥 Team Links** — share each in the team's WhatsApp group")
    t_cols = st.columns(len(TEAMS))
    for i, (team_name, info) in enumerate(TEAMS.items()):
        with t_cols[i]:
            st.markdown(f"**{team_name}**")
            st.caption(f"Leader: {info['leader']}")
            st.markdown(link_html(make_link("team", team_name)), unsafe_allow_html=True)

    st.divider()

    with st.expander("⚙️ One-Time Setup Guide (5 minutes)"):
        st.markdown("""
**Step 1 — Get a GitHub Token**
1. Go to 👉 https://github.com/settings/tokens
2. Click **Generate new token (classic)**
3. Name: `fleet-app` | Tick: `gist` only | Click **Generate token**
4. Copy the token immediately

**Step 2 — Create a Gist**
1. Go to 👉 https://gist.github.com
2. Filename: `fleet_data.json` | Content: `{}` | Click **Create secret gist**
3. Copy the ID from the URL (the long string after your username)

**Step 3 — Add to Streamlit Secrets**
1. Go to https://share.streamlit.io → your app → Settings → Secrets
2. Paste:
```toml
GITHUB_TOKEN = "ghp_yourTokenHere"
GIST_ID      = "yourGistIdHere"
```
3. Click Save
        """)


# ════════════════════════════════════════════════════════
# DRIVERS VIEW
# ════════════════════════════════════════════════════════
elif view == "drivers":
    data = load_fleet_data()
    st.markdown("# 🚛 SparklingBlu Moto — Your Weekly Stats")

    if not data:
        st.warning("Stats not available yet. Ask your fleet manager to publish this week's data.")
        st.stop()

    df      = pd.DataFrame(data["fleet"])
    wi      = data.get("week_info", week_info)
    updated = data.get("updated_at", "")

    st.markdown(
        f"*{wi.get('day_name','—')} check-in  |  "
        f"{wi.get('days_left','—')} day(s) left  |  Updated: {updated}*"
    )
    st.divider()

    search = st.text_input("Type your name:", placeholder="e.g. John Msosa")
    if not search:
        st.info("Start typing your name above to see your stats.")
        st.stop()

    matches = df[df["Driver"].str.lower().str.contains(search.strip().lower(), na=False)]
    if matches.empty:
        st.warning("No driver found. Try a different spelling.")
        st.stop()
    if len(matches) > 1:
        choice  = st.selectbox("Multiple matches — select your name:", matches["Driver"].tolist())
        matches = matches[matches["Driver"] == choice]

    row   = matches.iloc[0]
    score = float(row["Score"])
    score_color = ("#0a8a4e" if score >= 85 else
                   "#2980b9" if score >= 70 else
                   "#e67e22" if score >= 50 else "#c0392b")
    status_emoji = ("🌟" if row["Status"] == "Top Performer" else
                    "✅" if row["Status"] == "Good" else
                    "⚠️" if row["Status"] == "Needs Improvement" else "🚨")

    st.markdown(f"""
    <div style="background:white;border-radius:16px;padding:28px 32px;
                box-shadow:0 4px 20px rgba(0,0,0,.10);margin-bottom:18px;">
        <h2 style="margin:0 0 4px 0;color:#0f2027;">👤 {row['Driver']}</h2>
        <p style="color:#555;margin:0 0 20px 0;font-size:15px;">Team: {row.get('Team','—')}</p>
        <h1 style="font-size:64px;margin:0;color:{score_color};font-weight:900;">{score}</h1>
        <p style="font-size:20px;margin:6px 0 0 0;color:#0f2027;">
            {status_emoji} <strong>{row['Status']}</strong></p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Your KPIs This Week")
    k1, k2, k3, k4 = st.columns(4)

    def kpi_tile(col, label, value, target, on_track):
        col.metric(f"{'✅' if on_track else '❌'} {label}", value, target)

    kpi_tile(k1, "Hours Online (weekly)",
             f"{row.get('Hours Online (weekly)',row.get('hours_weekly','—'))}h",
             "Target: 10h/day", bool(row.get("Hours On Track", False)))
    kpi_tile(k2, "Trips (weekly)",
             str(row.get("Trips (weekly)", row.get("trips_weekly","—"))),
             "Target: 5 trips/day", bool(row.get("Trips On Track", False)))
    kpi_tile(k3, "Acceptance Rate",
             fmt_rate(row["Confirmation Rate"]), "Target: 80%+",
             bool(row.get("AR On Track", False)))
    kpi_tile(k4, "Cancellation Rate",
             fmt_rate(row["Cancellation Rate"]), "Target: max 5%",
             bool(row.get("CR On Track", False)))

    st.divider()
    st.markdown("### What You Still Need By Sunday")
    n1, n2 = st.columns(2)
    hrs_left  = float(row.get("Hours Needed", 0))
    trps_left = int(float(row.get("Trips Needed", 0)))

    (n1.error if hrs_left > 0 else n1.success)(
        f"⏱️ {'Still need ' + str(hrs_left) + 'h more this week' if hrs_left > 0 else 'Weekly hours target met!'}")
    (n2.error if trps_left > 0 else n2.success)(
        f"🚗 {'Still need ' + str(trps_left) + ' more trips this week' if trps_left > 0 else 'Weekly trips target met!'}")

    ar_ok = row.get("AR On Track", False) in [True, 1, "True"]
    cr_ok = row.get("CR On Track", False) in [True, 1, "True"]
    (st.success if ar_ok else st.error)(
        "📈 Acceptance rate on track!" if ar_ok else "📉 Acceptance rate below 80% — keep accepting trips!")
    (st.success if cr_ok else st.error)(
        "✅ Cancellation rate on track!" if cr_ok else "⚠️ Cancellation rate above 5% — reduce cancellations!")

    st.divider()
    st.markdown("### Coaching Message")
    st.info(str(row.get("Coaching", "")))
    st.caption(f"SparklingBlu Moto Fleet Team 🚛  |  Updated: {updated}")


# ════════════════════════════════════════════════════════
# FLEET / MANAGEMENT VIEW
# ════════════════════════════════════════════════════════
elif view == "fleet":
    data = load_fleet_data()
    st.markdown("# 📊 SparklingBlu Moto — Fleet Performance")

    if not data:
        st.warning("No data available. Ask the fleet manager to publish this week's stats.")
        st.stop()

    df          = pd.DataFrame(data["fleet"])
    wi          = data.get("week_info", week_info)
    updated     = data.get("updated_at", "")
    sbv_in      = data.get("sbv_in_csv", 0)
    sbv_tot     = data.get("sbv_total", SBV_TOTAL)
    sbv_kpi_n   = data.get("sbv_kpi", 0)
    sbv_pct     = round((sbv_kpi_n / sbv_in) * 100) if sbv_in else 0
    missing_sbv = data.get("missing_sbv", [])

    st.markdown(
        f"*Management Overview  |  {wi.get('day_name','—')}  |  "
        f"{wi.get('days_left','—')} day(s) left  |  Updated: {updated}*"
    )

    st.markdown(sbv_bar_html(
        f'🚛 <strong style="color:#0f2027;">SBV Drivers in report:</strong>'
        f' <span style="font-size:22px;font-weight:900;color:#0f2027;">'
        f'&nbsp;{sbv_in} / {sbv_tot}</span>'
        f'&nbsp;&nbsp;|&nbsp;&nbsp;'
        f'<span style="color:#0f2027;">SBV KPI Compliant: <strong>{sbv_kpi_n}/{sbv_in}</strong>'
        f'&nbsp;|&nbsp;SBV Compliance Rate: <strong>{sbv_pct}%</strong></span>'
    ), unsafe_allow_html=True)

    df["Score"] = df["Score"].astype(float)
    total       = len(df)
    top         = len(df[df["Score"] >= 85])
    attention   = len(df[(df["Score"] >= 50) & (df["Score"] < 70)])
    urgent      = len(df[df["Score"] < 50])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Drivers",          total)
    c2.metric("Top Performers",         top)
    c3.metric("Needs Attention",        attention)
    c4.metric("Needs Urgent Attention", urgent)

    st.divider()

    # Key Insights
    st.markdown("### Key Insights")
    i1, i2 = st.columns(2)
    top_driver = df.loc[df["Score"].idxmax(), "Driver"]

    with i1:
        st.markdown(insight_html(f"🏆 <strong>Best Driver:</strong> {top_driver} — score {df['Score'].max()}"), unsafe_allow_html=True)
        low_ar = (df["Confirmation Rate"].astype(float) < 0.80).sum()
        st.markdown(insight_html(f"📉 <strong>{low_ar} driver(s)</strong> below 80% acceptance rate"), unsafe_allow_html=True)
        high_cr = (df["Cancellation Rate"].astype(float) > 0.05).sum()
        st.markdown(insight_html(f"⚠️ <strong>{high_cr} driver(s)</strong> above 5% cancellation rate"), unsafe_allow_html=True)
    with i2:
        col_h = "Hours Online (weekly)"
        col_t = "Trips (weekly)"
        low_hrs  = (df[col_h].astype(float) < 10).sum() if col_h in df.columns else "—"
        low_trps = (df[col_t].astype(float) < 5).sum()  if col_t in df.columns else "—"
        st.markdown(insight_html(f"⏱️ <strong>{low_hrs} driver(s)</strong> with fewer than 10h online"), unsafe_allow_html=True)
        st.markdown(insight_html(f"🚗 <strong>{low_trps} driver(s)</strong> with fewer than 5 trips"), unsafe_allow_html=True)
        compliant = int(df["KPI Met"].apply(lambda x: x in [True,1,"True","YES"]).sum())
        fleet_pct = round((compliant/total)*100) if total else 0
        st.markdown(insight_html(f"✅ <strong>{compliant}/{total}</strong> drivers fully KPI compliant ({fleet_pct}%)"), unsafe_allow_html=True)

    st.divider()

    # Team compliance
    st.markdown("### Team Compliance")
    t_cols = st.columns(len(TEAMS))
    for i, (tn, info) in enumerate(TEAMS.items()):
        t_df   = df[df["Team"] == tn]
        t_n    = len(t_df)
        t_comp = int(t_df["KPI Met"].apply(lambda x: x in [True,1,"True","YES"]).sum()) if t_n else 0
        t_pct  = round((t_comp/t_n)*100) if t_n else 0
        t_cols[i].metric(tn, f"{t_comp}/{t_n}", f"{t_pct}% compliant")

    st.divider()

    # SBV Exploration
    if missing_sbv:
        with st.expander(f"🔴 SBV Drivers NOT ONLINE this period ({len(missing_sbv)} drivers)"):
            st.dataframe(pd.DataFrame({"Driver": sorted(missing_sbv)}),
                         use_container_width=True, hide_index=True)

    unassigned_sbv = df[(df.get("Is SBV", pd.Series(False, index=df.index)) == True) &
                        (df["Team"] == "Unassigned")] if "Is SBV" in df.columns else pd.DataFrame()
    if not unassigned_sbv.empty:
        with st.expander(f"🟡 SBV Drivers NOT assigned to any team ({len(unassigned_sbv)})"):
            ua = unassigned_sbv[["Driver","Score","Status"]].copy()
            st.dataframe(ua.sort_values("Score", ascending=False),
                         use_container_width=True, hide_index=True)

    st.divider()

    # Driver search table
    st.markdown("### Driver Search")
    search  = st.text_input("Search by name or team:", placeholder="e.g. John or Team LB")
    display = df.copy()
    if search:
        mask = (display["Driver"].str.lower().str.contains(search.lower(), na=False) |
                display["Team"].str.lower().str.contains(search.lower(), na=False))
        display = display[mask]

    show_cols = ["Driver","Team","Hours Online (weekly)","Trips (weekly)",
                 "Confirmation Rate","Cancellation Rate","Score","Status","KPI Met"]
    show_cols = [c for c in show_cols if c in display.columns]
    out = display[show_cols].copy()
    out["Confirmation Rate"] = out["Confirmation Rate"].apply(fmt_rate)
    out["Cancellation Rate"] = out["Cancellation Rate"].apply(fmt_rate)
    out["KPI Met"]           = out["KPI Met"].apply(fmt_bool)
    st.dataframe(out.sort_values("Score", ascending=False),
                 use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════
# TEAM VIEW
# ════════════════════════════════════════════════════════
elif view == "team":
    data = load_fleet_data()

    if not data:
        st.warning("No data available. Ask the fleet manager to publish this week's stats.")
        st.stop()

    df      = pd.DataFrame(data["fleet"])
    wi      = data.get("week_info", week_info)
    updated = data.get("updated_at", "")

    selected_team = (team_param if team_param and team_param in TEAMS
                     else st.selectbox("Select your team:", list(TEAMS.keys())))

    leader  = TEAMS[selected_team]["leader"]
    team_df = df[df["Team"] == selected_team].copy()
    team_df["Score"] = team_df["Score"].astype(float)

    st.markdown(f"# 👥 {selected_team} — Weekly Performance")
    st.markdown(
        f"*Leader: {leader}  |  {wi.get('day_name','—')}  |  "
        f"{wi.get('days_left','—')} day(s) left  |  Updated: {updated}*"
    )
    st.divider()

    if team_df.empty:
        st.warning("No drivers found for this team in the current data.")
        st.stop()

    t_total = len(team_df)
    t_comp  = int(team_df["KPI Met"].apply(lambda x: x in [True,1,"True","YES"]).sum())
    t_pct   = round((t_comp/t_total)*100) if t_total else 0
    t_best  = team_df.loc[team_df["Score"].idxmax(), "Driver"]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Team Size",       t_total)
    m2.metric("KPI Compliant",   f"{t_comp}/{t_total}")
    m3.metric("Compliance Rate", f"{t_pct}%")
    m4.metric("Top Driver",      t_best)

    st.divider()

    show_cols = ["Driver","Hours Online (weekly)","Trips (weekly)",
                 "Confirmation Rate","Cancellation Rate","Score","Status","KPI Met"]
    show_cols = [c for c in show_cols if c in team_df.columns]
    out = team_df[show_cols].copy()
    out["Confirmation Rate"] = out["Confirmation Rate"].apply(fmt_rate)
    out["Cancellation Rate"] = out["Cancellation Rate"].apply(fmt_rate)
    out["KPI Met"]           = out["KPI Met"].apply(fmt_bool)
    st.dataframe(out.sort_values("Score", ascending=False),
                 use_container_width=True, hide_index=True)
    st.caption(f"SparklingBlu Moto  |  Updated: {updated}")

else:
    st.error("Invalid link. Please ask your fleet manager for the correct link.")
