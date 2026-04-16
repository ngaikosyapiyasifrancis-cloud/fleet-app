# teams.py
# Team rosters + SBV master driver list

# ── SBV MASTER LIST (from Vehicle_List_Cleaned.xlsx) ─────────────────────────
# These are all 70 drivers assigned to SBV vehicles.
# Matching is case-insensitive and partial to handle name variations in CSV.
SBV_DRIVERS = [
    "Akimu Soko", "Alfred Sanny Tshabalala", "Alli Mabvuto", "Alnord Nyirenda",
    "Amazing Calvin Servazio", "Andrew Gracious Phiri", "Anthonio Haston Bikausi",
    "Asanda Nyembe", "Blessings Maseko Sinosi", "Brian Chiremba",
    "Brian Losen Mkandla", "Bright Jere", "Chidochase Chitendiso Mbulawa",
    "Davie Staliko", "Desmond Farai Murondi", "Esrom Maswekana",
    "Faidon Safali", "Francis Phwitiko", "Gift Obrey", "Gift Tenyiko Baloyi",
    "Gilbert Babou Marifa", "Godknows Sithole", "Hlayisane Mawelela",
    "Ibrahim Rishard", "Idelito Valexy", "Innocent Grant Chapotera",
    "Ishmael Mussah", "Jacob Murondi", "Jefule Mustafa", "John Msosa",
    "Jolter Sizwe Ndlovu", "Joshua Mtisi", "Junior Ishumeal", "Justin Alli",
    "Kado Genuen", "Kagiso Khoza", "Kago Ramasike", "Katleho Mahane Mahamo",
    "Khulerani Tshabalala", "Kimia Gedeon Beloko", "Lebohang Molefe",
    "Lehlohonolo Lucky Moloi", "Lester Banda", "Loshani Sakisoni",
    "Louis Suntche", "Lucas Inkosinathi Dhlamini", "Matata Samuel Netshandama",
    "Mgcini Moyo", "Mpho Mofokeng", "Nathan Ronald Nanchu", "Nekias Nkiwane",
    "Nelson Zangirai", "Ntokozo Godfrey Shwaye", "Paulo Antonio",
    "Percy Mabuza", "Raphael Banda", "Robert Nzuy Ngamuna", "Sabelo Vumasi",
    "Sam Haba", "Samuel German", "Sanele Nkosi", "Siphesihle Mdebuka",
    "Stephen Mohali", "Stiven Banda", "Tebogo Sathekge", "Vincent Tonex",
    "Vumbhoni Owen Mathye", "Vuyisa Mdebuka", "Willard Bakali",
    "Winson Chimfwembe Mwasinga",
]
SBV_TOTAL = len(SBV_DRIVERS)  # 70


def is_sbv_driver(name):
    """
    Returns True if a driver name matches any SBV driver.
    Uses partial case-insensitive matching to handle CSV name variations
    e.g. 'JOLTER NDLOVU' matches 'Jolter Sizwe Ndlovu'.
    """
    name_lower = name.strip().lower()
    for sbv in SBV_DRIVERS:
        sbv_lower = sbv.strip().lower()
        # Match if either name contains the other (handles truncations/variations)
        parts = sbv_lower.split()
        # Check if first + last name of SBV driver both appear in CSV name
        if len(parts) >= 2:
            if parts[0] in name_lower and parts[-1] in name_lower:
                return True
        if sbv_lower in name_lower or name_lower in sbv_lower:
            return True
    return False


def mark_sbv_drivers(df):
    """Adds an 'Is SBV' boolean column to the dataframe."""
    df = df.copy()
    df["Is SBV"] = df["Driver"].apply(is_sbv_driver)
    return df


# ── TEAM ROSTERS ─────────────────────────────────────────────────────────────
TEAMS = {
    "Team BK": {
        "leader": "Haston Bikausi",
        "drivers": [
            "Haston Bikausi", "Joshua Mtisi", "Alnord Nyirenda",
            "Yohane Stiven Banda", "Brian Losen Mkandla", "Raphael Banda",
            "Godknows Sithole", "Desmond Farai Murondi", "Loshani Loshani",
            "John Msosa", "Louis Suntche", "Esrom Maswikana Sekhobana",
            "K Tshabalala", "Alli Mabvuto", "Paul Moffat",
            "Asanda Nyembe", "Innocent Grant Chapotera",
        ],
    },
    "Team SV": {
        "leader": "Sabelo Vumasi",
        "drivers": [
            "Sabelo Vumasi","BLESSINGS ZUZE", "Siphesihle Mdebuka", "Mgcini Moyo",
            "Vinicent Tonex", "Gilbert Babou Kapanda", "Idelito Valexy",
            "Matata Samuel Netshandama", "Robert Nzuy Ngamuna",
            "Davie Nkhoma Staliko", "Samuel German", "Kado Genuen",
            "Willard Bakali", "Sam Haba", "Jacob Murondi",
            "Chidochase Chitendiso Mbulawa",
        ],
    },
    "Team SS": {
        "leader": "Stephen Mohali",
        "drivers": [
            "Stephen Mohali","Ramsey Mdumuka", "Sanele Sydwell Nkosi", "Nathan Ronald Nanchu",
            "Lebohang Molefe", "Sakhele Siboniso Percy Mabuza",
            "Lucas Inkosinathi Dhlamini", "Katleho Mahase Mahamo",
            "Lehlohonolo Lucky-Boy Moloi", "Nekias Nkiwane", "Vuyisa Mdebuka",
            "Junior Ishumeal", "Amazing Calvin Servazio",
            "Vumbhoni Owen Mathye", "Mpho Mofokeng", "Brian Chiremba",
        ],
    },
    "Team LB": {
        "leader": "Lester Gilamoto Banda",
        "drivers": [
            "Lester Gilamoto Banda","MPENDULO INNOCENT MPILA","Vusi Rodgers Mtwiche", "Bright Jere", "Jolter Ndlovu",
            "Nelson Zangirai", "Francis Phwitiko", "Jefule Mustafa",
            "Winson Mwasinga", "Paulo Antonio", "Akimu Soko",
            "Ishmael Mussah", "Faidon Safali", "Ibrahim Rishard",
            "Anele Sithole", "Hlayisane Makhuneni Mawelela",
            "Alfred Sanny Tshabalala",
        ],
    },
}


def get_team_for_driver(driver_name):
    """Returns the team name for a given driver. Case-insensitive."""
    name_lower = driver_name.strip().lower()
    for team_name, team_data in TEAMS.items():
        for d in team_data["drivers"]:
            if d.strip().lower() == name_lower:
                return team_name
    return "Unassigned"


def match_drivers_to_teams(df):
    """Adds a 'Team' column to the dataframe."""
    df = df.copy()
    df["Team"] = df["Driver"].apply(get_team_for_driver)
    return df


def is_sbv_driver_dynamic(name, sbv_list):
    """
    Same as is_sbv_driver but uses a dynamic list instead of the hardcoded one.
    Used when the user uploads a new Vehicle List Excel to override the default.
    """
    name_lower = name.strip().lower()
    for sbv in sbv_list:
        sbv_lower = str(sbv).strip().lower()
        parts = sbv_lower.split()
        if len(parts) >= 2:
            if parts[0] in name_lower and parts[-1] in name_lower:
                return True
        if sbv_lower in name_lower or name_lower in sbv_lower:
            return True
    return False
