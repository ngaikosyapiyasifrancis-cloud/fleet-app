# SparklingBlu Moto Fleet Performance Tracker
# =============================================

## Overview

A Streamlit-based driver performance tracking system that replaces PDF reports with shareable links. Drivers, team leaders, and management can access their stats anytime via unique URLs.

## Features

- **CSV Upload** — Upload Uber driver data and process instantly
- **Shareable Links** — Generate URLs for drivers, teams, and management
- **Real-time Stats** — Drivers see their KPIs and remaining targets
- **Team Management** — View team performance and compliance
- **Fleet Overview** — Management dashboard with insights and search
- **Data Backup** — Export processed data for historical tracking
- **Error Handling** — Graceful handling of corrupted/invalid links
- **Data Freshness** — Shows when data was last generated

## Setup Instructions

### 1. Requirements

- Python 3.10+
- Streamlit Cloud account (free)

### 2. Files Required

Copy these 3 files to your GitHub repository:

```
app.py      — Main application
engine.py   — Scoring and calculation logic
teams.py    — Team configuration
```

### 3. Deploy to Streamlit Cloud

1. Create a GitHub repository
2. Push the 3 files above
3. Go to [share.streamlit.io](https://share.streamlit.io)
4. Connect your GitHub repo
5. Deploy!

### 4. Configure Secrets

In Streamlit Cloud:

1. Go to your app settings → Secrets
2. Add your deployed app URL:
   ```
   APP_URL = https://your-app-name.streamlit.app
   ```

### 5. Update Teams

Edit `teams.py` to add/remove drivers or change team assignments. The file is heavily commented for easy editing.

## Workflow

### Admin (You)
1. Download CSV from Uber dashboard
2. Upload to the app
3. Copy generated links
4. Share via WhatsApp

### Drivers
1. Click the driver link
2. Search for their name
3. View their stats and targets

### Team Leaders
1. Click the team link
2. View team performance
3. Identify drivers needing coaching

### Management
1. Click the management link
2. View fleet-wide insights
3. Search any driver's stats

## File Structure

```
/
├── app.py          # Main Streamlit app (all views)
├── engine.py       # Scoring algorithms
├── teams.py        # Team configuration
├── README.md       # This file
└── .streamlit/
    └── config.toml # Streamlit settings (optional)
```

## Updating Teams

Open `teams.py` and edit the `TEAMS` dictionary:

```python
TEAMS = {
    "Team BK": {
        "leader": "Leader Name",
        "drivers": ["Driver One", "Driver Two"],
    },
    # Add more teams...
}
```

## Troubleshooting

### Links not working?
Make sure `APP_URL` is set in Streamlit secrets.

### Driver not found?
Check spelling in `teams.py` — matching is case-insensitive.

### Data looks old?
Links contain snapshot data. Generate new links weekly.

## Support

For issues or feature requests, contact your fleet manager.
