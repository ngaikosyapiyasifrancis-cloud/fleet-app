# app.py
# SparklingBlu Moto — Weekly Driver Performance Tracker (SBV Integrated)

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
# LOAD SBV FILE (YOUR BACKEND LIST)
# ─────────────────────────────────────────────
@st.cache_data
def load_sbv_list():
    df = pd.read_excel("Vehicle_List_Cleaned (1) (1).xlsx")
    
    # 🔥 IMPORTANT: adjust column name if needed
    # assuming column contains driver names
    df["Driver_clean"] = df.iloc[:,0].astype(str).str.lower().str.strip()
    df["Driver"] = df.iloc[:,0]
    
    return df[["Driver", "Driver_clean"]]

# ─────────────────────────────────────────────
# ENCODE / DECODE
# ─────────────────────────────────────────────
def encode_data(df):
    raw = df.to_json(orient="records")
    compressed = gzip.compress(raw.encode("utf-8"))
    return base64.urlsafe_b64encode(compressed).decode("utf-8")

def decode_data(encoded):
    compressed = base64.urlsafe_b64decode(encoded.encode("utf-8"))
    raw = gzip.decompress(compressed).decode("utf-8")
    return pd.DataFrame(json.loads(raw))

def make_link(view, df, team=None):
    base = st.secrets.get("APP_URL","https://your-app-url.streamlit.app")
    encoded = encode_data(df)
    params = {"view": view, "data": encoded}
    if team:
        params["team"] = team
    return f"{base}/?{urllib.parse.urlencode(params)}"

# ─────────────────────────────────────────────
# PROCESS DF
# ─────────────────────────────────────────────
def process_df(df):
    week_info = get_week_progress()

    scores, statuses, coachings = [], [], []
    hrs_needed, trps_needed = [], []
    ar_ok_list, cr_ok_list, hrs_ok_list, trps_ok_list = [], [], [], []

    for _, row in df.iterrows():
        rem = get_remaining_targets(
            row["Hours Online"], row["Trips Taken"],
            row["Confirmation Rate"], row["Cancellation Rate"],
            week_info["progress"]
        )

        score = calculate_performance_score(
            row["Confirmation Rate"], row["Cancellation Rate"],
            row["Trips / hr"], row["Earnings / hr"],
            row["Hours Online"], row["Trips Taken"],
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
    df["Score"] = scores
    df["Status"] = statuses
    df["Coaching"] = coachings
    df["Hours Needed"] = hrs_needed
    df["Trips Needed"] = trps_needed
    df["AR On Track"] = ar_ok_list
    df["CR On Track"] = cr_ok_list
    df["Hours On Track"] = hrs_ok_list
    df["Trips On Track"] = trps_ok_list

    df["KPI Met"] = (
        (df["Hours Online"] >= 50) &
        (df["Confirmation Rate"] >= 0.80) &
        (df["Cancellation Rate"] <= 0.05) &
        (df["Trips Taken"] >= 30)
    )

    return df, week_info


def fmt_rate(val):
    try:
        return f"{round(float(val)*100)}%"
    except:
        return str(val)

# ─────────────────────────────────────────────
# ROUTING
# ─────────────────────────────────────────────
params = st.query_params
view = params.get("view", "admin")
data = params.get("data", None)

# ═══════════════════════════════════════════
# ADMIN VIEW
# ═══════════════════════════════════════════
if view == "admin":

    st.title("🚛 SparklingBlu Dashboard (SBV Enabled)")

    uploaded = st.file_uploader("Upload Uber CSV", type=["csv"])
    if uploaded is None:
        st.stop()

    raw_df = pd.read_csv(uploaded)

    raw_df["Driver"] = raw_df["Driver first name"] + " " + raw_df["Driver surname"]
    raw_df = match_drivers_to_teams(raw_df)

    df, week_info = process_df(raw_df)

    # ─────────────────────────────
    # SBV MATCHING
    # ─────────────────────────────
    sbv_df = load_sbv_list()

    df["Driver_clean"] = df["Driver"].str.lower().str.strip()

    active_sbv = df[df["Driver_clean"].isin(sbv_df["Driver_clean"])]
    missing_sbv = sbv_df[~sbv_df["Driver_clean"].isin(df["Driver_clean"])]

    total_sbv = len(sbv_df)
    active_count = len(active_sbv)
    coverage_pct = round((active_count / total_sbv)*100,1) if total_sbv else 0

    # ─────────────────────────────
    # DISPLAY SBV STATS
    # ─────────────────────────────
    st.subheader("🚛 SBV Fleet Coverage")

    c1, c2, c3 = st.columns(3)
    c1.metric("Total SBV Bikes", total_sbv)
    c2.metric("Active SBV Drivers", f"{active_count}/{total_sbv}")
    c3.metric("Coverage", f"{coverage_pct}%")

    st.divider()

    # Missing drivers
    st.subheader("⚠️ SBV Drivers Not Online")

    if missing_sbv.empty:
        st.success("All SBV drivers are online ✅")
    else:
        st.warning(f"{len(missing_sbv)} drivers missing")

        st.dataframe(
            missing_sbv[["Driver"]],
            use_container_width=True,
            hide_index=True
        )

    st.divider()

    # ─────────────────────────────
    # NORMAL SYSTEM CONTINUES
    # ─────────────────────────────
    st.subheader("Fleet Overview")

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Drivers", len(df))
    c2.metric("Top Performers", len(df[df["Score"] >= 85]))
    c3.metric("Urgent", len(df[df["Score"] < 50]))

    st.divider()

    # LINKS
    lean_df = df.copy()

    st.subheader("Links")

    drivers_link = make_link("drivers", lean_df)
    fleet_link = make_link("fleet", lean_df)

    st.code(drivers_link)
    st.code(fleet_link)

# ═══════════════════════════════════════════
# DRIVERS VIEW
# ═══════════════════════════════════════════
elif view == "drivers" and data:

    df = decode_data(data)

    st.title("📱 Driver View")

    name = st.text_input("Search your name")

    if not name:
        st.stop()

    match = df[df["Driver"].str.lower().str.contains(name.lower())]

    if match.empty:
        st.warning("No driver found")
        st.stop()

    row = match.iloc[0]

    st.metric("Score", row["Score"])
    st.write(row["Coaching"])

# ═══════════════════════════════════════════
# FLEET VIEW
# ═══════════════════════════════════════════
elif view == "fleet" and data:

    df = decode_data(data)

    st.title("📊 Fleet View")

    st.dataframe(df)

# ═══════════════════════════════════════════
# FALLBACK
# ═══════════════════════════════════════════
else:
    st.error("Invalid link")
