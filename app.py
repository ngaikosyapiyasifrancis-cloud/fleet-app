# app.py — SparklingBlu Moto | Weekly Driver Performance Tracker
# Four views: admin | drivers | fleet | team
# Data stored in GitHub Gist for persistent auto-updating links

import streamlit as st
import pandas as pd
import json
from datetime import datetime
from engine import (
    calculate_performance_score, get_coaching_message,
    get_week_progress, get_remaining_targets,
    kpi_fully_met, WEEKLY_TARGETS,
)
from teams import TEAMS, SBV_TOTAL, match_drivers_to_teams, mark_sbv_drivers
from storage import save_fleet_data, load_fleet_data, is_storage_configured

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SparklingBlu — Driver Performance",
    page_icon="🚛", layout="wide"
)

st.markdown("""
<style>
[data-testid="stAppViewContainer"]  { background:#f0f4f8; }
[data-testid="stMetric"]            { background:white; border-radius:14px;
                                      padding:18px 22px; text-align:center;
                                      box-shadow:0 2px 10px rgba(0,0,0,.07); }
[data-testid="stMetricLabel"]       { font-size:12px!important; font-weight:800!important;
                                      color:#203a43!important; text-transform:uppercase;
                                      letter-spacing:.6px; }
[data-testid="stMetricValue"]       { font-size:32px!important; font-weight:900!important;
                                      color:#0f2027!important; }
.banner { background:linear-gradient(90deg,#0f2027,#203a43,#2c5364);
          color:white; padding:14px 22px; border-radius:12px;
          margin-bottom:18px; font-size:14px; }
.driver-card { background:white; border-radius:16px; padding:28px 32px;
               box-shadow:0 4px 20px rgba(0,0,0,.10); margin-bottom:18px; }
.insight-card { background:white; border-radius:12px; padding:14px 18px;
                box-shadow:0 2px 8px rgba(0,0,0,.07); margin-bottom:10px;
                font-size:15px; }
.link-box { background:#0f2027; border-left:5px solid #25D366;
            border-radius:8px; padding:12px 16px; font-family:monospace;
            font-size:13px; word-break:break-all; color:#25D366; margin-top:6px;
            letter-spacing:0.3px; }
.sbv-bar  { background:white; border-radius:12px; padding:16px 22px;
            border-left:5px solid #2c5364; margin-bottom:16px; }
</style>
""", unsafe_allow_html=True)

# ── HELPERS ───────────────────────────────────────────────────────────────────
def fmt_rate(v):
    try:    return f"{round(float(v)*100)}%"
    except: return str(v)

def fmt_bool(v):
    if v is True  or v == 1 or v == "True":  return "YES"
    if v is False or v == 0 or v == "False": return "NO"
    return str(v)

BASE_URL = "https://fleet-app-v25cphks3psbb94zeedjfq.streamlit.app"

def make_link(view, team=None):
    if team:
        return f"{BASE_URL}/?view={view}&team={team.replace(' ', '+')}"
    return f"{BASE_URL}/?view={view}"

# ── ROUTE ─────────────────────────────────────────────────────────────────────
params     = st.query_params
view       = params.get("view", "admin")
team_param = params.get("team", None)
week_info  = get_week_progress()


# ════════════════════════════════════════════
# ADMIN VIEW
# ════════════════════════════════════════════
if view == "admin":
    st.markdown("# 🚛 SparklingBlu — Admin Panel")
    st.caption("Upload CSV → process data → publish links")

    # Storage status
    if not is_storage_configured():
        st.warning("""
        ⚙️ **One-time setup needed for auto-updating links.**
        See the **Setup Guide** section at the bottom of this page.
        """)

    st.markdown(f"""
    <div class="banner">
        Today: <strong>{week_info['day_name']}, {datetime.now().strftime('%d %b %Y  %H:%M')}</strong>
        &nbsp;|&nbsp; Week: <strong>{round(week_info['progress']*100,1)}%</strong> complete
        &nbsp;|&nbsp; <strong>{week_info['days_left']} day(s)</strong> left
        &nbsp;|&nbsp; Shift: <strong>5:00am – 7:30pm</strong>
        &nbsp;|&nbsp; Targets: <strong>10h/day | 5 trips/day | 80% AR | 5% CR | 50h/week</strong>
    </div>
    """, unsafe_allow_html=True)

    col_a, col_b = st.columns([3, 1])
    with col_a:
        uploaded = st.file_uploader("Upload Uber CSV", type=["csv"])
    with col_b:
        report_days = st.number_input(
            "Days this CSV covers", min_value=1, max_value=7, value=1,
            help="e.g. if the CSV covers Mon–Wed, enter 3"
        )
        week_label = st.text_input(
            "Week label", value=datetime.now().strftime("%d %b %Y")
        )

    if uploaded is None:
        st.info("Upload your Uber driver CSV file to get started.")
        st.stop()

    # ── Process CSV ──────────────────────────────────────────
    raw = pd.read_csv(uploaded)
    raw["Driver"] = raw["Driver first name"] + " " + raw["Driver surname"]
    raw = match_drivers_to_teams(raw)
    raw = mark_sbv_drivers(raw)

    scores, statuses, coachings = [], [], []
    hrs_needed, trps_needed     = [], []
    ar_ok, cr_ok, hrs_ok, trps_ok = [], [], [], []
    d_hrs_avg, d_trp_avg        = [], []
    kpi_met_list                = []

    for _, row in raw.iterrows():
        rem = get_remaining_targets(
            row["Hours Online"], row["Trips Taken"],
            row["Confirmation Rate"], row["Cancellation Rate"],
            week_info["progress"], report_days
        )
        score = calculate_performance_score(
            row["Confirmation Rate"], row["Cancellation Rate"],
            row["Hours Online"], row["Trips Taken"],
            week_info["progress"], report_days
        )
        status, coaching = get_coaching_message(score, rem, week_info)
        kpi = kpi_fully_met(row["Hours Online"], row["Trips Taken"],
                            row["Confirmation Rate"], row["Cancellation Rate"],
                            report_days)

        scores.append(score);    statuses.append(status);   coachings.append(coaching)
        hrs_needed.append(rem["hours_needed"])
        trps_needed.append(rem["trips_needed"])
        ar_ok.append(rem["ar_on_track"]);   cr_ok.append(rem["cr_on_track"])
        hrs_ok.append(rem["hours_on_track"]); trps_ok.append(rem["trips_on_track"])
        d_hrs_avg.append(rem["daily_hours_avg"])
        d_trp_avg.append(rem["daily_trips_avg"])
        kpi_met_list.append(kpi)

    raw["Score"]          = scores
    raw["Status"]         = statuses
    raw["Coaching"]       = coachings
    raw["Hours Needed"]   = hrs_needed
    raw["Trips Needed"]   = trps_needed
    raw["AR On Track"]    = ar_ok
    raw["CR On Track"]    = cr_ok
    raw["Hours On Track"] = hrs_ok
    raw["Trips On Track"] = trps_ok
    raw["Daily Hrs Avg"]  = d_hrs_avg
    raw["Daily Trips Avg"]= d_trp_avg
    raw["KPI Met"]        = kpi_met_list

    df = raw.copy()

    # ── SBV Banner ────────────────────────────────────────────
    sbv_in_csv = df["Is SBV"].sum()
    sbv_kpi    = df[df["Is SBV"] == True]["KPI Met"].sum()
    st.markdown(f"""
    <div class="sbv-bar">
        🚛 <strong>SBV Drivers in this report:</strong>
        <span style="font-size:22px; font-weight:900; color:#0f2027;">
        &nbsp;{sbv_in_csv} / {SBV_TOTAL}</span>
        &nbsp;&nbsp;|&nbsp;&nbsp;
        SBV KPI Compliant: <strong>{sbv_kpi} / {sbv_in_csv}</strong>
        &nbsp;&nbsp;|&nbsp;&nbsp;
        SBV Compliance Rate: <strong>{round((sbv_kpi/sbv_in_csv)*100) if sbv_in_csv else 0}%</strong>
    </div>
    """, unsafe_allow_html=True)

    # ── Summary metrics ───────────────────────────────────────
    st.subheader("Fleet Overview")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Drivers",          len(df))
    c2.metric("Top Performers",         len(df[df["Score"] >= 85]))
    c3.metric("Needs Attention",        len(df[(df["Score"] >= 50) & (df["Score"] < 70)]))
    c4.metric("Needs Urgent Attention", len(df[df["Score"] < 50]))

    st.divider()

    # ── Preview table ─────────────────────────────────────────
    with st.expander("Preview Driver Table"):
        prev = df[["Driver","Team","Is SBV","Hours Online","Daily Hrs Avg",
                   "Trips Taken","Daily Trips Avg",
                   "Confirmation Rate","Cancellation Rate","Score","Status","KPI Met"]].copy()
        prev["Confirmation Rate"] = prev["Confirmation Rate"].apply(fmt_rate)
        prev["Cancellation Rate"] = prev["Cancellation Rate"].apply(fmt_rate)
        prev["KPI Met"]           = prev["KPI Met"].apply(fmt_bool)
        st.dataframe(prev.sort_values("Score", ascending=False),
                     use_container_width=True, hide_index=True)

    st.divider()

    # ── Save & generate links ─────────────────────────────────
    st.subheader("Publish & Share Links")

    encode_cols = [
        "Driver","Team","Is SBV","Hours Online","Trips Taken",
        "Confirmation Rate","Cancellation Rate",
        "Score","Status","Coaching",
        "Hours Needed","Trips Needed","Daily Hrs Avg","Daily Trips Avg",
        "AR On Track","CR On Track","Hours On Track","Trips On Track","KPI Met"
    ]
    fleet_records = df[encode_cols].to_dict(orient="records")
    payload = {
        "fleet":       fleet_records,
        "week_info":   week_info,
        "week_label":  week_label,
        "report_days": int(report_days),
        "updated_at":  datetime.now().strftime("%d %b %Y %H:%M"),
        "sbv_in_csv":  int(sbv_in_csv),
        "sbv_total":   SBV_TOTAL,
    }

    if is_storage_configured():
        if st.button("📤 Publish Data & Update All Links", type="primary",
                     use_container_width=True):
            with st.spinner("Saving to GitHub Gist..."):
                ok = save_fleet_data(payload)
            if ok:
                st.success("Data published! All links are now updated.")
            else:
                st.error("Failed to save. Check your GITHUB_TOKEN and GIST_ID in secrets.")
    else:
        st.info("Complete the one-time setup below to enable auto-updating links.")

    st.divider()

    # ── Links ─────────────────────────────────────────────────
    st.markdown("#### Your Permanent Links")
    st.caption("These links never change. Once drivers bookmark them, they always see the latest data.")

    l1, l2 = st.columns(2)
    with l1:
        st.markdown("**📱 Drivers Link** — share in your whole driver group")
        drivers_link = make_link("drivers")
        st.markdown(f'<div class="link-box">{drivers_link}</div>', unsafe_allow_html=True)
        st.code(drivers_link, language=None)

    with l2:
        st.markdown("**📊 Management Link** — share with management")
        fleet_link = make_link("fleet")
        st.markdown(f'<div class="link-box">{fleet_link}</div>', unsafe_allow_html=True)
        st.code(fleet_link, language=None)

    st.markdown("**👥 Team Links** — share each link in the team's WhatsApp group")
    t_cols = st.columns(len(TEAMS))
    for i, (team_name, info) in enumerate(TEAMS.items()):
        tlink = make_link("team", team_name)
        with t_cols[i]:
            st.markdown(f"**{team_name}**")
            st.caption(f"Leader: {info['leader']}")
            st.code(tlink, language=None)

    st.divider()

    # ── Setup Guide ───────────────────────────────────────────
    with st.expander("⚙️ One-Time Setup Guide (5 minutes)"):
        st.markdown("""
### How to enable auto-updating links

**Step 1 — Create a GitHub Personal Access Token**
1. Go to 👉 https://github.com/settings/tokens
2. Click **"Generate new token (classic)"**
3. Name it: `fleet-app-gist`
4. Tick the **`gist`** checkbox only
5. Click **"Generate token"**
6. **Copy the token** (you won't see it again)

---

**Step 2 — Create an empty GitHub Gist**
1. Go to 👉 https://gist.github.com
2. Filename: `fleet_data.json`
3. Content: `{}`
4. Click **"Create secret gist"**
5. **Copy the Gist ID** from the URL:
   `https://gist.github.com/yourname/` **`THIS_IS_YOUR_GIST_ID`**

---

**Step 3 — Add to Streamlit Secrets**
1. Go to 👉 https://share.streamlit.io → your app → **Settings** → **Secrets**
2. Paste this (replace with your values):
```toml
GITHUB_TOKEN = "ghp_yourTokenHere"
GIST_ID      = "yourGistIdHere"
```
3. Click **Save**

---

**That's it!** From now on, every time you upload a CSV and click **"Publish Data"**,
all links automatically show the new data. Drivers bookmark once and always see fresh stats.
        """)


# ════════════════════════════════════════════
# DRIVERS VIEW
# ════════════════════════════════════════════
elif view == "drivers":
    data = load_fleet_data()

    st.markdown("# 🚛 SparklingBlu Moto — Your Weekly Stats")

    if not data:
        st.warning("Stats not available yet. Please ask your fleet manager to publish this week's data.")
        st.stop()

    df = pd.DataFrame(data["fleet"])
    wi = data.get("week_info", week_info)
    updated = data.get("updated_at", "")

    st.markdown(f"*{wi.get('day_name','—')} check-in  |  "
                f"{wi.get('days_left','—')} day(s) left  |  "
                f"Last updated: {updated}*")
    st.divider()

    search = st.text_input("Type your name:", placeholder="e.g. John Msosa")
    if not search:
        st.info("Start typing your name above to see your stats.")
        st.stop()

    matches = df[df["Driver"].str.lower().str.contains(search.strip().lower(), na=False)]
    if matches.empty:
        st.warning("No driver found with that name. Try a different spelling.")
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
    <div class="driver-card">
        <h2 style="margin:0 0 4px 0;">👤 {row['Driver']}</h2>
        <p style="color:#666; margin:0 0 20px 0;">Team: {row.get('Team','—')}</p>
        <h1 style="font-size:64px; margin:0; color:{score_color};">{score}</h1>
        <p style="font-size:20px; margin:6px 0 0 0;">
            {status_emoji} <strong>{row['Status']}</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Your KPIs This Week")
    k1, k2, k3, k4 = st.columns(4)

    def kpi_tile(col, label, value, target, on_track):
        icon = "✅" if on_track else "❌"
        col.metric(f"{icon} {label}", value, target)

    kpi_tile(k1, "Daily Hours Avg",
             f"{row['Daily Hrs Avg']}h/day", "Target: 10h/day min",
             bool(row.get("Hours On Track", False)))
    kpi_tile(k2, "Daily Trips Avg",
             f"{row['Daily Trips Avg']}/day", "Target: 5 trips/day min",
             bool(row.get("Trips On Track", False)))
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
        f"⏱️ {'Still need ' + str(hrs_left) + ' more hours this week' if hrs_left > 0 else 'Weekly hours target met!'}")
    (n2.error if trps_left > 0 else n2.success)(
        f"🚗 {'Still need ' + str(trps_left) + ' more trips this week' if trps_left > 0 else 'Weekly trips target met!'}")

    ar_ok = row.get("AR On Track", False)
    cr_ok = row.get("CR On Track", False)
    (st.success if ar_ok else st.error)(
        "📈 Acceptance rate is on track!" if ar_ok else "📉 Acceptance rate is below 80% — keep accepting trips!")
    (st.success if cr_ok else st.error)(
        "✅ Cancellation rate is on track!" if cr_ok else "⚠️ Cancellation rate is above 5% — reduce cancellations!")

    st.divider()
    st.markdown("### Coaching Message")
    st.info(str(row.get("Coaching", "")))
    st.caption("SparklingBlu Moto Fleet Team 🚛")


# ════════════════════════════════════════════
# FLEET / MANAGEMENT VIEW
# ════════════════════════════════════════════
elif view == "fleet":
    data = load_fleet_data()

    st.markdown("# 📊 SparklingBlu Moto — Fleet Performance")

    if not data:
        st.warning("No data available. Ask the fleet manager to publish this week's stats.")
        st.stop()

    df      = pd.DataFrame(data["fleet"])
    wi      = data.get("week_info", week_info)
    updated = data.get("updated_at", "")
    sbv_in  = data.get("sbv_in_csv", 0)
    sbv_tot = data.get("sbv_total", SBV_TOTAL)

    st.markdown(f"*Management Overview  |  {wi.get('day_name','—')}  |  "
                f"{wi.get('days_left','—')} day(s) left  |  Updated: {updated}*")

    st.markdown(f"""
    <div class="sbv-bar">
        🚛 <strong>SBV Drivers in report:</strong>
        <span style="font-size:20px; font-weight:900;">&nbsp;{sbv_in} / {sbv_tot}</span>
    </div>
    """, unsafe_allow_html=True)

    total     = len(df)
    df["Score"] = df["Score"].astype(float)
    compliant = int(df["KPI Met"].apply(lambda x: x in [True, 1, "True", "YES"]).sum())
    fleet_pct = round((compliant / total) * 100) if total else 0
    top       = len(df[df["Score"] >= 85])
    urgent    = len(df[df["Score"] < 50])
    avg_score = round(df["Score"].mean(), 1)
    top_driver= df.loc[df["Score"].idxmax(), "Driver"]

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Total Drivers",    total)
    c2.metric("Fleet Compliance", f"{fleet_pct}%")
    c3.metric("Avg Score",        avg_score)
    c4.metric("Top Performers",   top)
    c5.metric("Urgent Attention", urgent)

    st.divider()
    st.markdown("### Key Insights")
    i1, i2 = st.columns(2)

    def insight(col, text):
        col.markdown(f'<div class="insight-card">{text}</div>', unsafe_allow_html=True)

    with i1:
        insight(i1, f"🏆 <strong>Best Driver:</strong> {top_driver} — score {df['Score'].max()}")
        low_ar = (df["Confirmation Rate"].astype(float) < 0.80).sum()
        insight(i1, f"📉 <strong>{low_ar} driver(s)</strong> below 80% acceptance rate")
        high_cr = (df["Cancellation Rate"].astype(float) > 0.05).sum()
        insight(i1, f"⚠️ <strong>{high_cr} driver(s)</strong> above 5% cancellation rate")
    with i2:
        low_dhrs = (df["Daily Hrs Avg"].astype(float) < 10).sum()
        insight(i2, f"⏱️ <strong>{low_dhrs} driver(s)</strong> averaging below 10h/day")
        low_dtrp = (df["Daily Trips Avg"].astype(float) < 5).sum()
        insight(i2, f"🚗 <strong>{low_dtrp} driver(s)</strong> averaging below 5 trips/day")
        insight(i2, f"✅ <strong>{compliant}/{total}</strong> drivers fully KPI compliant ({fleet_pct}%)")

    st.divider()
    st.markdown("### Team Compliance")
    t_cols = st.columns(len(TEAMS))
    for i, (tn, info) in enumerate(TEAMS.items()):
        t_df   = df[df["Team"] == tn]
        t_n    = len(t_df)
        t_comp = int(t_df["KPI Met"].apply(
            lambda x: x in [True, 1, "True", "YES"]).sum()) if t_n else 0
        t_pct  = round((t_comp/t_n)*100) if t_n else 0
        t_cols[i].metric(tn, f"{t_comp}/{t_n}", f"{t_pct}% compliant")

    st.divider()
    st.markdown("### Driver Search")
    search  = st.text_input("Search by name or team:", placeholder="e.g. John or Team LB")
    display = df.copy()
    if search:
        mask = (display["Driver"].str.lower().str.contains(search.lower(), na=False) |
                display["Team"].str.lower().str.contains(search.lower(), na=False))
        display = display[mask]

    out = display[["Driver","Team","Daily Hrs Avg","Daily Trips Avg",
                   "Confirmation Rate","Cancellation Rate","Score","Status","KPI Met"]].copy()
    out["Confirmation Rate"] = out["Confirmation Rate"].apply(fmt_rate)
    out["Cancellation Rate"] = out["Cancellation Rate"].apply(fmt_rate)
    out["KPI Met"]           = out["KPI Met"].apply(fmt_bool)
    st.dataframe(out.sort_values("Score", ascending=False),
                 use_container_width=True, hide_index=True)


# ════════════════════════════════════════════
# TEAM VIEW
# ════════════════════════════════════════════
elif view == "team":
    data = load_fleet_data()

    if not data:
        st.warning("No data available. Ask the fleet manager to publish this week's stats.")
        st.stop()

    df      = pd.DataFrame(data["fleet"])
    wi      = data.get("week_info", week_info)
    updated = data.get("updated_at", "")

    if team_param and team_param in TEAMS:
        selected_team = team_param
    else:
        selected_team = st.selectbox("Select your team:", list(TEAMS.keys()))

    leader  = TEAMS[selected_team]["leader"]
    team_df = df[df["Team"] == selected_team].copy()
    team_df["Score"] = team_df["Score"].astype(float)

    st.markdown(f"# 👥 {selected_team} — Weekly Performance")
    st.markdown(f"*Leader: {leader}  |  {wi.get('day_name','—')}  |  "
                f"{wi.get('days_left','—')} day(s) left  |  Updated: {updated}*")
    st.divider()

    if team_df.empty:
        st.warning("No drivers found for this team in the current data.")
        st.stop()

    t_total = len(team_df)
    t_comp  = int(team_df["KPI Met"].apply(
        lambda x: x in [True, 1, "True", "YES"]).sum())
    t_pct   = round((t_comp/t_total)*100) if t_total else 0
    t_avg   = round(team_df["Score"].mean(), 1)
    t_best  = team_df.loc[team_df["Score"].idxmax(), "Driver"]

    m1,m2,m3,m4 = st.columns(4)
    m1.metric("Team Size",       t_total)
    m2.metric("KPI Compliant",   f"{t_comp}/{t_total}")
    m3.metric("Compliance Rate", f"{t_pct}%")
    m4.metric("Top Driver",      t_best)

    st.divider()

    out = team_df[["Driver","Daily Hrs Avg","Daily Trips Avg",
                   "Confirmation Rate","Cancellation Rate","Score","Status","KPI Met"]].copy()
    out["Confirmation Rate"] = out["Confirmation Rate"].apply(fmt_rate)
    out["Cancellation Rate"] = out["Cancellation Rate"].apply(fmt_rate)
    out["KPI Met"]           = out["KPI Met"].apply(fmt_bool)
    st.dataframe(out.sort_values("Score", ascending=False),
                 use_container_width=True, hide_index=True)
    st.caption(f"SparklingBlu Moto  |  {datetime.now().strftime('%d %b %Y %H:%M')}")

else:
    st.error("Invalid link. Please ask your fleet manager for the correct link.")
