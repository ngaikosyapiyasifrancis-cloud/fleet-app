# storage.py
# Handles saving and loading fleet data using GitHub Gist.
# This gives us persistent, auto-updating links.
# Data is stored as JSON in a private GitHub Gist.

import json
import requests
import streamlit as st


def _headers():
    token = st.secrets.get("GITHUB_TOKEN", "")
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }


def save_fleet_data(data_dict):
    """
    Saves fleet data to the GitHub Gist defined in Streamlit secrets.
    data_dict should contain keys like 'fleet', 'week_info', 'week_label'.

    Returns True on success, False on failure.
    """
    gist_id = st.secrets.get("GIST_ID", "")
    if not gist_id:
        st.error("GIST_ID not set in Streamlit secrets. See setup instructions.")
        return False

    payload = {
        "description": "SparklingBlu Fleet Data - auto updated",
        "files": {
            "fleet_data.json": {
                "content": json.dumps(data_dict, default=str)
            }
        }
    }

    resp = requests.patch(
        f"https://api.github.com/gists/{gist_id}",
        headers=_headers(),
        json=payload,
        timeout=10
    )

    return resp.status_code == 200


def load_fleet_data():
    """
    Loads the latest fleet data from the GitHub Gist.
    Returns a dict on success, or None if unavailable.
    """
    gist_id = st.secrets.get("GIST_ID", "")
    if not gist_id:
        return None

    resp = requests.get(
        f"https://api.github.com/gists/{gist_id}",
        headers=_headers(),
        timeout=10
    )

    if resp.status_code != 200:
        return None

    try:
        content = resp.json()["files"]["fleet_data.json"]["content"]
        return json.loads(content)
    except Exception:
        return None


def is_storage_configured():
    """Returns True if both GITHUB_TOKEN and GIST_ID are set in secrets."""
    return bool(st.secrets.get("GITHUB_TOKEN")) and bool(st.secrets.get("GIST_ID"))
