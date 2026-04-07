# app.py
# The dashboard for the Fleet Performance & Coaching System.
# Reads a real Uber CSV file uploaded by the user.

import streamlit as st
import pandas as pd
from engine import calculate_performance_score, get_coaching_message

# --- PAGE SETUP ---
st.set_page_config(page_title="Fleet Performance System", page_icon="🚛", layout="wide")

st.title("🚛 Fleet Performance & Coaching System")
st.write("Upload your Uber driver report to see performance scores and coaching messages.")

# --- FILE UPLOAD ---
uploaded_file = st.file_uploader("📂 Upload your Uber CSV file", type=["csv"])

if uploaded_file is None:
    # Show a friendly message if no file uploaded yet
    st.info("👆 Please upload your Uber driver CSV file to get started.")
    st.stop()

# --- READ THE CSV ---
df = pd.read_csv(uploaded_file)

# --- CALCULATE SCORES ---
scores = []
statuses = []
messages = []

for _, row in df.iterrows():
    score = calculate_performance_score(
        confirmation_rate=row["Confirmation Rate"],
        cancellation_rate=row["Cancellation Rate"],
        trips_per_hr=row["Trips / hr"],
        earnings_per_hr=row["Earnings / hr"]
    )
    status, message = get_coaching_message(score)
    scores.append(score)
    statuses.append(status)
    messages.append(message)

df["Score"]             = scores
df["Status"]            = statuses
df["Coaching Message"]  = messages

# --- FULL NAME COLUMN ---
df["Driver"] = df["Driver first name"] + " " + df["Driver surname"]

# --- SUMMARY METRICS ---
st.subheader("📈 Summary")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Drivers",  len(df))
col2.metric("Avg Score",      round(df["Score"].mean(), 1))
col3.metric("Top Performer",  df.loc[df["Score"].idxmax(), "Driver"])
col4.metric("Needs Attention",len(df[df["Score"] < 50]))

st.divider()

# --- FILTER ---
st.subheader("🔍 Filter Drivers")
status_options = ["All"] + sorted(df["Status"].unique().tolist())
selected_status = st.selectbox("Filter by Status:", status_options)

if selected_status != "All":
    filtered_df = df[df["Status"] == selected_status]
else:
    filtered_df = df

# --- DISPLAY TABLE ---
st.subheader(f"📊 Driver Performance Overview ({len(filtered_df)} drivers)")

display_cols = [
    "Driver",
    "Trips Taken",
    "Trips / hr",
    "Earnings / hr",
    "Confirmation Rate",
    "Cancellation Rate",
    "Score",
    "Status",
    "Coaching Message"
]

st.dataframe(filtered_df[display_cols].sort_values("Score", ascending=False),
             use_container_width=True)

st.divider()

# --- DOWNLOAD REPORT ---
st.subheader("📥 Download Coaching Report")

csv_export = filtered_df[display_cols].sort_values("Score", ascending=False)
csv_data = csv_export.to_csv(index=False).encode("utf-8")

st.download_button(
    label="⬇️ Download Report as CSV",
    data=csv_data,
    file_name="fleet_coaching_report.csv",
    mime="text/csv"
)
