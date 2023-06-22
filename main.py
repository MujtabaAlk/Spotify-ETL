from __future__ import annotations

import base64
import json
import logging
import secrets
import webbrowser
from datetime import datetime
from datetime import timedelta
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from urllib import parse

import httpx

from data import ClientCreds
from data import UserAuth


class AuthServer(HTTPServer):
    code: str
    state: str


class AuthRequestHandler(BaseHTTPRequestHandler):
    server: AuthServer

    def _generate_response(self, status_code: int, template_path: str) -> None:
        self.send_response(status_code)
        self.end_headers()
        with open(template_path) as file:
            content = file.read()

        self.wfile.write(content.encode())

    def do_GET(self) -> None:
        parsed_path = parse.urlparse(self.path)
        query = parse.parse_qs(parsed_path.query)
        query_state = query.get("state")
        query_code = query.get("code")

        # Request failiar
        if query_state is None or len(query_state) < 1:
            return self._generate_response(400, "error.html")

        # State value missmach
        if self.server.state != query_state[0]:
            return self._generate_response(400, "error.html")

        # Auth Api did not autharize
        if query_code is None or len(query_code) < 1:
            logging.error(
                f"Authorization code requet erorr: {query.get('error')}"
            )
            return self._generate_response(401, "error.html")

        self.server.code = query_code[0]

        return self._generate_response(200, "index.html")


def get_authorization_code(client_creds: ClientCreds) -> str | None:
    scope = "user-read-email"
    redirect_uri = "http://127.0.0.1:9090/"
    state = secrets.token_urlsafe(16)

    query_params = {
        "client_id": client_creds.client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "state": state,
        "scope": scope,
    }

    auth_url = "https://accounts.spotify.com/authorize?" + parse.urlencode(
        query_params
    )

    server = AuthServer(("0.0.0.0", 9090), AuthRequestHandler)
    server.state = state
    logging.info("Waiting for request...")
    webbrowser.open(auth_url)
    server.handle_request()
    logging.info("Request handled.")
    logging.info(f"Returned Code value: {server.code=}")

    return server.code


def get_user_access_token(
    client_creds: ClientCreds, auth_code: str
) -> UserAuth | None:
    # request body
    grant_type = "authorization_code"
    redirect_uri = "http://127.0.0.1:9090/"
    # request headers
    content_type = "application/x-www-form-urlencoded"
    client_b64 = base64.b64encode(
        f"{client_creds.client_id}:{client_creds.client_secret}".encode(
            "ascii"
        )
    ).decode("ascii")

    response = httpx.post(
        "https://accounts.spotify.com/api/token",
        headers={
            "Authorization": f"Basic {client_b64}",
            "Content-Type": content_type,
        },
        data={
            "grant_type": grant_type,
            "code": auth_code,
            "redirect_uri": redirect_uri,
        },
    )

    if response.status_code != 200:
        logging.error("Unable to obtain access token")
        return None

    response_data = response.json()
    access_token: str = response_data.get("access_token")
    expires_in: int = response_data.get("expires_in")
    refresh_token: str = response_data.get("refresh_token")

    expires_in_dt = datetime.utcnow() + timedelta(seconds=expires_in)
    return UserAuth(access_token, refresh_token, expires_in_dt)


def main() -> int:
    print("Hey Hi, Hello!")
    # logging.getLogger().setLevel(logging.INFO)

    # Load Creds
    with open("client_credentials.json") as file:
        client_creds = ClientCreds(**json.load(file))

    # Get authorization code
    auth_code = get_authorization_code(client_creds)
    if auth_code is None or auth_code == "":
        logging.error("Unable to get authorization code")
        return -1

    # Get access token
    user_access_token = get_user_access_token(client_creds, auth_code)
    if user_access_token is None:
        logging.error("Unable to get access token")
        return -1

    # Request profile data
    profile_response = httpx.get(
        "https://api.spotify.com/v1/me",
        headers={"Authorization": f"Bearer {user_access_token.access_token}"},
    )

    if profile_response.status_code != 200:
        logging.error(f"status code: {profile_response.status_code}")

    print(profile_response.json())

    with open("response_data.json", mode="w+") as file:
        json.dump(profile_response.json(), file, indent=4)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
