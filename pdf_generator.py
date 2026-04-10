from fpdf import FPDF
from datetime import datetime

# --- BRAND COLOURS (RGB) ---
DARK_BLUE  = (15,  32,  39)
MID_BLUE   = (32,  58,  67)
WHITE      = (255, 255, 255)
BLACK      = (0,   0,   0)
GREEN      = (0,  140,  70)
RED        = (200,  30,  30)
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
        f"Generated: {datetime.now().strftime('%d %b %Y  %H:%M')}  |  Page {pdf.page_no()}",
        align="C"
    )


# ─────────────────────────────────────────────
# PDF 1 - FULL FLEET REPORT (CLEANED)
# ─────────────────────────────────────────────
def generate_fleet_pdf(df, week_label=""):
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.add_page()

    subtitle = f"Weekly KPI Report  |  {week_label}"
    _header(pdf, "WEEKLY FLEET KPI REPORT", subtitle)

    # Table header (REMOVED Team + Score)
    cols = [
        ("#",            10),
        ("Driver Name", 70),
        ("Hours",       30),
        ("Accept %",    30),
        ("Cancel %",    30),
        ("Trips",       25),
        ("KPI Met?",    30),
    ]

    pdf.set_fill_color(*DARK_BLUE)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_x(8)

    for label, w in cols:
        pdf.cell(w, 8, label, align="C", fill=True)
    pdf.ln()

    # Rows
    sorted_df = df.sort_values("Driver").reset_index(drop=True)

    for i, row in sorted_df.iterrows():
        kpi = (
            row["Hours Online"] >= 50 and
            row["Confirmation Rate"] >= 0.80 and
            row["Cancellation Rate"] <= 0.05 and
            row["Trips Taken"] >= 30
        )

        pdf.set_fill_color(*(LIGHT_GREY if i % 2 == 0 else WHITE))
        pdf.set_x(8)

        cells = [
            (str(i + 1),                                      10, "C"),
            (str(row["Driver"])[:40],                         70, "L"),
            (f"{round(row['Hours Online'], 1)}h",             30, "C"),
            (f"{round(row['Confirmation Rate'] * 100)}%",     30, "C"),
            (f"{round(row['Cancellation Rate'] * 100)}%",     30, "C"),
            (str(int(row["Trips Taken"])),                    25, "C"),
            ("YES" if kpi else "NO",                          30, "C"),
        ]

        for j, (val, w, align) in enumerate(cells):
            if j == 6:  # KPI column
                pdf.set_text_color(*(GREEN if kpi else RED))
                pdf.set_font("Helvetica", "B", 10)
            else:
                pdf.set_text_color(*BLACK)
                pdf.set_font("Helvetica", "", 9)

            pdf.cell(w, 7, val, align=align, fill=True)

        pdf.ln()

    _footer(pdf)
    return bytearray(pdf.output())


# ─────────────────────────────────────────────
# PDF 2 - TEAM REPORT (ONE PAGE + BIG KPI)
# ─────────────────────────────────────────────
def generate_team_pdf(team_name, leader_name, team_df, week_label=""):
    pdf = FPDF(orientation="P", unit="mm", format="A4")

    # ❗ Disable auto page break → force ONE PAGE
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()

    title = f"{team_name.upper()} - KPI TRACKER"
    subtitle = f"Leader: {leader_name}  |  {week_label}"
    _header(pdf, title, subtitle)

    cols = [
        ("#",           10),
        ("Driver Name", 80),
        ("Hours",       20),
        ("AR %",        20),
        ("CR %",        20),
        ("Trips",       15),
        ("KPI",         20),
    ]

    pdf.set_fill_color(*DARK_BLUE)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_x(8)

    for label, w in cols:
        pdf.cell(w, 8, label, align="C", fill=True)
    pdf.ln()

    sorted_team = team_df.sort_values("Driver").reset_index(drop=True)

    for i, row in sorted_team.iterrows():
        kpi = (
            row["Hours Online"] >= 50 and
            row["Confirmation Rate"] >= 0.80 and
            row["Cancellation Rate"] <= 0.05 and
            row["Trips Taken"] >= 30
        )

        pdf.set_fill_color(*(LIGHT_GREY if i % 2 == 0 else WHITE))
        pdf.set_x(8)

        cells = [
            (str(i + 1),                                     10, "C"),
            (str(row["Driver"])[:35],                        80, "L"),
            (f"{round(row['Hours Online'], 1)}h",            20, "C"),
            (f"{round(row['Confirmation Rate'] * 100)}%",    20, "C"),
            (f"{round(row['Cancellation Rate'] * 100)}%",    20, "C"),
            (str(int(row["Trips Taken"])),                   15, "C"),
            ("YES" if kpi else "NO",                         20, "C"),
        ]

        for j, (val, w, align) in enumerate(cells):
            if j == 6:  # KPI column → BIG + COLOR
                pdf.set_text_color(*(GREEN if kpi else RED))
                pdf.set_font("Helvetica", "B", 12)
            else:
                pdf.set_text_color(*BLACK)
                pdf.set_font("Helvetica", "", 9)

            pdf.cell(w, 8, val, align=align, fill=True)

        pdf.ln()

    _footer(pdf)
    return bytearray(pdf.output())
