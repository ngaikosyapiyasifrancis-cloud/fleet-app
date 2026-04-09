# app.py
# Fleet Performance & Coaching System

import streamlit as st
import pandas as pd
from engine import (
    calculate_performance_score,
    get_coaching_message,
    get_week_progress,
    get_remaining_targets,
    generate_whatsapp_message,
)

# --- PAGE SETUP ---
st.set_page_config(
    page_title="Fleet Performance System",
    page_icon="🚛",
    layout="wide"
)

# --- HEADER ---
st.title("🚛 Fleet Performance & Coaching System")
st.caption("SparklingBlu Moto — Weekly Driver Performance Tracker")
st.divider()

# --- WEEK PROGRESS ---
week_info = get_week_progress()

st.info(
    f"📅 {week_info['day_name']} | "
    f"⏳ {round(week_info['progress']*100,1)}% of week done | "
    f"📆 {week_info['days_left']} day(s) left"
)

# --- FILE UPLOAD ---
uploaded_file = st.file_uploader("📂 Upload Uber CSV", type=["csv"])

if uploaded_file is None:
    st.warning("Upload your CSV to start.")
    st.stop()

# --- READ DATA ---
df = pd.read_csv(uploaded_file)
df["Driver"] = df["Driver first name"] + " " + df["Driver surname"]

# --- CALCULATIONS ---
scores, statuses, messages = [], [], []

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

df["Score"] = scores
df["Status"] = statuses
df["Coaching Message"] = messages

# --- SUMMARY ---
st.subheader("📊 Fleet Summary")
col1, col2, col3 = st.columns(3)

col1.metric("Drivers", len(df))
col2.metric("Avg Score", round(df["Score"].mean(), 1))
col3.metric("Needs Attention", len(df[df["Score"] < 70]))

st.divider()

# --- TABS ---
tab1, tab2, tab3 = st.tabs([
    "📊 All Drivers",
    "🚨 Needs Attention",
    "🌟 Top Performers"
])

# ==============================
# TAB 1 — ALL DRIVERS
# ==============================
with tab1:

    st.subheader("All Drivers")

    for i, row in df.sort_values("Score", ascending=False).iterrows():

        with st.container():

            col1, col2, col3 = st.columns([3, 2, 2])

            # DRIVER INFO
            with col1:
                st.markdown(f"### {row['Driver']}")
                st.caption(f"Score: {round(row['Score'],1)} | {row['Status']}")

            # STATS
            with col2:
                st.write(f"⏱ Hours: {row['Hours Online']}")
                st.write(f"🚗 Trips: {row['Trips Taken']}")
                st.write(f"✅ AR: {round(row['Confirmation Rate']*100,1)}%")
                st.write(f"❌ CR: {round(row['Cancellation Rate']*100,1)}%")

            # BUTTON
            with col3:

                if st.button("Generate Message", key=f"btn_{i}"):

                    remaining = get_remaining_targets(
                        hours_online=row["Hours Online"],
                        trips_taken=row["Trips Taken"],
                        confirmation_rate=row["Confirmation Rate"],
                        cancellation_rate=row["Cancellation Rate"],
                        progress=week_info["progress"]
                    )

                    msg = generate_whatsapp_message(
                        driver_name=row["Driver"],
                        score=row["Score"],
                        status=row["Status"],
                        remaining=remaining,
                        week_info=week_info,
                        row=row,
                        language="english"
                    )

                    st.text_area(
                        "Copy Message",
                        msg,
                        height=250,
                        key=f"text_{i}"
                    )

            st.divider()

# ==============================
# TAB 2 — NEEDS ATTENTION
# ==============================
with tab2:

    st.subheader("Drivers Needing Attention")

    attention_df = df[df["Score"] < 70].sort_values("Score")

    if attention_df.empty:
        st.success("All drivers performing well!")
    else:
        for i, row in attention_df.iterrows():

            with st.container():

                col1, col2 = st.columns([3, 1])

                with col1:
                    st.write(f"⚠️ {row['Driver']} — Score: {round(row['Score'],1)}")

                with col2:
                    if st.button("Message", key=f"alert_{i}"):

                        remaining = get_remaining_targets(
                            hours_online=row["Hours Online"],
                            trips_taken=row["Trips Taken"],
                            confirmation_rate=row["Confirmation Rate"],
                            cancellation_rate=row["Cancellation Rate"],
                            progress=week_info["progress"]
                        )

                        msg = generate_whatsapp_message(
                            driver_name=row["Driver"],
                            score=row["Score"],
                            status=row["Status"],
                            remaining=remaining,
                            week_info=week_info,
                            row=row,
                            language="english"
                        )

                        st.text_area("Message", msg, key=f"alert_text_{i}")

# ==============================
# TAB 3 — TOP PERFORMERS
# ==============================
with tab3:

    st.subheader("Top Performers")

    top_df = df[df["Score"] >= 85].sort_values("Score", ascending=False)

    if top_df.empty:
        st.info("No top performers yet.")
    else:
        for _, row in top_df.iterrows():
            st.success(f"🌟 {row['Driver']} — Score: {round(row['Score'],1)}")

# --- DOWNLOAD ---
st.divider()

csv = df.sort_values("Score", ascending=False).to_csv(index=False).encode("utf-8")

st.download_button(
    "⬇️ Download Report",
    csv,
    "fleet_report.csv",
    "text/csv"
)
