import os
import requests

CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI")

API_BASE = "https://discord.com/api"


def get_login_url():

    return (
        f"{API_BASE}/oauth2/authorize"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=identify guilds"
    )


def exchange_code(code):

    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    r = requests.post(
        f"{API_BASE}/oauth2/token",
        data=data,
        headers=headers
    )

    return r.json()


def get_user(token):

    headers = {
        "Authorization": f"Bearer {token}"
    }

    r = requests.get(
        f"{API_BASE}/users/@me",
        headers=headers
    )

    return r.json()

print("CLIENT_ID:", CLIENT_ID)
print("REDIRECT:", REDIRECT_URI)