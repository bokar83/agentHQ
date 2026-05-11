"""
gws_auth_setup.py — OAuth credential setup for agentsHQ Gmail accounts.

Run this locally to generate credentials for any Gmail account.
The output JSON goes in secrets/ and gets SCP'd to the VPS.

Usage:
    python scripts/gws_auth_setup.py --account bokar83
    python scripts/gws_auth_setup.py --account catalystworks

Requirements:
    pip install google-auth-oauthlib

You need the client_secrets.json from Google Cloud Console:
    1. Go to https://console.cloud.google.com/apis/credentials
    2. Click your OAuth 2.0 Desktop client
    3. Download JSON → save as secrets/client_secrets.json
"""

import argparse
import json
import os
import sys

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.settings.basic",
    "https://www.googleapis.com/auth/gmail.settings.sharing",
    "https://www.googleapis.com/auth/calendar",
]

ACCOUNT_MAP = {
    "bokar83": {
        "email": "bokar83@gmail.com",
        "output_file": "secrets/gws-oauth-credentials.json",
    },
    "catalystworks": {
        "email": "catalystworks.ai@gmail.com",
        "output_file": "secrets/gws-oauth-credentials-cw.json",
    },
}


def main():
    parser = argparse.ArgumentParser(description="Generate GWS OAuth credentials for agentsHQ.")
    parser.add_argument(
        "--account",
        required=True,
        choices=list(ACCOUNT_MAP.keys()),
        help="Which account to authorize.",
    )
    parser.add_argument(
        "--client-secrets",
        default="secrets/client_secrets.json",
        help="Path to client_secrets.json downloaded from Google Cloud Console.",
    )
    args = parser.parse_args()

    account = ACCOUNT_MAP[args.account]

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print("ERROR: google-auth-oauthlib not installed.")
        print("Run: pip install google-auth-oauthlib")
        sys.exit(1)

    if not os.path.exists(args.client_secrets):
        print(f"ERROR: client_secrets.json not found at {args.client_secrets}")
        print("Download it from: https://console.cloud.google.com/apis/credentials")
        print("Click your OAuth 2.0 Desktop client → Download JSON")
        print(f"Save it as: {args.client_secrets}")
        sys.exit(1)

    print(f"\nAuthorizing account: {account['email']}")
    print("A browser window will open. Sign in as that account and grant access.\n")

    flow = InstalledAppFlow.from_client_secrets_file(args.client_secrets, SCOPES)
    creds = flow.run_local_server(port=0)

    output = {
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "refresh_token": creds.refresh_token,
        "token_uri": "https://oauth2.googleapis.com/token",
        "scopes": SCOPES,
        "account_email": account["email"],
    }

    os.makedirs("secrets", exist_ok=True)
    with open(account["output_file"], "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nCredentials saved to: {account['output_file']}")
    print("\nNext step — SCP to VPS:")
    print(f"  scp {account['output_file']} root@72.60.209.109:/root/agentHQ/{account['output_file']}")
    print("\nThen restart the orchestrator:")
    print("  ssh root@72.60.209.109 'cd /root/agentHQ && docker compose restart orchestrator'")


if __name__ == "__main__":
    main()
