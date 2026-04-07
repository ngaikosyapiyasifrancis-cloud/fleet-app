# app.py
# This is the dashboard — what you see in your browser.
# It uses Streamlit to display driver performance data in a table.

import streamlit as st
import pandas as pd
from engine import calculate_performance_score, get_coaching_message

# --- PAGE SETUP ---
st.set_page_config(page_title="Fleet Performance System", page_icon="🚛")

st.title("🚛 Fleet Performance & Coaching System")
st.write("Monitor your drivers and get coaching recommendations.")

# --- MOCK DATA ---
# This is fake data to test the app. Later you can replace this with real data.
drivers = [
    {"name": "John Mokoena",  "on_time_rate": 92, "fuel_efficiency": 13.5, "safety_incidents": 0},
    {"name": "Sipho Dlamini", "on_time_rate": 75, "fuel_efficiency": 11.0, "safety_incidents": 1},
    {"name": "Thabo Nkosi",   "on_time_rate": 60, "fuel_efficiency": 9.5,  "safety_incidents": 2},
    {"name": "Lerato Molete", "on_time_rate": 88, "fuel_efficiency": 14.0, "safety_incidents": 0},
    {"name": "Bongani Zulu",  "on_time_rate": 45, "fuel_efficiency": 8.0,  "safety_incidents": 3},
]

# --- CALCULATE SCORES ---
# Loop through each driver and calculate their score and coaching message
for driver in drivers:
    driver["score"] = calculate_performance_score(
        driver["on_time_rate"],
        driver["fuel_efficiency"],
        driver["safety_incidents"]
    )
    driver["coaching"] = get_coaching_message(driver["score"])

# --- BUILD TABLE ---
# Convert the list of drivers into a Pandas DataFrame (a table)
df = pd.DataFrame(drivers)

# Rename columns to look nice on screen
df.columns = ["Driver", "On-Time %", "Fuel (km/L)", "Incidents", "Score", "Coaching Message"]

# --- DISPLAY TABLE ---
st.subheader("📊 Driver Performance Overview")
st.dataframe(df, use_container_width=True)

# --- SUMMARY NUMBERS ---
st.subheader("📈 Summary")
col1, col2, col3 = st.columns(3)
col1.metric("Total Drivers", len(df))
col2.metric("Avg Score", round(df["Score"].mean(), 1))
col3.metric("Top Driver", df.loc[df["Score"].idxmax(), "Driver"])
