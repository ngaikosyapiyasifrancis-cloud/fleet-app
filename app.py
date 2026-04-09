# app.py

import streamlit as st
import pandas as pd

from engine import (
    calculate_performance_score,
    get_coaching_message,
    get_week_progress,
    get_remaining_targets,
    generate_whatsapp_message,
)

from teams import match_drivers_to_teams, TEAMS
from pdf_generator import generate_fleet_pdf, generate_team_pdf

# ---------------------------
# PAGE SETUP
# ---------------------------
st.set_page_config(
    page_title="SparklingBlu — Weekly Driver Performance Tracker",
    layout="wide"
)

st.title("🚛 SparklingBlu — Weekly Driver Performance Tracker")
st.divider()

# ---------------------------
# WEEK INFO
# ---------------------------
week_info = get_week_progress()

st.info(
    f"{week_info['day_name']} | "
    f"{round(week_info['progress']*100,1)}% week done | "
    f"{week_info['days_left']} day(s) left"
)

# ---------------------------
# UPLOAD CSV
# ---------------------------
file = st.file_uploader("Upload Uber CSV", type=["csv"])

if file is None:
    st.stop()

df = pd.read_csv(file)
df["Driver"] = df["Driver first name"] + " " + df["Driver surname"]

# ---------------------------
# MATCH TEAMS
# ---------------------------
df = match_drivers_to_teams(df)

# ---------------------------
# CALCULATIONS
# ---------------------------
scores = []
statuses = []

for _, row in df.iterrows():

    remaining = get_remaining_targets(
        row["Hours Online"],
        row["Trips Taken"],
        row["Confirmation Rate"],
        row["Cancellation Rate"],
        week_info["progress"]
    )

    score = calculate_performance_score(
        row["Confirmation Rate"],
        row["Cancellation Rate"],
        row["Trips / hr"],
        row["Earnings / hr"],
        row["Hours Online"],
        row["Trips Taken"],
        week_info["progress"]
    )

    status, _ = get_coaching_message(score, remaining, week_info)

    scores.append(score)
    statuses.append(status)

df["Score"] = scores
df["Status"] = statuses

# ---------------------------
# KPI DASHBOARD
# ---------------------------
st.subheader("📊 Overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Drivers", len(df))
col2.metric("Top Performers", len(df[df["Score"] >= 85]))
col3.metric("Needs Attention", len(df[(df["Score"] >= 50) & (df["Score"] < 70)]))
col4.metric("Urgent Attention", len(df[df["Score"] < 50]))

st.divider()

# ---------------------------
# TABS
# ---------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 All Drivers",
    "⚠️ Needs Attention",
    "🚨 Needs Urgent Attention",
    "👥 Teams"
])

# ---------------------------
# TAB 1 — ALL DRIVERS
# ---------------------------
with tab1:

    for i, row in df.sort_values("Score", ascending=False).iterrows():

        col1, col2, col3 = st.columns([3,2,2])

        with col1:
            st.markdown(f"**{row['Driver']}**")
            st.caption(f"{row['Team']} | Score: {row['Score']}")

        with col2:
            st.caption(f"Hours: {row['Hours Online']} | Trips: {row['Trips Taken']}")

        with col3:
            if st.button("Generate Message", key=f"a{i}"):

                remaining = get_remaining_targets(
                    row["Hours Online"],
                    row["Trips Taken"],
                    row["Confirmation Rate"],
                    row["Cancellation Rate"],
                    week_info["progress"]
                )

                msg = generate_whatsapp_message(
                    row["Driver"],
                    row["Score"],
                    row["Status"],
                    remaining,
                    week_info,
                    row
                )

                st.text_area("Message", msg, key=f"m{i}")

        st.divider()

    # -------- PDF BUTTON --------
    if st.button("📄 Download Fleet PDF"):
        pdf = generate_fleet_pdf(df)
        st.download_button(
            "Download Fleet Report",
            pdf,
            "fleet_report.pdf"
        )

# ---------------------------
# TAB 2 — NEEDS ATTENTION
# ---------------------------
with tab2:

    df_att = df[df["Score"] < 70]

    for i, row in df_att.iterrows():
        st.write(f"{row['Driver']} — {row['Score']}")

# ---------------------------
# TAB 3 — URGENT
# ---------------------------
with tab3:

    df_urgent = df[df["Score"] < 50]

    for _, row in df_urgent.iterrows():
        st.error(f"{row['Driver']} — {row['Score']}")

# ---------------------------
# TAB 4 — TEAMS
# ---------------------------
with tab4:

    team_names = list(TEAMS.keys())
    selected_team = st.selectbox("Select Team", team_names)

    team_df = df[df["Team"] == selected_team]

    st.subheader(selected_team)

    for _, row in team_df.iterrows():
        st.write(f"{row['Driver']} — {row['Score']}")

    # TEAM PDF
    if st.button("📄 Download Team PDF"):
        pdf = generate_team_pdf(team_df, selected_team)
        st.download_button(
            "Download Team Report",
            pdf,
            f"{selected_team}_report.pdf"
        )
