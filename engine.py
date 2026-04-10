# engine.py
# The brain of the Fleet Performance & Coaching System.
# Scores and coaches drivers based on weekly targets and how far into the week we are.

from datetime import datetime, timezone

# --- WEEKLY TARGETS ---
WEEKLY_TARGETS = {
    "hours":        50.0,   # minimum hours online per week
    "acceptance":   0.80,   # minimum acceptance rate (80%)
    "cancellation": 0.05,   # maximum cancellation rate (5%)
    "trips":        30,     # minimum trips per week
}


def get_week_progress():
    """
    Works out how far through the current week we are (Monday=0 to Sunday=6).
    The week runs Monday 00:00 to Sunday 23:59.

    Returns:
    - day_number   : 0 = Monday, 6 = Sunday
    - day_name     : e.g. "Wednesday"
    - progress     : fraction of week elapsed e.g. 0.43 means 43% through the week
    - days_elapsed : how many full days have passed e.g. 3
    - days_left    : how many days remain e.g. 4
    """
    now = datetime.now()
    day_number  = now.weekday()          # Monday=0, Sunday=6
    day_name    = now.strftime("%A")     # e.g. "Wednesday"
    hour        = now.hour

    # Progress = days elapsed + fraction of current day
    days_elapsed = day_number + (hour / 24)
    progress     = days_elapsed / 7

    days_left = 6 - day_number  # full days remaining after today

    return {
        "day_number":   day_number,
        "day_name":     day_name,
        "progress":     round(progress, 4),
        "days_elapsed": round(days_elapsed, 2),
        "days_left":    days_left,
    }


def get_prorated_targets(progress):
    """
    Calculates how much of each target a driver should have achieved by now.

    For example: if it's Wednesday afternoon and progress=0.43
    - Expected hours so far: 50 * 0.43 = 21.5 hrs
    - Expected trips so far: 30 * 0.43 = 12.9 trips

    Note: Rates (AR, CR) are not pro-rated — they apply at all times.

    Returns a dict of expected values so far this week.
    """
    return {
        "hours":    round(WEEKLY_TARGETS["hours"]  * progress, 1),
        "trips":    round(WEEKLY_TARGETS["trips"]  * progress, 1),
        "acceptance":   WEEKLY_TARGETS["acceptance"],    # rate — always applies
        "cancellation": WEEKLY_TARGETS["cancellation"],  # rate — always applies
    }


def calculate_performance_score(confirmation_rate, cancellation_rate, trips_per_hr,
                                  earnings_per_hr, hours_online, trips_taken, progress):
    """
    Calculates a performance score (0 to 100) adjusted for week progress.

    Parameters:
    - confirmation_rate  : acceptance rate        (e.g. 0.96)
    - cancellation_rate  : cancellation rate      (e.g. 0.02)
    - trips_per_hr       : trips per hour         (e.g. 1.5)
    - earnings_per_hr    : rands earned per hour  (e.g. 13.50)
    - hours_online       : total hours online     (e.g. 22.5)
    - trips_taken        : total trips completed  (e.g. 18)
    - progress           : how far through week   (e.g. 0.43)

    Returns:
    - score between 0 and 100
    """

    # --- COMPONENT 1: Acceptance Rate (30%) ---
    # Must be above 80% at all times
    ar_score = (confirmation_rate / WEEKLY_TARGETS["acceptance"]) * 100
    ar_score = min(ar_score, 100) * 0.30

    # --- COMPONENT 2: Cancellation Rate (25%) ---
    # Must stay at or below 5%
    if cancellation_rate <= WEEKLY_TARGETS["cancellation"]:
        cr_score = 100
    else:
        # Each % above 5% costs 20 points
        excess = (cancellation_rate - WEEKLY_TARGETS["cancellation"]) * 100
        cr_score = max(100 - (excess * 20), 0)
    cr_score = cr_score * 0.25

    # --- COMPONENT 3: Hours Progress (25%) ---
    # Compare actual hours to expected hours at this point in the week
    expected_hours = WEEKLY_TARGETS["hours"] * max(progress, 0.01)
    hours_score = min((hours_online / expected_hours) * 100, 100) * 0.25

    # --- COMPONENT 4: Trips Progress (20%) ---
    # Compare actual trips to expected trips at this point in the week
    expected_trips = WEEKLY_TARGETS["trips"] * max(progress, 0.01)
    trips_score = min((trips_taken / expected_trips) * 100, 100) * 0.20

    total_score = ar_score + cr_score + hours_score + trips_score
    return round(total_score, 1)


def get_remaining_targets(hours_online, trips_taken, confirmation_rate,
                           cancellation_rate, progress):
    """
    Calculates what each driver still needs to achieve by Sunday 23:59.

    Returns a dict with remaining targets and on-track status for each metric.
    """
    remaining = {}

    # Hours still needed
    hours_needed = max(WEEKLY_TARGETS["hours"] - hours_online, 0)
    remaining["hours_needed"]    = round(hours_needed, 1)
    remaining["hours_on_track"]  = hours_online >= (WEEKLY_TARGETS["hours"] * progress)

    # Trips still needed
    trips_needed = max(WEEKLY_TARGETS["trips"] - trips_taken, 0)
    remaining["trips_needed"]    = int(trips_needed)
    remaining["trips_on_track"]  = trips_taken >= (WEEKLY_TARGETS["trips"] * progress)

    # Acceptance rate status
    remaining["ar_on_track"]     = confirmation_rate >= WEEKLY_TARGETS["acceptance"]
    remaining["ar_gap"]          = round(max(WEEKLY_TARGETS["acceptance"] - confirmation_rate, 0) * 100, 1)

    # Cancellation rate status
    remaining["cr_on_track"]     = cancellation_rate <= WEEKLY_TARGETS["cancellation"]
    remaining["cr_gap"]          = round(max(cancellation_rate - WEEKLY_TARGETS["cancellation"], 0) * 100, 1)

    return remaining


def get_coaching_message(score, remaining, week_info):
    """
    Returns a status label and a personalised coaching message based on:
    - The driver's score
    - What they still need to achieve
    - What day of the week it is

    Returns:
    - (status, message)
    """
    day_name  = week_info["day_name"]
    days_left = week_info["days_left"]

    # Build a list of specific issues
    issues = []
    if not remaining["hours_on_track"]:
        issues.append(f"{remaining['hours_needed']} more hours online needed")
    if not remaining["trips_on_track"]:
        issues.append(f"{remaining['trips_needed']} more trips needed")
    if not remaining["ar_on_track"]:
        issues.append(f"Acceptance Rate is {remaining['ar_gap']}% below the 80% minimum")
    if not remaining["cr_on_track"]:
        issues.append(f"Cancellation Rate is {remaining['cr_gap']}% above the 5% maximum")

    issue_text = " | ".join(issues) if issues else "All targets on track ✅"

    if score >= 85:
        status  = "🌟 Top Performer"
        message = f"Excellent work this {day_name}! You are ahead of your weekly targets. {issue_text}"
    elif score >= 70:
        status  = "✅ Good"
        message = f"Good progress. {days_left} day(s) left to finish strong. {issue_text}"
    elif score >= 50:
        status  = "⚠️ Needs Improvement"
        message = f"You are falling behind. Only {days_left} day(s) left this week. {issue_text}"
    else:
        status  = "🚨 Urgent Attention"
        message = f"Critical — urgent action needed before Sunday. {days_left} day(s) left. {issue_text}"

    return (status, message)


# ---------------------------------------------------------------------------
# WHATSAPP MESSAGE GENERATOR
# ---------------------------------------------------------------------------

def generate_whatsapp_message(driver_name, score, status, remaining,
                               week_info, row, language="english"):
    """
    Generates a full WhatsApp message for a driver.

    Parameters:
    - driver_name : full name of the driver
    - score       : performance score (0-100)
    - status      : status label e.g. "🌟 Top Performer"
    - remaining   : dict from get_remaining_targets()
    - week_info   : dict from get_week_progress()
    - row         : the driver's full data row (pandas Series)
    - language    : "english" or "zulu"

    Returns:
    - A formatted WhatsApp message string
    """

    day_name  = week_info["day_name"]
    days_left = week_info["days_left"]

    # --- Format metrics ---
    ar  = round(row["Confirmation Rate"] * 100, 1)
    cr  = round(row["Cancellation Rate"] * 100, 1)
    hrs = round(row["Hours Online"], 1)
    trp = int(row["Trips Taken"])
    eph = round(row["Earnings / hr"], 2)
    tot = round(row["Total Earnings"], 2)

    # --- Remaining targets ---
    hrs_needed  = remaining["hours_needed"]
    trp_needed  = remaining["trips_needed"]
    ar_ok       = "✅" if remaining["ar_on_track"]  else "❌"
    cr_ok       = "✅" if remaining["cr_on_track"]  else "❌"
    hrs_ok      = "✅" if remaining["hours_on_track"] else "❌"
    trp_ok      = "✅" if remaining["trips_on_track"] else "❌"

    if language == "zulu":
        msg = f"""🚛 *UMBIKO WOKUSEBENZA KWEVIKI*
━━━━━━━━━━━━━━━━━━━━
👤 Umshayeli: *{driver_name}*
📅 Usuku: *{day_name}* | Izinsuku eziShiyiwe: *{days_left}*
⭐ Inombolo Yokusebenza: *{score}/100*
📊 Isimo: *{status}*

━━━━━━━━━━━━━━━━━━━━
📋 *IZINKOMBA ZEVIKI KUZE KUBE MANJE*
━━━━━━━━━━━━━━━━━━━━
⏱️ Amahora Online: *{hrs} hrs* {hrs_ok} _(kudingeka okungenani 50 hrs)_
🚗 Izinhambazime: *{trp} trips* {trp_ok} _(kudingeka okungenani 30 trips)_
✅ Amazinga Wokuqinisekisa: *{ar}%* {ar_ok} _(kufanele abe ngo-80%+)_
❌ Amazinga Okukhansela: *{cr}%* {cr_ok} _(kufanele abe ngaphansi kuka-5%)_
💰 Inzuzo / Ihora: *R{eph}*
💵 Inzuzo Yesamba: *R{tot}*

━━━━━━━━━━━━━━━━━━━━
🎯 *OKUSASELE UKUZE UFINYELELE IZINHLOSO*
━━━━━━━━━━━━━━━━━━━━
⏱️ Amahora asasele: *{hrs_needed} hrs*
🚗 Izinhambazime ezisasele: *{trp_needed} trips*
{'⚠️ Amazinga AR akekho endleleni — gcina ukwamukela amabhukhu!' if not remaining['ar_on_track'] else '✅ AR inhloso ifinyelelwe!'}
{'⚠️ Amazinga CR aphezulu kakhulu — nciphisa ukukhansela!' if not remaining['cr_on_track'] else '✅ CR inhloso ifinyelelwe!'}

━━━━━━━━━━━━━━━━━━━━
💬 *UMLAYEZO WOKUQEQESHA*
━━━━━━━━━━━━━━━━━━━━
Qhubeka usebenza nkumu! Usuku oluhle lokushayela. 🙏
_SparklingBlu Moto Fleet Team_"""

    else:
        msg = f"""🚛 *WEEKLY PERFORMANCE REPORT*
━━━━━━━━━━━━━━━━━━━━
👤 Driver: *{driver_name}*
📅 Day: *{day_name}* | Days Left: *{days_left}*
⭐ Performance Score: *{score}/100*
📊 Status: *{status}*

━━━━━━━━━━━━━━━━━━━━
📋 *THIS WEEK'S METRICS SO FAR*
━━━━━━━━━━━━━━━━━━━━
⏱️ Hours Online: *{hrs} hrs* {hrs_ok} _(min 50 hrs required)_
🚗 Trips Taken: *{trp} trips* {trp_ok} _(min 30 trips required)_
✅ Acceptance Rate: *{ar}%* {ar_ok} _(must be 80%+)_
❌ Cancellation Rate: *{cr}%* {cr_ok} _(must be 5% or below)_
💰 Earnings / hr: *R{eph}*
💵 Total Earnings: *R{tot}*

━━━━━━━━━━━━━━━━━━━━
🎯 *WHAT YOU STILL NEED BY SUNDAY*
━━━━━━━━━━━━━━━━━━━━
⏱️ Hours still needed: *{hrs_needed} hrs*
🚗 Trips still needed: *{trp_needed} trips*
{'⚠️ AR is off track — keep accepting trips!' if not remaining['ar_on_track'] else '✅ AR target met!'}
{'⚠️ CR is too high — reduce cancellations!' if not remaining['cr_on_track'] else '✅ CR target met!'}

━━━━━━━━━━━━━━━━━━━━
💬 *COACHING MESSAGE*
━━━━━━━━━━━━━━━━━━━━
Keep pushing — you've got this! Have a great day on the road. 🙏
_SparklingBlu Moto Fleet Team_"""

    return msg


def generate_bulk_whatsapp_message(df_summary, week_info):
    """
    Generates a single bulk WhatsApp message summarising the whole fleet.

    Parameters:
    - df_summary : pandas DataFrame with Score and Status columns
    - week_info  : dict from get_week_progress()

    Returns:
    - A formatted bulk WhatsApp message string
    """
    day_name    = week_info["day_name"]
    days_left   = week_info["days_left"]
    total       = len(df_summary)
    avg_score   = round(df_summary["Score"].mean(), 1)
    top         = len(df_summary[df_summary["Score"] >= 85])
    good        = len(df_summary[(df_summary["Score"] >= 70) & (df_summary["Score"] < 85)])
    needs_imp   = len(df_summary[(df_summary["Score"] >= 50) & (df_summary["Score"] < 70)])
    urgent      = len(df_summary[df_summary["Score"] < 50])
    top_driver  = df_summary.loc[df_summary["Score"].idxmax(), "Driver"]
    top_score   = df_summary["Score"].max()

    msg = f"""🚛 *SPARKLINGBLU MOTO — FLEET WEEKLY UPDATE*
━━━━━━━━━━━━━━━━━━━━
📅 *{day_name}* | {days_left} day(s) left this week
👥 Total Active Drivers: *{total}*
⭐ Fleet Average Score: *{avg_score}/100*

━━━━━━━━━━━━━━━━━━━━
📊 *PERFORMANCE BREAKDOWN*
━━━━━━━━━━━━━━━━━━━━
🌟 Top Performers  : *{top} drivers*
✅ Good             : *{good} drivers*
⚠️ Needs Improvement: *{needs_imp} drivers*
🚨 Urgent Attention : *{urgent} drivers*

━━━━━━━━━━━━━━━━━━━━
🏆 *DRIVER OF THE WEEK (SO FAR)*
━━━━━━━━━━━━━━━━━━━━
👤 *{top_driver}* with a score of *{top_score}/100* 🎉

━━━━━━━━━━━━━━━━━━━━
💬 Let's finish this week strong!
Targets: 50hrs | 80%+ AR | ≤5% CR | 30+ trips
_SparklingBlu Moto Fleet Team_ 🙏"""

    return msg
