# app.py
# SparklingBlu Moto — Weekly Driver Performance Tracker

import streamlit as st
import pandas as pd
from datetime import datetime
from engine import (
    calculate_performance_score,
    get_coaching_message,
    get_week_progress,
    get_remaining_targets,
    generate_whatsapp_message,
)
from teams import TEAMS, match_drivers_to_teams
from pdf_generator import generate_fleet_pdf, generate_team_pdf

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
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
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("# SparklingBlu — Weekly Driver Performance Tracker")
st.caption("Powered by SparklingBlu Moto Fleet System")
st.divider()

# ─────────────────────────────────────────────
# WEEK PROGRESS BANNER
# ─────────────────────────────────────────────
week_info    = get_week_progress()
progress_pct = round(week_info["progress"] * 100, 1)
day_name     = week_info["day_name"]
days_left    = week_info["days_left"]
now_str      = datetime.now().strftime("%d %b %Y  %H:%M")

st.markdown(f"""
<div class="week-banner">
    &nbsp; Today: <strong>{day_name}, {now_str}</strong>
    &nbsp;&nbsp;|&nbsp;&nbsp;
    Week Progress: <strong>{progress_pct}%</strong>
    &nbsp;&nbsp;|&nbsp;&nbsp;
    <strong>{days_left} day(s)</strong> left until Sunday 23:59
    &nbsp;&nbsp;|&nbsp;&nbsp;
    Targets: <strong>50+ hrs &nbsp;|&nbsp; 80%+ AR &nbsp;|&nbsp; max 5% CR &nbsp;|&nbsp; 30+ trips</strong>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# FILE UPLOAD
# ─────────────────────────────────────────────
uploaded_file = st.file_uploader("Upload your Uber CSV file", type=["csv"])

if uploaded_file is None:
    st.info("Please upload your Uber driver CSV file to get started.")
    st.stop()

# ─────────────────────────────────────────────
# WEEK LABEL INPUT (for PDFs)
# ─────────────────────────────────────────────
week_label = st.text_input(
    "Week label for PDFs (e.g.  06 - 08 April 2026)",
    value=datetime.now().strftime("%d %b %Y")
)

# ─────────────────────────────────────────────
# LOAD & PROCESS DATA
# ─────────────────────────────────────────────
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

# ─────────────────────────────────────────────
# SUMMARY METRICS
# ─────────────────────────────────────────────
st.subheader("Fleet Overview")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Drivers",       len(df))
c2.metric("Top Performers",      len(top_performers))
c3.metric("Needs Attention",     len(needs_attention))
c4.metric("Needs Urgent Attention", len(needs_urgent))

st.divider()

# ─────────────────────────────────────────────
# HELPER: FORMAT TABLE
# ─────────────────────────────────────────────
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

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📊  All Drivers",
    "⚠️  Needs Attention",
    "🚨  Needs Urgent Attention",
    "👥  Teams",
])

# ── TAB 1: ALL DRIVERS ───────────────────────
with tab1:
    st.markdown(f"**{len(df)} drivers** in this report")
    st.dataframe(
        fmt(df.sort_values("Score", ascending=False)),
        use_container_width=True,
        hide_index=True
    )
    st.divider()
    st.markdown("#### Generate Fleet PDF Report")
    fleet_pdf = generate_fleet_pdf(df, week_label)
    st.download_button(
        label="Download Fleet PDF",
        data=fleet_pdf,
        file_name=f"SparklingBlu_Fleet_Report_{week_label.replace(' ', '_')}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

# ── TAB 2: NEEDS ATTENTION ───────────────────
with tab2:
    if needs_attention.empty:
        st.success("No drivers in this category right now.")
    else:
        st.warning(f"{len(needs_attention)} driver(s) need attention (score 50–69).")
        st.dataframe(
            fmt(needs_attention.sort_values("Score")),
            use_container_width=True,
            hide_index=True
        )

# ── TAB 3: NEEDS URGENT ATTENTION ────────────
with tab3:
    if needs_urgent.empty:
        st.success("No drivers need urgent attention right now.")
    else:
        st.error(f"{len(needs_urgent)} driver(s) need urgent attention (score below 50).")
        st.dataframe(
            fmt(needs_urgent.sort_values("Score")),
            use_container_width=True,
            hide_index=True
        )

# ── TAB 4: TEAMS ─────────────────────────────
with tab4:
    st.markdown("### Teams")

    # Team selector
    team_names    = list(TEAMS.keys())
    selected_team = st.selectbox("Select a team:", team_names)
    team_info     = TEAMS[selected_team]
    leader_name   = team_info["leader"]

    # Filter drivers for this team
    team_df = df[df["Team"] == selected_team].copy()

    if team_df.empty:
        st.warning("No drivers from this team found in the uploaded CSV.")
    else:
        # Team summary
        t_compliant = len(team_df[team_df["KPI Met"] == "YES"])
        t_total     = len(team_df)
        t_pct       = round((t_compliant / t_total) * 100) if t_total else 0

        m1, m2, m3 = st.columns(3)
        m1.metric("Team Leader",       leader_name)
        m2.metric("Drivers in CSV",    t_total)
        m3.metric("KPI Compliance",    f"{t_compliant}/{t_total}  ({t_pct}%)")

        st.dataframe(
            fmt(team_df.sort_values("Score", ascending=False)),
            use_container_width=True,
            hide_index=True
        )

        # Team PDF
        st.divider()
        st.markdown("#### Generate Team PDF Report")
        team_pdf = generate_team_pdf(selected_team, leader_name, team_df, week_label)
        st.download_button(
            label=f"Download {selected_team} PDF",
            data=team_pdf,
            file_name=f"SparklingBlu_{selected_team.replace(' ', '_')}_{week_label.replace(' ', '_')}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

        # Individual WhatsApp messages
        st.divider()
        st.markdown("#### Individual Driver WhatsApp Message")
        st.caption("Select a driver to generate a ready-to-copy message.")

        driver_list    = sorted(team_df["Driver"].tolist())
        selected_driver = st.selectbox("Select a driver:", driver_list, key="team_driver")

        if selected_driver:
            d_row      = df[df["Driver"] == selected_driver].iloc[0]
            d_idx      = df[df["Driver"] == selected_driver].index[0]
            d_remaining = remaining_list[d_idx]

            wa_msg = generate_whatsapp_message(
                driver_name=selected_driver,
                score=d_row["Score"],
                status=d_row["Status"],
                remaining=d_remaining,
                week_info=week_info,
                row=d_row,
                language="english"
            )

            st.markdown(f"**Message for {selected_driver}** — copy and paste into WhatsApp:")
            st.text_area(
                label="",
                value=wa_msg,
                height=400,
                key="wa_individual"
            )
