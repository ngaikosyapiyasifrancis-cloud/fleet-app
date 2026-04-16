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

# (ALL YOUR CSS REMAINS EXACTLY THE SAME — unchanged)
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

    uploaded = st.file_uploader("Upload Uber CSV", type=["csv"])
    report_days = st.number_input("Days this CSV covers", min_value=1, max_value=7, value=1)

    if uploaded is None:
        st.stop()

    raw = pd.read_csv(uploaded)
    raw["Driver"] = raw["Driver first name"] + " " + raw["Driver surname"]
    raw = match_drivers_to_teams(raw)
    raw = mark_sbv_drivers(raw)

    scores, statuses = [], []

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

        status, _ = get_coaching_message(score, rem, week_info)

        scores.append(score)
        statuses.append(status)

    raw["Score"] = scores
    raw["Status"] = statuses

    df = raw.copy()

    # ✅ CHANGE: removed Daily Hrs Avg from display
    st.dataframe(df[[
        "Driver","Team","Is SBV","Hours Online",
        "Trips Taken","Score","Status"
    ]])


# ════════════════════════════════════════════
# DRIVERS VIEW
# ════════════════════════════════════════════
elif view == "drivers":
    data = load_fleet_data()

    if not data:
        st.stop()

    df = pd.DataFrame(data["fleet"])

    search = st.text_input("Type your name:")
    if not search:
        st.stop()

    match = df[df["Driver"].str.lower().str.contains(search.lower())]

    if match.empty:
        st.warning("No driver found")
        st.stop()

    row = match.iloc[0]

    st.metric("Score", row["Score"])

    # ✅ CHANGE HERE ONLY
    st.metric(
        "Weekly Hours",
        f"{row['Hours Online']}h",
        "Target: 50h/week"
    )


# ════════════════════════════════════════════
# FLEET VIEW
# ════════════════════════════════════════════
elif view == "fleet":
    data = load_fleet_data()

    if not data:
        st.stop()

    df = pd.DataFrame(data["fleet"])

    # ✅ CHANGE HERE ONLY
    low_hrs = (df["Hours Online"].astype(float) < 50).sum()
    st.metric("Drivers Below 50h/week", low_hrs)

    st.dataframe(df[[
        "Driver","Hours Online","Trips Taken","Score"
    ]])


# ════════════════════════════════════════════
# TEAM VIEW
# ════════════════════════════════════════════
elif view == "team":
    data = load_fleet_data()

    if not data:
        st.stop()

    df = pd.DataFrame(data["fleet"])

    team = st.selectbox("Select team", list(TEAMS.keys()))
    team_df = df[df["Team"] == team]

    # ✅ CHANGE HERE ONLY
    st.dataframe(team_df[[
        "Driver","Hours Online","Trips Taken","Score"
    ]])
