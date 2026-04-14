# SparklingBlu Moto — Weekly Driver Performance Tracker
# One app, four views driven by URL parameters
# Ready for Streamlit Cloud deployment

import streamlit as st
import pandas as pd
import json, gzip, base64, urllib.parse
from datetime import datetime
from engine import (
    calculate_performance_score,
    get_coaching_message,
    get_week_progress,
    get_remaining_targets,
)
from teams import TEAMS, match_drivers_to_teams

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="SparklingBlu — Driver Performance",
    page_icon="🚛",
    layout="wide"
)

# ─────────────────────────────────────────────
# STYLES
# ─────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #f0f4f8; }

/* Metric cards */
[data-testid="stMetric"] {
    background: white;
    border-radius: 14px;
    padding: 18px 22px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.07);
    text-align: center;
}
[data-testid="stMetricLabel"] {
    font-size: 12px !important;
    font-weight: 800 !important;
    color: #203a43 !important;
    text-transform: uppercase;
    letter-spacing: 0.6px;
}
[data-testid="stMetricValue"] {
    font-size: 34px !important;
    font-weight: 900 !important;
    color: #0f2027 !important;
}

/* Banner */
.banner {
    background: linear-gradient(90deg, #0f2027, #203a43, #2c5364);
    color: white;
    padding: 14px 22px;
    border-radius: 12px;
    margin-bottom: 18px;
    font-size: 14px;
}

/* Driver card */
.driver-card {
    background: white;
    border-radius: 16px;
    padding: 28px 32px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.10);
    margin-bottom: 18px;
}

/* KPI row items */
.kpi-met    { color: #0a8a4e; font-weight: 700; }
.kpi-notmet { color: #c0392b; font-weight: 700; }

/* Link box */
.link-box {
    background: #e8f5e9;
    border-left: 5px solid #25D366;
    border-radius: 8px;
    padding: 14px 18px;
    font-family: monospace;
    font-size: 13px;
    word-break: break-all;
    color: #111;
    margin-top: 8px;
}

/* Insight card */
.insight-card {
    background: white;
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.07);
    margin-bottom: 10px;
    font-size: 15px;
}

/* Stale data warning */
.stale-warning {
    background: #fff3cd;
    border-left: 5px solid #ffc107;
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 14px;
    margin-bottom: 16px;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# ENCODE / DECODE HELPERS (WITH ERROR HANDLING)
# ─────────────────────────────────────────────
def encode_data(df):
    """Compress a DataFrame to a URL-safe base64 string with timestamp."""
    df = df.copy()
    df.attrs["generated_at"] = datetime.now().isoformat()
    raw       = df.to_json(orient="records")
    compressed = gzip.compress(raw.encode("utf-8"))
    return base64.urlsafe_b64encode(compressed).decode("utf-8")


def decode_data(encoded):
    """
    Restore a DataFrame from a URL-safe base64 string.
    Returns (DataFrame, error_message) - error_message is None if successful.
    """
    try:
        compressed = base64.urlsafe_b64decode(encoded.encode("utf-8"))
        raw        = gzip.decompress(compressed).decode("utf-8")
        df         = pd.DataFrame(json.loads(raw))
        return df, None
    except Exception:
        return None, "Unable to decode data. The link may be corrupted or expired."


    return df


def make_link(view, df, team=None):
    """Build a shareable Streamlit URL for the given view."""
    base = st.secrets.get("APP_URL", "")
    if not base:
        st.error("APP_URL not configured in Streamlit secrets. Please contact your fleet manager.")
        st.stop()
    encoded = encode_data(df)
    params  = {"view": view, "data": encoded}
    if team:
        params["team"] = team
    return f"{base}/?{urllib.parse.urlencode(params)}"


# ─────────────────────────────────────────────
# SHARED PROCESSING
# ─────────────────────────────────────────────
def process_df(df):
    """Calculate scores, statuses, remaining targets for all drivers."""
    week_info = get_week_progress()
    scores, statuses, coachings, hrs_needed, trps_needed = [], [], [], [], []
    ar_ok_list, cr_ok_list, hrs_ok_list, trps_ok_list = [], [], [], []

    for _, row in df.iterrows():
        rem = get_remaining_targets(
            row["Hours Online"], row["Trips Taken"],
            row["Confirmation Rate"], row["Cancellation Rate"],
            week_info["progress"]
        )
        score = calculate_performance_score(
            row["Confirmation Rate"], row["Cancellation Rate"],
            row["Trips / hr"],        row["Earnings / hr"],
            row["Hours Online"],      row["Trips Taken"],
            week_info["progress"]
        )
        status, coaching = get_coaching_message(score, rem, week_info)
        scores.append(score)
        statuses.append(status)
        coachings.append(coaching)
        hrs_needed.append(rem["hours_needed"])
        trps_needed.append(rem["trips_needed"])
        ar_ok_list.append(rem["ar_on_track"])
        cr_ok_list.append(rem["cr_on_track"])
        hrs_ok_list.append(rem["hours_on_track"])
        trps_ok_list.append(rem["trips_on_track"])

    df = df.copy()
    df["Score"]          = scores
    df["Status"]         = statuses
    df["Coaching"]       = coachings
    df["Hours Needed"]   = hrs_needed
    df["Trips Needed"]   = trps_needed
    df["AR On Track"]    = ar_ok_list
    df["CR On Track"]    = cr_ok_list
    df["Hours On Track"] = hrs_ok_list
    df["Trips On Track"] = trps_ok_list
    df["KPI Met"]        = (
        (df["Hours Online"]      >= 50)   &
        (df["Confirmation Rate"] >= 0.80) &
        (df["Cancellation Rate"] <= 0.05) &
        (df["Trips Taken"]       >= 30)
    )
    return df, week_info


def fmt_rate(val):
    try:
        return f"{round(float(val) * 100)}%"
    except Exception:
        return str(val)


# ─────────────────────────────────────────────
# VIEW ROUTER
# ─────────────────────────────────────────────
params = st.query_params
view   = params.get("view", "admin")
data   = params.get("data", None)
team_param = params.get("team", None)


# ═══════════════════════════════════════════
# ADMIN VIEW
# ═══════════════════════════════════════════
if view == "admin":
    st.markdown("# 🚛 SparklingBlu — Weekly Driver Performance Tracker")
    st.caption("Admin Panel — Upload CSV to generate shareable links")
    st.divider()

    week_info    = get_week_progress()
    progress_pct = round(week_info["progress"] * 100, 1)
    day_name     = week_info["day_name"]
    days_left    = week_info["days_left"]
    now_str      = datetime.now().strftime("%d %b %Y  %H:%M")

    st.markdown(f"""
    <div class="banner">
        Today: <strong>{day_name}, {now_str}</strong>
        &nbsp;|&nbsp; Week: <strong>{progress_pct}%</strong> complete
        &nbsp;|&nbsp; <strong>{days_left} day(s)</strong> left
        &nbsp;|&nbsp; Targets: <strong>50h | 80% AR | 5% CR | 30 trips</strong>
    </div>
    """, unsafe_allow_html=True)

    uploaded = st.file_uploader("Upload Uber CSV", type=["csv"])
    if uploaded is None:
        st.info("Upload your Uber driver CSV file to get started.")
        st.stop()

    raw_df = pd.read_csv(uploaded)
    raw_df["Driver"] = raw_df["Driver first name"] + " " + raw_df["Driver surname"]
    raw_df = match_drivers_to_teams(raw_df)
    df, week_info = process_df(raw_df)

    # Summary
    st.subheader("Fleet Overview")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Drivers",         len(df))
    c2.metric("Top Performers",         len(df[df["Score"] >= 85]))
    c3.metric("Needs Attention",       len(df[(df["Score"] >= 50) & (df["Score"] < 70)]))
    c4.metric("Needs Urgent Attention",len(df[df["Score"] < 50]))
    st.divider()

    # Quick table preview
    with st.expander("Preview Driver Table"):
        preview = df[["Driver","Team","Hours Online","Trips Taken",
                       "Confirmation Rate","Cancellation Rate","Score","Status","KPI Met"]].copy()
        preview["Confirmation Rate"] = preview["Confirmation Rate"].apply(fmt_rate)
        preview["Cancellation Rate"] = preview["Cancellation Rate"].apply(fmt_rate)
        st.dataframe(preview.sort_values("Score", ascending=False),
                     use_container_width=True, hide_index=True)
    st.divider()

    # ── EXPORT BACKUP ───────────────────────────
    st.subheader("Export Data")
    col1, col2 = st.columns(2)
    with col1:
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="Download Processed CSV",
            data=csv_data,
            file_name=f"fleet_performance_{datetime.now().strftime('%Y-%m-%d')}.csv",
            mime="text/csv"
        )
    with col2:
        st.caption("Keep weekly backups for historical tracking and handover purposes.")
    st.divider()

    # ── GENERATE LINKS ─────────────────────────────
    st.subheader("Generate Shareable Links")

    # Columns to encode (keep it lean to reduce link size)
    encode_cols = [
        "Driver","Team","Hours Online","Trips Taken",
        "Confirmation Rate","Cancellation Rate",
        "Trips / hr","Earnings / hr",
        "Score","Status","Coaching",
        "Hours Needed","Trips Needed",
        "AR On Track","CR On Track","Hours On Track","Trips On Track","KPI Met"
    ]
    lean_df = df[encode_cols].copy()

    # 1. Drivers link
    st.markdown("#### Drivers Link")
    st.caption("Share this in your whole driver WhatsApp group. Each driver searches their own name.")
    drivers_link = make_link("drivers", lean_df)
    st.markdown(f'<div class="link-box">{drivers_link}</div>', unsafe_allow_html=True)
    st.code(drivers_link, language=None)

    st.divider()

    # 2. Fleet / Management link
    st.markdown("#### Management Link")
    st.caption("Share with management. Shows full fleet stats, insights, and driver search.")
    fleet_link = make_link("fleet", lean_df)
    st.markdown(f'<div class="link-box">{fleet_link}</div>', unsafe_allow_html=True)
    st.code(fleet_link, language=None)

    st.divider()

    # 3. Team links
    st.markdown("#### Team Links")
    st.caption("Generate a link for each team. Share in the team's WhatsApp group.")

    for team_name in list(TEAMS.keys()):
        team_df = lean_df[lean_df["Team"] == team_name]
        if team_df.empty:
            st.warning(f"{team_name}: no drivers found in this CSV.")
            continue
        t_link = make_link("team", lean_df, team=team_name)
        leader = TEAMS[team_name]["leader"]
        n      = len(team_df)
        kpi_n  = int(team_df["KPI Met"].sum()) if "KPI Met" in team_df.columns else 0
        with st.expander(f"{team_name}  —  Leader: {leader}  |  {n} drivers  |  {kpi_n} KPI compliant"):
            st.code(t_link, language=None)


# ═══════════════════════════════════════════
# DRIVERS VIEW
# ═══════════════════════════════════════════
elif view == "drivers" and data:
    df, error = decode_data(data)
    if error:
        st.error(error)
        st.info("Please ask your fleet manager for a new link.")
        st.stop()

    week_info = get_week_progress()

    st.markdown("# 🚛 SparklingBlu Moto — Your Weekly Stats")
    st.markdown(f"*{week_info['day_name']} check-in  |  {week_info['days_left']} day(s) left this week*")

    # Show data freshness if available
    generated_at = df.attrs.get("generated_at", None)
    if generated_at:
        try:
            gen_date = datetime.fromisoformat(generated_at)
            days_old = (datetime.now() - gen_date).days
            if days_old > 0:
                st.markdown(f"""
                <div class="stale-warning">
                    <strong>Data is {days_old} day(s) old</strong> — Last updated: {gen_date.strftime('%d %b %Y')}
                </div>
                """, unsafe_allow_html=True)
        except Exception:
            pass

    st.divider()

    search = st.text_input("Type your name to find your stats:", placeholder="e.g. John Msosa")

    if not search:
        st.info("Start typing your name above to see your stats.")
        st.stop()

    # Case-insensitive search
    matches = df[df["Driver"].str.lower().str.contains(search.strip().lower(), na=False)]

    if matches.empty:
        st.warning("No driver found with that name. Try a different spelling.")
        st.stop()

    if len(matches) > 1:
        names   = matches["Driver"].tolist()
        choice  = st.selectbox("Multiple matches — select your name:", names)
        matches = matches[matches["Driver"] == choice]

    row = matches.iloc[0]

    score  = float(row["Score"])
    status = str(row["Status"])

    # Score colour
    if score >= 85:
        score_color = "#0a8a4e"
    elif score >= 70:
        score_color = "#2980b9"
    elif score >= 50:
        score_color = "#e67e22"
    else:
        score_color = "#c0392b"

    st.markdown(f"""
    <div class="driver-card">
        <h2 style="margin:0 0 4px 0;">{row['Driver']}</h2>
        <p style="color:#666; margin:0 0 20px 0;">Team: {row.get('Team','—')}</p>
        <h1 style="font-size:64px; margin:0; color:{score_color};">{score}</h1>
        <p style="font-size:18px; color:#333; margin:4px 0 0 0;"><strong>{status}</strong></p>
    </div>
    """, unsafe_allow_html=True)

    # KPI tiles
    st.markdown("### Your KPIs This Week")
    k1, k2, k3, k4 = st.columns(4)

    def kpi_tile(col, label, value, target_label, on_track):
        icon = "OK" if on_track else "X"
        col.metric(f"{icon} {label}", value, target_label)

    kpi_tile(k1, "Hours Online",
             f"{round(float(row['Hours Online']), 1)}h",
             "Target: 50h+",
             bool(row["Hours On Track"]))
    kpi_tile(k2, "Trips Taken",
             str(int(float(row["Trips Taken"]))),
             "Target: 30+",
             bool(row["Trips On Track"]))
    kpi_tile(k3, "Acceptance Rate",
             fmt_rate(row["Confirmation Rate"]),
             "Target: 80%+",
             bool(row["AR On Track"]))
    kpi_tile(k4, "Cancellation Rate",
             fmt_rate(row["Cancellation Rate"]),
             "Target: max 5%",
             bool(row["CR On Track"]))

    st.divider()

    # What still needed
    st.markdown("### What You Still Need By Sunday")
    n1, n2 = st.columns(2)
    hrs_left  = float(row["Hours Needed"])
    trps_left = int(float(row["Trips Needed"]))

    if hrs_left > 0:
        n1.error(f"{hrs_left} more hours online needed")
    else:
        n1.success("Hours target met!")

    if trps_left > 0:
        n2.error(f"{trps_left} more trips needed")
    else:
        n2.success("Trips target met!")

    if not bool(row["AR On Track"]):
        st.error("Acceptance rate is below 80% — keep accepting trips!")
    else:
        st.success("Acceptance rate is on track!")

    if not bool(row["CR On Track"]):
        st.error("Cancellation rate is above 5% — reduce cancellations!")
    else:
        st.success("Cancellation rate is on track!")

    st.divider()

    # Coaching message
    st.markdown("### Coaching Message")
    st.info(str(row["Coaching"]))
    st.caption("SparklingBlu Moto Fleet Team")


# ═══════════════════════════════════════════
# FLEET / MANAGEMENT VIEW
# ═══════════════════════════════════════════
elif view == "fleet" and data:
    df, error = decode_data(data)
    if error:
        st.error(error)
        st.info("Please ask your fleet manager for a new link.")
        st.stop()

    week_info = get_week_progress()

    st.markdown("# 📊 SparklingBlu Moto — Fleet Performance")
    st.markdown(f"*Management Overview  |  {week_info['day_name']}  |  {week_info['days_left']} day(s) left*")

    # Show data freshness if available
    generated_at = df.attrs.get("generated_at", None)
    if generated_at:
        try:
            gen_date = datetime.fromisoformat(generated_at)
            days_old = (datetime.now() - gen_date).days
            if days_old > 0:
                st.markdown(f"""
                <div class="stale-warning">
                    <strong>Data is {days_old} day(s) old</strong> — Last updated: {gen_date.strftime('%d %b %Y')}
                </div>
                """, unsafe_allow_html=True)
        except Exception:
            pass

    st.divider()

    total      = len(df)
    compliant  = int(df["KPI Met"].sum())
    fleet_pct  = round((compliant / total) * 100) if total else 0
    top        = len(df[df["Score"].astype(float) >= 85])
    urgent     = len(df[df["Score"].astype(float) < 50])
    avg_score  = round(df["Score"].astype(float).mean(), 1)
    top_driver = df.loc[df["Score"].astype(float).idxmax(), "Driver"]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Drivers",    total)
    c2.metric("Fleet Compliance", f"{fleet_pct}%")
    c3.metric("Avg Score",        avg_score)
    c4.metric("Top Performers",   top)
    c5.metric("Urgent Attention", urgent)

    st.divider()

    # Key Insights
    st.markdown("### Key Insights")
    i1, i2 = st.columns(2)

    with i1:
        st.markdown(f"""
        <div class="insight-card"><strong>Best Driver:</strong> {top_driver}
        with a score of {df['Score'].astype(float).max()}</div>
        """, unsafe_allow_html=True)

        low_ar = df[df["Confirmation Rate"].astype(float) < 0.80]
        st.markdown(f"""
        <div class="insight-card"><strong>{len(low_ar)} driver(s)</strong>
        have acceptance rate below 80%</div>
        """, unsafe_allow_html=True)

        high_cr = df[df["Cancellation Rate"].astype(float) > 0.05]
        st.markdown(f"""
        <div class="insight-card"><strong>{len(high_cr)} driver(s)</strong>
        have cancellation rate above 5%</div>
        """, unsafe_allow_html=True)

    with i2:
        low_hrs = df[df["Hours Online"].astype(float) < 50]
        st.markdown(f"""
        <div class="insight-card"><strong>{len(low_hrs)} driver(s)</strong>
        have not yet reached 50 hours online</div>
        """, unsafe_allow_html=True)

        low_trips = df[df["Trips Taken"].astype(float) < 30]
        st.markdown(f"""
        <div class="insight-card"><strong>{len(low_trips)} driver(s)</strong>
        have not yet reached 30 trips</div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="insight-card"><strong>{compliant} of {total} drivers</strong>
        are fully KPI compliant this week ({fleet_pct}%)</div>
        """, unsafe_allow_html=True)

    st.divider()

    # Team compliance breakdown
    st.markdown("### Team Compliance")
    t_cols = st.columns(len(TEAMS))
    for i, (team_name, info) in enumerate(TEAMS.items()):
        t_df   = df[df["Team"] == team_name]
        t_n    = len(t_df)
        t_comp = int(t_df["KPI Met"].sum()) if t_n else 0
        t_pct  = round((t_comp / t_n) * 100) if t_n else 0
        t_cols[i].metric(team_name, f"{t_comp}/{t_n}", f"{t_pct}% compliant")

    st.divider()

    # Full driver table with search
    st.markdown("### Driver Search")
    search = st.text_input("Search by driver name or team:", placeholder="e.g. John or Team LB")
    display = df.copy()
    if search:
        mask = (
            display["Driver"].str.lower().str.contains(search.lower(), na=False) |
            display["Team"].str.lower().str.contains(search.lower(), na=False)
        )
        display = display[mask]

    display_cols = ["Driver","Team","Hours Online","Trips Taken",
                    "Confirmation Rate","Cancellation Rate","Score","Status","KPI Met"]
    out = display[display_cols].copy()
    out["Confirmation Rate"] = out["Confirmation Rate"].apply(fmt_rate)
    out["Cancellation Rate"] = out["Cancellation Rate"].apply(fmt_rate)
    out["Hours Online"]      = out["Hours Online"].astype(float).round(1)
    out["KPI Met"]           = out["KPI Met"].map({True:"YES", False:"NO", 1:"YES", 0:"NO"})
    st.dataframe(out.sort_values("Score", ascending=False),
                 use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════
# TEAM VIEW
# ═══════════════════════════════════════════
elif view == "team" and data:
    df, error = decode_data(data)
    if error:
        st.error(error)
        st.info("Please ask your fleet manager for a new link.")
        st.stop()

    week_info = get_week_progress()

    # If team param provided, filter directly; otherwise let user choose
    if team_param and team_param in TEAMS:
        selected_team = team_param
    else:
        selected_team = st.selectbox("Select your team:", list(TEAMS.keys()))

    leader   = TEAMS[selected_team]["leader"]
    team_df  = df[df["Team"] == selected_team].copy()

    st.markdown(f"# 👥 {selected_team} — Weekly Performance")
    st.markdown(f"*Team Leader: {leader}  |  {week_info['day_name']}  |  {week_info['days_left']} day(s) left*")
    st.divider()

    if team_df.empty:
        st.warning("No drivers found for this team in the current data.")
        st.stop()

    t_total   = len(team_df)
    t_comp    = int(team_df["KPI Met"].sum())
    t_pct     = round((t_comp / t_total) * 100) if t_total else 0
    t_best    = team_df.loc[team_df["Score"].astype(float).idxmax(), "Driver"]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Team Size",        t_total)
    m2.metric("KPI Compliant",    f"{t_comp}/{t_total}")
    m3.metric("Compliance Rate",  f"{t_pct}%")
    m4.metric("Top Driver",       t_best)

    st.divider()

    # Team driver table
    display_cols = ["Driver","Hours Online","Trips Taken",
                    "Confirmation Rate","Cancellation Rate","Score","Status","KPI Met"]
    out = team_df[display_cols].copy()
    out["Confirmation Rate"] = out["Confirmation Rate"].apply(fmt_rate)
    out["Cancellation Rate"] = out["Cancellation Rate"].apply(fmt_rate)
    out["Hours Online"]      = out["Hours Online"].astype(float).round(1)
    out["KPI Met"]           = out["KPI Met"].map({True:"YES", False:"NO", 1:"YES", 0:"NO"})
    st.dataframe(out.sort_values("Score", ascending=False),
                 use_container_width=True, hide_index=True)

    st.divider()
    st.caption(f"SparklingBlu Moto Fleet System  |  Generated {datetime.now().strftime('%d %b %Y %H:%M')}")


# ═══════════════════════════════════════════
# FALLBACK
# ═══════════════════════════════════════════
else:
    st.error("Invalid link. Please ask your fleet manager for the correct link.")
