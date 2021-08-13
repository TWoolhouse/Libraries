import json
import os.path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

def obtain_oauth(token: str, client_secret: str, scope: list[str]) -> Credentials:
    c = None
    if os.path.exists(token):
        with open(token, "r", encoding="utf8") as file:
            data = json.load(file)
        if data["scope"] == scope:
            c = Credentials.from_authorized_user_info(data["token"], scope)

    if c is None or not c.valid:
        if c and c.expired and c.refresh_token:
            c.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", scope)
            c = flow.run_local_server(port=0)
        with open(token, "w", encoding="utf8") as file:
            data = {
                "scope": scope,
                "token": json.loads(c.to_json()),
            }
            json.dump(data, file)

    return c
