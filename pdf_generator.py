# pdf_generator.py
# Generates two types of PDFs:
# 1. Fleet-wide KPI report  (all drivers)
# 2. Team KPI compliance tracker (one team at a time)

from fpdf import FPDF
from datetime import datetime

# --- BRAND COLOURS (RGB) ---
DARK_BLUE  = (15,  32,  39)
MID_BLUE   = (32,  58,  67)
WHITE      = (255, 255, 255)
BLACK      = (0,   0,   0)
GREEN      = (0,  140,  70)
RED        = (200,  30,  30)
AMBER      = (200, 130,   0)
LIGHT_GREY = (240, 245, 248)


def _header(pdf, title, subtitle=""):
    pdf.set_fill_color(*DARK_BLUE)
    pdf.rect(0, 0, pdf.w, 24, "F")
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_xy(8, 6)
    pdf.cell(0, 7, "SPARKLINGBLU MOTO  |  " + title)
    if subtitle:
        pdf.set_font("Helvetica", "", 8)
        pdf.set_xy(8, 15)
        pdf.cell(0, 5, subtitle)
    pdf.set_text_color(*BLACK)
    pdf.ln(18)


def _footer(pdf):
    pdf.set_y(-12)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(130, 130, 130)
    pdf.cell(
        0, 5,
        f"Generated: {datetime.now().strftime('%d %b %Y  %H:%M')}  |  "
        f"SparklingBlu Moto Fleet System  |  Page {pdf.page_no()}",
        align="C"
    )


# ─────────────────────────────────────────────
# PDF 1 - FULL FLEET REPORT
# ─────────────────────────────────────────────
def generate_fleet_pdf(df, week_label=""):
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.add_page()

    subtitle = (f"Weekly KPI Report  |  {week_label}  |  "
                f"Targets: >=50h  |  >=80% AR  |  <=5% CR  |  >=30 Trips")
    _header(pdf, "WEEKLY FLEET KPI REPORT", subtitle)

    # Summary bar
    total     = len(df)
    compliant = len(df[
        (df["Hours Online"]      >= 50)   &
        (df["Confirmation Rate"] >= 0.80) &
        (df["Cancellation Rate"] <= 0.05) &
        (df["Trips Taken"]       >= 30)
    ])
    pct = round((compliant / total) * 100) if total else 0

    pdf.set_fill_color(*MID_BLUE)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_x(8)
    for label in [f"Total Drivers: {total}",
                  f"KPI Compliant: {compliant}",
                  f"Fleet Compliance Rate: {pct}%"]:
        pdf.cell(62, 8, label, fill=True, align="C")
        pdf.cell(3)
    pdf.ln(12)

    # Table header
    cols = [
        ("#",            8),
        ("Team",        24),
        ("Driver Name", 58),
        ("Hours",       20),
        ("Accept %",    22),
        ("Cancel %",    22),
        ("Trips",       16),
        ("Score",       18),
        ("KPI Met?",    20),
    ]
    pdf.set_fill_color(*DARK_BLUE)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_x(8)
    for label, w in cols:
        pdf.cell(w, 7, label, align="C", fill=True)
    pdf.ln()

    # Rows
    sorted_df = df.sort_values(["Team", "Driver"]).reset_index(drop=True)
    for i, row in sorted_df.iterrows():
        kpi = (row["Hours Online"]      >= 50   and
               row["Confirmation Rate"] >= 0.80 and
               row["Cancellation Rate"] <= 0.05 and
               row["Trips Taken"]       >= 30)

        pdf.set_fill_color(*(LIGHT_GREY if i % 2 == 0 else WHITE))
        pdf.set_x(8)

        cells = [
            (str(i + 1),                                      8,  "C"),
            (str(row.get("Team", ""))[:16],                  24,  "C"),
            (str(row["Driver"])[:32],                        58,  "L"),
            (f"{round(row['Hours Online'], 1)}h",             20, "C"),
            (f"{round(row['Confirmation Rate'] * 100)}%",     22, "C"),
            (f"{round(row['Cancellation Rate'] * 100)}%",     22, "C"),
            (str(int(row["Trips Taken"])),                    16, "C"),
            (str(row["Score"]),                               18, "C"),
            ("YES" if kpi else "NO",                          20, "C"),
        ]

        for j, (val, w, align) in enumerate(cells):
            if j == 8:
                pdf.set_text_color(*(GREEN if kpi else RED))
                pdf.set_font("Helvetica", "B", 8)
            else:
                pdf.set_text_color(*BLACK)
                pdf.set_font("Helvetica", "", 8)
            pdf.cell(w, 6, val, align=align, fill=True)
        pdf.ln()

    # Team compliance summary
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*DARK_BLUE)
    pdf.set_x(8)
    pdf.cell(0, 6, "TEAM COMPLIANCE SUMMARY", ln=True)

    for team_name in sorted(df["Team"].dropna().unique()):
        t_df    = df[df["Team"] == team_name]
        t_total = len(t_df)
        t_comp  = len(t_df[
            (t_df["Hours Online"]      >= 50)   &
            (t_df["Confirmation Rate"] >= 0.80) &
            (t_df["Cancellation Rate"] <= 0.05) &
            (t_df["Trips Taken"]       >= 30)
        ])
        t_pct   = round((t_comp / t_total) * 100) if t_total else 0
        color   = GREEN if t_pct >= 50 else (AMBER if t_pct >= 25 else RED)

        pdf.set_x(8)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*BLACK)
        pdf.cell(50, 5, team_name)
        pdf.cell(35, 5, f"{t_comp} / {t_total} compliant")
        pdf.set_text_color(*color)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(20, 5, f"{t_pct}%")
        pdf.ln()

    _footer(pdf)
    return bytes(pdf.output())


# ─────────────────────────────────────────────
# PDF 2 - TEAM KPI COMPLIANCE TRACKER
# ─────────────────────────────────────────────
def generate_team_pdf(team_name, leader_name, team_df, week_label=""):
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.add_page()

    title    = f"{team_name.upper()} - KPI COMPLIANCE TRACKER"
    subtitle = (f"Leader: {leader_name}  |  {week_label}  |  "
                f"Targets: >=50h  |  >=80% AR  |  <=5% CR  |  >=30 Trips")
    _header(pdf, title, subtitle)

    # Table header
    cols = [
        ("#",           10),
        ("Driver Name", 74),
        ("Hours",       22),
        ("Accept %",    24),
        ("Cancel %",    24),
        ("Trips",       20),
        ("Score",       20),
        ("KPI Met?",    22),
    ]
    pdf.set_fill_color(*DARK_BLUE)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_x(8)
    for label, w in cols:
        pdf.cell(w, 8, label, align="C", fill=True)
    pdf.ln()

    # Rows
    sorted_team   = team_df.sort_values("Score", ascending=False).reset_index(drop=True)
    compliant_cnt = 0

    for i, row in sorted_team.iterrows():
        kpi = (row["Hours Online"]      >= 50   and
               row["Confirmation Rate"] >= 0.80 and
               row["Cancellation Rate"] <= 0.05 and
               row["Trips Taken"]       >= 30)
        if kpi:
            compliant_cnt += 1

        is_leader = row["Driver"].strip().lower() == leader_name.strip().lower()
        pdf.set_fill_color(*(LIGHT_GREY if i % 2 == 0 else WHITE))
        pdf.set_x(8)

        name_display = ("* " if is_leader else "  ") + str(row["Driver"])[:30]

        cells = [
            (str(i + 1),                                     10, "C"),
            (name_display,                                   74, "L"),
            (f"{round(row['Hours Online'], 1)}h",            22, "C"),
            (f"{round(row['Confirmation Rate'] * 100)}%",    24, "C"),
            (f"{round(row['Cancellation Rate'] * 100)}%",    24, "C"),
            (str(int(row["Trips Taken"])),                   20, "C"),
            (str(row["Score"]),                              20, "C"),
            ("YES" if kpi else "NO",                         22, "C"),
        ]

        for j, (val, w, align) in enumerate(cells):
            if j == 7:
                pdf.set_text_color(*(GREEN if kpi else RED))
                pdf.set_font("Helvetica", "B", 9)
            elif j == 1 and is_leader:
                pdf.set_text_color(*DARK_BLUE)
                pdf.set_font("Helvetica", "B", 9)
            else:
                pdf.set_text_color(*BLACK)
                pdf.set_font("Helvetica", "", 9)
            pdf.cell(w, 7, val, align=align, fill=True)
        pdf.ln()

    # Compliance summary bar
    total     = len(sorted_team)
    pct       = round((compliant_cnt / total) * 100) if total else 0
    bar_color = GREEN if pct >= 50 else (AMBER if pct >= 25 else RED)

    pdf.ln(5)
    pdf.set_fill_color(*bar_color)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_x(8)
    pdf.cell(
        0, 10,
        f"  COMPLIANT THIS WEEK: {compliant_cnt} / {total}        "
        f"{pct}% Team Compliance Rate",
        fill=True
    )

    _footer(pdf)
    return bytes(pdf.output())
