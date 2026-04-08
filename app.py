# app.py
# Fleet Performance & Coaching System
# Time-aware dashboard using real Uber CSV data

import streamlit as st
import pandas as pd
from engine import (
    calculate_performance_score,
    get_coaching_message,
    get_week_progress,
    get_remaining_targets,
)

# --- PAGE SETUP ---
st.set_page_config(
    page_title="Fleet Performance System",
    page_icon="🚛",
    layout="wide"
)

# --- CUSTOM STYLES ---
st.markdown("""
    <style>
        .metric-box {
            background-color: #1e1e2e;
            border-radius: 12px;
            padding: 16px;
            text-align: center;
        }
        .section-title {
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 4px;
        }
        .week-banner {
            background: linear-gradient(90deg, #0f2027, #203a43, #2c5364);
            color: white;
            padding: 14px 20px;
            border-radius: 12px;
            margin-bottom: 20px;
        }
    </style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown("# 🚛 Fleet Performance & Coaching System")
st.markdown("*SparklingBlu Moto — Weekly Driver Performance Tracker*")
st.divider()

# --- WEEK PROGRESS BANNER ---
week_info = get_week_progress()
progress_pct = round(week_info["progress"] * 100, 1)
days_left = week_info["days_left"]
day_name = week_info["day_name"]

st.markdown(f"""
<div class="week-banner">
    📅 Today is <strong>{day_name}</strong> &nbsp;|&nbsp;
    ⏳ Week Progress: <strong>{progress_pct}%</strong> &nbsp;|&nbsp;
    📆 <strong>{days_left} day(s)</strong> remaining until Sunday 23:59 &nbsp;|&nbsp;
    🎯 Weekly Targets: <strong>50+ hrs &nbsp;|&nbsp; 80%+ AR &nbsp;|&nbsp; ≤5% CR &nbsp;|&nbsp; 30+ trips</strong>
</div>
""", unsafe_allow_html=True)

# --- FILE UPLOAD ---
uploaded_file = st.file_uploader("📂 Upload your Uber CSV file", type=["csv"])

if uploaded_file is None:
    st.info("👆 Please upload your Uber driver CSV file to get started.")
    st.stop()

# --- READ CSV ---
df = pd.read_csv(uploaded_file)
df["Driver"] = df["Driver first name"] + " " + df["Driver surname"]

# --- CALCULATE SCORES ---
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

df["Score"]           = scores
df["Status"]          = statuses
df["Coaching Message"] = messages

# --- SUMMARY METRICS ---
st.subheader("📈 Fleet Summary")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("👥 Total Drivers",     len(df))
col2.metric("⭐ Avg Score",          round(df["Score"].mean(), 1))
col3.metric("🌟 Top Performer",      df.loc[df["Score"].idxmax(), "Driver"])
col4.metric("⚠️ Needs Improvement",  len(df[df["Score"] < 70]))
col5.metric("🚨 Urgent Attention",   len(df[df["Score"] < 50]))

st.divider()

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["📊 All Drivers", "🚨 Needs Attention", "🌟 Top Performers"])

display_cols = [
    "Driver", "Hours Online", "Trips Taken",
    "Confirmation Rate", "Cancellation Rate",
    "Earnings / hr", "Score", "Status", "Coaching Message"
]

def format_table(data):
    data = data.copy()
    data["Confirmation Rate"] = (data["Confirmation Rate"] * 100).round(1).astype(str) + "%"
    data["Cancellation Rate"] = (data["Cancellation Rate"] * 100).round(1).astype(str) + "%"
    data["Earnings / hr"]     = "R" + data["Earnings / hr"].round(2).astype(str)
    return data

with tab1:
    # Filter
    status_options = ["All"] + sorted(df["Status"].unique().tolist())
    selected = st.selectbox("Filter by Status:", status_options)
    filtered = df if selected == "All" else df[df["Status"] == selected]
    st.dataframe(
        format_table(filtered[display_cols]).sort_values("Score", ascending=False),
        use_container_width=True, hide_index=True
    )

with tab2:
    attention_df = df[df["Score"] < 70].sort_values("Score", ascending=True)
    if attention_df.empty:
        st.success("✅ All drivers are performing well this week!")
    else:
        st.warning(f"{len(attention_df)} driver(s) need attention.")
        st.dataframe(
            format_table(attention_df[display_cols]),
            use_container_width=True, hide_index=True
        )

with tab3:
    top_df = df[df["Score"] >= 85].sort_values("Score", ascending=False)
    if top_df.empty:
        st.info("No drivers have reached Top Performer status yet this week.")
    else:
        st.success(f"🌟 {len(top_df)} Top Performer(s) this week!")
        st.dataframe(
            format_table(top_df[display_cols]),
            use_container_width=True, hide_index=True
        )

st.divider()

# --- DOWNLOAD REPORT ---
st.subheader("📥 Download Coaching Report")
csv_data = df[display_cols].sort_values("Score", ascending=False).to_csv(index=False).encode("utf-8")
st.download_button(
    label="⬇️ Download Full Report as CSV",
    data=csv_data,
    file_name="fleet_coaching_report.csv",
    mime="text/csv"
)
