#!/usr/bin/env python3
"""
get_google_token.py — One-Time Google OAuth Token Generator
============================================================
Module: 04-youtube-publishing

Generates a token.json file containing Google OAuth2 refresh credentials
for Google Drive and YouTube upload. This script only needs to run ONCE.

Usage:
    python get_google_token.py

The script reads Client ID and Client Secret from environment variables
or from the project .env file. After authorizing in the browser, it saves
the generated token to token.json in the current directory.

Dependencies:
    pip install google-auth-oauthlib google-api-python-client google-auth-httplib2
"""

import os
import sys
import json
import pathlib

# Try to import oauthlib, guide the user to install it if missing
try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("Error: The 'google-auth-oauthlib' package is not installed.")
    print("Please install it by running the following command in your terminal:")
    print("👉 pip install google-auth-oauthlib google-api-python-client google-auth-httplib2")
    sys.exit(1)

# Scopes for Google Drive and YouTube
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/youtube.upload'
]


def _find_env_file():
    """Walk up from the script directory to find the nearest .env file."""
    search = pathlib.Path(__file__).parent.resolve()
    for _ in range(10):
        candidate = search / ".env"
        if candidate.exists():
            return candidate
        parent = search.parent
        if parent == search:
            break
        search = parent
    return None


def _load_env():
    """Load .env file into os.environ (existing vars take priority)."""
    env_file = _find_env_file()
    if env_file is None:
        return
    with open(env_file, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key not in os.environ:
                os.environ[key] = val


def main():
    print("=========================================================")
    print("      Google API Authorization Generator")
    print("=========================================================")

    # Load .env to get credentials
    _load_env()

    # Read Client ID and Secret from environment variables (never hardcode!)
    client_id = os.environ.get("GOOGLE_CLIENT_ID_B", "")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET_B", "")

    if not client_id or not client_secret:
        print("\n[ERROR] Google OAuth credentials not found!")
        print("Set these environment variables (or add them to .env):")
        print("  GOOGLE_CLIENT_ID_B=your_client_id_here")
        print("  GOOGLE_CLIENT_SECRET_B=your_client_secret_here")
        print("\nGet them from: console.cloud.google.com → APIs & Services → Credentials")
        sys.exit(1)

    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost:8080/"]
        }
    }

    # Run the authorization flow using local server on port 8080
    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    print("\nStarting local authentication server on port 8080...")
    print("A browser window will open automatically. Please authorize the app with your YouTube account.")
    print("---------------------------------------------------------")

    try:
        # Force prompt='consent' and access_type='offline' to guarantee a refresh_token is returned
        creds = flow.run_local_server(port=8080, prompt='consent', access_type='offline')

        # Save the credentials to token.json
        creds_dict = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': list(creds.scopes) if creds.scopes else list(SCOPES)
        }

        with open('token.json', 'w') as token_file:
            json.dump(creds_dict, token_file, indent=2)

        print("---------------------------------------------------------")
        print("\nSUCCESS! token.json has been created in this folder.")
        print("What to do next:")
        print("1. Open 'token.json' file using Notepad.")
        print("2. Copy all of its text content.")
        print("3. Paste it into your GitHub Repository Secrets as 'GOOGLE_TOKEN_JSON'.")
    except Exception as e:
        print(f"\nAuthentication Failed: {e}")
        print("Please check your client ID and secret settings.")

if __name__ == '__main__':
    main()
