# teams.py
# Defines all fleet teams, their leaders, and driver rosters.
# Update this file whenever team membership changes.

TEAMS = {
    "Team BK": {
        "leader": "Haston Bikausi",
        "drivers": [
            "Haston Bikausi",
            "Joshua Mtisi",
            "Alnord Nyirenda",
            "Yohane Stiven Banda",
            "Brian Losen Mkandla",
            "Raphael Banda",
            "Godknows Sithole",
            "Desmond Farai Murondi",
            "Loshani Loshani",
            "John Msosa",
            "Louis Suntche",
            "Esrom Maswikana Sekhobana",
            "K Tshabalala",
            "Alli Mabvuto",
            "Paul Moffat",
            "Asanda Nyembe",
            "Innocent Grant Chapotera",
        ],
    },
    "Team SV": {
        "leader": "Sabelo Vumasi",
        "drivers": [
            "Sabelo Vumasi",
            "Siphesihle Mdebuka",
            "Mgcini Moyo",
            "Vinicent Tonex",
            "Gilbert Babou Kapanda",
            "Idelito Valexy",
            "Matata Samuel Netshandama",
            "Robert Nzuy Ngamuna",
            "Davie Nkhoma Staliko",
            "Samuel German",
            "Kado Genuen",
            "Willard Bakali",
            "Sam Haba",
            "Jacob Murondi",
            "Chidochase Chitendiso Mbulawa",
        ],
    },
    "Team SS": {
        "leader": "Stephen Mohali",
        "drivers": [
            "Stephen Mohali",
            "Sanele Sydwell Nkosi",
            "Nathan Ronald Nanchu",
            "Lebohang Molefe",
            "Sakhele Siboniso Percy Mabuza",
            "Lucas Inkosinathi Dhlamini",
            "Katleho Mahase Mahamo",
            "Lehlohonolo Lucky-Boy Moloi",
            "Nekias Nkiwane",
            "Vuyisa Mdebuka",
            "Junior Ishumeal",
            "Amazing Calvin Servazio",
            "Vumbhoni Owen Mathye",
            "Mpho Mofokeng",
            "Brian Chiremba",
        ],
    },
    "Team LB": {
        "leader": "Lester Gilamoto Banda",
        "drivers": [
            "Lester Gilamoto Banda",
            "Bright Jere",
            "Jolter Ndlovu",
            "Nelson Zangirai",
            "Francis Phwitiko",
            "Jefule Mustafa",
            "Winson Mwasinga",
            "Paulo Antonio",
            "Akimu Soko",
            "Ishmael Mussah",
            "Faidon Safali",
            "Ibrahim Rishard",
            "Anele Sithole",
            "Hlayisane Makhuneni Mawelela",
            "Alfred Sanny Tshabalala",
        ],
    },
}


def get_team_for_driver(driver_name):
    """
    Returns the team name for a given driver, or 'Unassigned' if not found.
    Uses case-insensitive matching to handle CSV name inconsistencies.
    """
    name_lower = driver_name.strip().lower()
    for team_name, team_data in TEAMS.items():
        for d in team_data["drivers"]:
            if d.strip().lower() == name_lower:
                return team_name
    return "Unassigned"


def match_drivers_to_teams(df):
    """
    Adds a 'Team' column to the dataframe by matching driver names to teams.

    Parameters:
    - df : pandas DataFrame with a 'Driver' column

    Returns:
    - df with a new 'Team' column
    """
    df = df.copy()
    df["Team"] = df["Driver"].apply(get_team_for_driver)
    return df
