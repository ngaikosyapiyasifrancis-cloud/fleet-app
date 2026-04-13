# app.py
# SparklingBlu Moto — Weekly Driver Performance Tracker
# Generates shareable links instead of PDFs for drivers, teams, and fleet overview.

import streamlit as st
import pandas as pd
from datetime import datetime
from engine import (
    calculate_performance_score,
    get_coaching_message,
    get_week_progress,
    get_remaining_targets,
    generate_whatsapp_message,
    generate_team_whatsapp_message,
    generate_driver_link,
    generate_team_link,
    generate_fleet_link,
)
from teams import TEAMS, match_drivers_to_teams

# ---------------------------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="SparklingBlu — Driver Performance",
    page_icon="🚛",
    layout="wide"
)

st.markdown("""
<style>
/* Main background */
[data-testid="stAppViewContainer"] { background-color: #f4f6f9; }

/* Metric cards */
[data-testid="stMetric"] {
    background: white;
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    text-align: center;
}
[data-testid="stMetricLabel"] {
    font-size: 13px !important;
    font-weight: 700 !important;
    color: #203a43 !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
[data-testid="stMetricValue"] {
    font-size: 32px !important;
    font-weight: 800 !important;
    color: #0f2027 !important;
}

/* Week banner */
.week-banner {
    background: linear-gradient(90deg, #0f2027, #203a43, #2c5364);
    color: white;
    padding: 14px 22px;
    border-radius: 12px;
    margin-bottom: 18px;
    font-size: 14px;
}

/* Link box */
.link-box {
    background: #e8f5e9;
    border-left: 4px solid #4CAF50;
    border-radius: 8px;
    padding: 16px;
    font-family: monospace;
    font-size: 13px;
    white-space: pre-wrap;
    color: #111;
}

/* WhatsApp message box */
.wa-box {
    background: #f0f4f0;
    border-left: 4px solid #25D366;
    border-radius: 8px;
    padding: 16px;
    font-family: monospace;
    font-size: 13px;
    white-space: pre-wrap;
    color: #111;
}

/* Tab styling */
[data-testid="stTab"] { font-weight: 600; }

/* Success/Info boxes */
.stAlert { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# HEADER
# ---------------------------------------------------------------------------
st.markdown("# SparklingBlu — Weekly Driver Performance Tracker")
st.caption("Powered by SparklingBlu Moto Fleet System")
st.divider()

# ---------------------------------------------------------------------------
# WEEK PROGRESS BANNER
# ---------------------------------------------------------------------------
week_info    = get_week_progress()
progress_pct = round(week_info["progress"] * 100, 1)
day_name     = week_info["day_name"]
days_left    = week_info["days_left"]
now_str      = datetime.now().strftime("%d %b %Y  %H:%M")

st.markdown(f"""
<div class="week-banner">
    Today: <strong>{day_name}, {now_str}</strong>
    &nbsp;|&nbsp;
    Week Progress: <strong>{progress_pct}%</strong>
    &nbsp;|&nbsp;
    <strong>{days_left} day(s)</strong> left until Sunday 23:59
    &nbsp;|&nbsp;
    Targets: <strong>50+ hrs | 80%+ AR | max 5% CR | 30+ trips</strong>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# APP URL CONFIGURATION
# ---------------------------------------------------------------------------
st.markdown("### Configuration")
col_url1, col_url2 = st.columns([3, 1])

with col_url1:
    app_url = st.text_input(
        "App URL (for generating shareable links)",
        value="https://sparklingblu-fleet.streamlit.app",
        help="This is the URL where your viewer.html will be deployed. Update this after deployment."
    )

with col_url2:
    week_label = st.text_input(
        "Week Label",
        value=datetime.now().strftime("%d %b %Y"),
        help="Label for this week's data (e.g., '06 - 12 April 2026')"
    )

st.divider()

# ---------------------------------------------------------------------------
# FILE UPLOAD
# ---------------------------------------------------------------------------
uploaded_file = st.file_uploader("Upload your Uber CSV file", type=["csv"])

if uploaded_file is None:
    st.info("Please upload your Uber driver CSV file to get started.")
    st.stop()

# ---------------------------------------------------------------------------
# LOAD & PROCESS DATA
# ---------------------------------------------------------------------------
df = pd.read_csv(uploaded_file)
df["Driver"] = df["Driver first name"] + " " + df["Driver surname"]
df = match_drivers_to_teams(df)

scores, statuses, messages, remaining_list = [], [], [], []

for _, row in df.iterrows():
    remaining = get_remaining_targets(
        hours_online=row["Hours Online"],
        trips_taken=row["Trips Taken"],
        confirmation_rate=row["Confirmation Rate"],
        cancellation_rate=row["Cancellation Rate"],
        progress=week_info["progress"]
    )
    score = calculate_performance_score(
        confirmation_rate=row["Confirmation Rate"],
        cancellation_rate=row["Cancellation Rate"],
        trips_per_hr=row["Trips / hr"],
        earnings_per_hr=row["Earnings / hr"],
        hours_online=row["Hours Online"],
        trips_taken=row["Trips Taken"],
        progress=week_info["progress"]
    )
    status, message = get_coaching_message(score, remaining, week_info)
    scores.append(score)
    statuses.append(status)
    messages.append(message)
    remaining_list.append(remaining)

df["Score"]            = scores
df["Status"]           = statuses
df["Coaching Message"] = messages

# KPI compliance flag
df["KPI Met"] = (
    (df["Hours Online"]      >= 50)  &
    (df["Confirmation Rate"] >= 0.80) &
    (df["Cancellation Rate"] <= 0.05) &
    (df["Trips Taken"]       >= 30)
).map({True: "YES", False: "NO"})

# Count known drivers (matched to a team)
known_drivers   = df[df["Team"] != "Unassigned"]
top_performers  = df[df["Score"] >= 85]
needs_attention = df[(df["Score"] >= 50) & (df["Score"] < 70)]
needs_urgent    = df[df["Score"] < 50]

# ---------------------------------------------------------------------------
# SUMMARY METRICS
# ---------------------------------------------------------------------------
st.subheader("Fleet Overview")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Drivers",       len(df))
c2.metric("Top Performers",      len(top_performers))
c3.metric("Needs Attention",     len(needs_attention))
c4.metric("Needs Urgent Attention", len(needs_urgent))

st.divider()

# ---------------------------------------------------------------------------
# HELPER: FORMAT TABLE
# ---------------------------------------------------------------------------
DISPLAY_COLS = [
    "Driver", "Team", "Hours Online", "Trips Taken",
    "Confirmation Rate", "Cancellation Rate",
    "Score", "Status", "KPI Met"
]

def fmt(data):
    d = data[DISPLAY_COLS].copy()
    d["Confirmation Rate"] = (d["Confirmation Rate"] * 100).round(1).astype(str) + "%"
    d["Cancellation Rate"] = (d["Cancellation Rate"] * 100).round(1).astype(str) + "%"
    d["Hours Online"]      = d["Hours Online"].round(1)
    return d

# ---------------------------------------------------------------------------
# TABS
# ---------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Fleet Overview",
    "Individual Driver Links",
    "Team Links",
    "All Drivers Table",
    "WhatsApp Messages"
])

# ── TAB 1: FLEET OVERVIEW ───────────────────────────────────────────────────
with tab1:
    st.markdown("### Fleet Performance Summary")

    # Fleet stats
    fleet_avg = round(df["Score"].mean(), 1)
    fleet_pct = round((len(df[df["KPI Met"] == "YES"]) / len(df)) * 100, 1)

    col1, col2, col3 = st.columns(3)
    col1.metric("Fleet Avg Score", f"{fleet_avg}/100")
    col2.metric("KPI Compliance", f"{fleet_pct}%")
    col3.metric("Total Active", len(df))

    st.divider()

    # Fleet shareable link
    fleet_link = generate_fleet_link(app_url, week_label)
    st.markdown("#### Shareable Fleet Link")
    st.markdown("Share this link with management to view the full fleet performance:")

    st.markdown(f'<div class="link-box">{fleet_link}</div>', unsafe_allow_html=True)
    st.code(fleet_link, language=None)

    st.divider()

    # Team breakdown
    st.markdown("#### Team Performance Breakdown")
    team_stats = []
    for team_name in sorted(TEAMS.keys()):
        team_df_subset = df[df["Team"] == team_name]
        if not team_df_subset.empty:
            avg_score = round(team_df_subset["Score"].mean(), 1)
            compliant = len(team_df_subset[team_df_subset["KPI Met"] == "YES"])
            total = len(team_df_subset)
            team_stats.append({
                "Team": team_name,
                "Leader": TEAMS[team_name]["leader"],
                "Active Drivers": total,
                "Avg Score": avg_score,
                "KPI Compliant": f"{compliant}/{total}"
            })

    if team_stats:
        st.dataframe(pd.DataFrame(team_stats), use_container_width=True, hide_index=True)
    else:
        st.warning("No team data available yet.")

# ── TAB 2: INDIVIDUAL DRIVER LINKS ────────────────────────────────────────
with tab2:
    st.markdown("### Generate Individual Driver Links")
    st.info("Click the button next to a driver to copy their shareable link. Drivers will see their personal stats and what they need to meet their targets.")

    # Driver selector
    driver_list = sorted(df["Driver"].tolist())
    selected_driver = st.selectbox("Select a driver:", driver_list, key="driver_link_select")

    if selected_driver:
        d_row = df[df["Driver"] == selected_driver].iloc[0]
        d_idx = df[df["Driver"] == selected_driver].index[0]
        d_remaining = remaining_list[d_idx]

        # Driver stats display
        st.markdown("#### Driver Stats Preview")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Score", f"{d_row['Score']}/100")
        col2.metric("Status", d_row["Status"])
        col3.metric("Team", d_row["Team"])
        col4.metric("KPI Met", d_row["KPI Met"])

        with st.expander("View full stats"):
            col_a, col_b = st.columns(2)
            with col_a:
                st.write(f"**Hours Online:** {round(d_row['Hours Online'], 1)} hrs")
                st.write(f"**Trips Taken:** {int(d_row['Trips Taken'])}")
                st.write(f"**Earnings / hr:** R{round(d_row['Earnings / hr'], 2)}")
            with col_b:
                st.write(f"**Acceptance Rate:** {round(d_row['Confirmation Rate'] * 100, 1)}%")
                st.write(f"**Cancellation Rate:** {round(d_row['Cancellation Rate'] * 100, 1)}%")
                st.write(f"**Total Earnings:** R{round(d_row['Total Earnings'], 2)}")

        st.divider()

        # Generate link
        driver_link = generate_driver_link(app_url, selected_driver, week_label)
        st.markdown("#### Shareable Link for Driver")
        st.markdown(f"Share this link with {selected_driver} on WhatsApp:")

        st.markdown(f'<div class="link-box">{driver_link}</div>', unsafe_allow_html=True)
        st.code(driver_link, language=None)

        st.divider()

        # WhatsApp message for this driver
        wa_msg = generate_whatsapp_message(
            driver_name=selected_driver,
            score=d_row["Score"],
            status=d_row["Status"],
            remaining=d_remaining,
            week_info=week_info,
            row=d_row,
            language="english"
        )

        st.markdown("#### WhatsApp Message for Driver")
        st.text_area(
            label="Copy this message:",
            value=wa_msg,
            height=300,
            key="wa_driver_tab"
        )

    st.divider()

    # Bulk generate all driver links
    st.markdown("#### All Driver Links (Bulk)")
    with st.expander("Show all driver links"):
        for driver in sorted(df["Driver"].tolist()):
            link = generate_driver_link(app_url, driver, week_label)
            st.text(f"{driver}: {link}")

# ── TAB 3: TEAM LINKS ───────────────────────────────────────────────────────
with tab3:
    st.markdown("### Generate Team Links")
    st.info("Share team links with team leaders so they can view their team's performance.")

    # Team selector
    team_names = list(TEAMS.keys())
    selected_team = st.selectbox("Select a team:", team_names, key="team_link_select")
    team_info = TEAMS[selected_team]
    leader_name = team_info["leader"]

    # Filter team data
    team_df = df[df["Team"] == selected_team].copy()

    if team_df.empty:
        st.warning("No drivers from this team found in the uploaded CSV.")
    else:
        # Team stats
        t_avg = round(team_df["Score"].mean(), 1)
        t_compliant = len(team_df[team_df["KPI Met"] == "YES"])
        t_total = len(team_df)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Team Leader", leader_name)
        col2.metric("Active Drivers", t_total)
        col3.metric("Avg Score", f"{t_avg}/100")
        col4.metric("KPI Compliant", f"{t_compliant}/{t_total}")

        st.divider()

        # Generate team link
        team_link = generate_team_link(app_url, selected_team, week_label)
        st.markdown("#### Shareable Team Link")
        st.markdown(f"Share this link with {leader_name} and the {selected_team} management:")

        st.markdown(f'<div class="link-box">{team_link}</div>', unsafe_allow_html=True)
        st.code(team_link, language=None)

        st.divider()

        # Team WhatsApp message
        team_wa = generate_team_whatsapp_message(selected_team, team_df, week_info)
        st.markdown("#### WhatsApp Message for Team")
        st.text_area(
            label="Copy this message:",
            value=team_wa,
            height=200,
            key="wa_team_tab"
        )

        st.divider()

        # Team driver list with links
        st.markdown("#### Individual Driver Links for This Team")
        for driver in sorted(team_df["Driver"].tolist()):
            link = generate_driver_link(app_url, driver, week_label)
            with st.expander(f"{driver}"):
                st.code(link, language=None)

    st.divider()

    # All teams overview
    st.markdown("#### All Team Links")
    for team_name in sorted(TEAMS.keys()):
        link = generate_team_link(app_url, team_name, week_label)
        st.text(f"{team_name}: {link}")

# ── TAB 4: ALL DRIVERS TABLE ────────────────────────────────────────────────
with tab4:
    st.markdown(f"**{len(df)} drivers** in this report")

    # Filters
    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        filter_team = st.selectbox("Filter by Team:", ["All"] + list(TEAMS.keys()))
    with col_filter2:
        filter_status = st.selectbox("Filter by Status:", ["All", "Top Performer", "Good", "Needs Improvement", "Urgent Attention"])

    filtered_df = df.copy()
    if filter_team != "All":
        filtered_df = filtered_df[filtered_df["Team"] == filter_team]
    if filter_status != "All":
        status_map = {
            "Top Performer": "Top Performer",
            "Good": "Good",
            "Needs Improvement": "Needs Improvement",
            "Urgent Attention": "Urgent Attention"
        }
        filtered_df = filtered_df[filtered_df["Status"] == status_map[filter_status]]

    st.dataframe(
        fmt(filtered_df.sort_values("Score", ascending=False)),
        use_container_width=True,
        hide_index=True
    )

# ── TAB 5: WHATSAPP MESSAGES ────────────────────────────────────────────────
with tab5:
    st.markdown("### WhatsApp Messages")

    # Fleet WhatsApp message
    st.markdown("#### Fleet-Wide Message (for Management)")
    fleet_msg = generate_bulk_whatsapp_message(df, week_info)
    st.text_area(
        label="Copy this message:",
        value=fleet_msg,
        height=250,
        key="wa_fleet"
    )

    st.divider()

    # Team WhatsApp messages
    st.markdown("#### Team Messages")
    team_for_wa = st.selectbox("Select team:", list(TEAMS.keys()), key="wa_team_select")
    team_df_wa = df[df["Team"] == team_for_wa].copy()

    if not team_df_wa.empty:
        team_wa_msg = generate_team_whatsapp_message(team_for_wa, team_df_wa, week_info)
        st.text_area(
            label=f"Copy {team_for_wa} message:",
            value=team_wa_msg,
            height=150,
            key=f"wa_team_{team_for_wa}"
        )

    st.divider()

    # Individual driver message
    st.markdown("#### Individual Driver Message")
    driver_for_wa = st.selectbox("Select driver:", sorted(df["Driver"].tolist()), key="wa_individual_select")

    if driver_for_wa:
        d_row_wa = df[df["Driver"] == driver_for_wa].iloc[0]
        d_idx_wa = df[df["Driver"] == driver_for_wa].index[0]
        d_remaining_wa = remaining_list[d_idx_wa]

        ind_wa_msg = generate_whatsapp_message(
            driver_name=driver_for_wa,
            score=d_row_wa["Score"],
            status=d_row_wa["Status"],
            remaining=d_remaining_wa,
            week_info=week_info,
            row=d_row_wa,
            language="english"
        )
        st.text_area(
            label=f"Copy message for {driver_for_wa}:",
            value=ind_wa_msg,
            height=350,
            key=f"wa_ind_{driver_for_wa}"
        )

# ---------------------------------------------------------------------------
# FOOTER
# ---------------------------------------------------------------------------
st.divider()
st.caption(f"Generated: {now_str} | SparklingBlu Moto Fleet System")
