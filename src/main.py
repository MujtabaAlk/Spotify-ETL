from __future__ import annotations

import base64
import json
import logging
import secrets
import webbrowser
from datetime import date
from datetime import datetime
from datetime import time
from datetime import timedelta
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from urllib import parse

import httpx
from sqlalchemy import create_engine
from sqlalchemy import insert
from sqlalchemy import select

from data import AppConfig
from data import UserAuth
from database import SongTable
from database import SongDBMapping
from database import map_song_items
from response_data import AccessTokenResponse
from response_data import RecentlyPlayedResponse


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
            return self._generate_response(400, "src/templates/error.html")

        # State value missmach
        if self.server.state != query_state[0]:
            return self._generate_response(400, "src/templates/error.html")

        # Auth Api did not autharize
        if query_code is None or len(query_code) < 1:
            logging.error(
                f"Authorization code requet erorr: {query.get('error')}"
            )
            return self._generate_response(401, "src/templates/error.html")

        self.server.code = query_code[0]

        return self._generate_response(200, "src/templates/index.html")


def get_authorization_code(app_config: AppConfig) -> str | None:
    scope = "user-read-email user-read-recently-played"
    redirect_uri = "http://127.0.0.1:9090/"
    state = secrets.token_urlsafe(16)

    query_params = {
        "client_id": app_config.client_id,
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
    app_config: AppConfig, auth_code: str
) -> UserAuth | None:
    # request body
    grant_type = "authorization_code"
    redirect_uri = "http://127.0.0.1:9090/"
    # request headers
    content_type = "application/x-www-form-urlencoded"
    client_b64 = base64.b64encode(
        f"{app_config.client_id}:{app_config.client_secret}".encode("ascii")
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

    response_data: AccessTokenResponse = response.json()
    access_token = response_data["access_token"]
    expires_in = response_data["expires_in"]
    refresh_token = response_data["refresh_token"]

    expires_at = (
        datetime.utcnow() + timedelta(seconds=expires_in)
    ).timestamp()

    return UserAuth(access_token, refresh_token, expires_in, expires_at)


def main() -> int:
    print("Hey Hi, Hello!")
    # logging.getLogger().setLevel(logging.INFO)

    with open("config.json") as file:
        app_config = AppConfig(**json.load(file))

    # Get authorization code
    auth_code = get_authorization_code(app_config)
    if auth_code is None or auth_code == "":
        logging.error("Unable to get authorization code")
        return -1

    # Get access token
    user_access_token = get_user_access_token(app_config, auth_code)
    if user_access_token is None:
        logging.error("Unable to get access token")
        return -1

    with open("access_token.json", mode="w+") as file:
        json.dump(user_access_token._asdict(), file, indent=4)

    # Request profile data
    profile_response = httpx.get(
        "https://api.spotify.com/v1/me",
        headers={"Authorization": f"Bearer {user_access_token.access_token}"},
    )

    if profile_response.status_code != 200:
        logging.error(
            f"status code: {profile_response.status_code}, on profile request"
        )

    print(profile_response.json())

    # Request recently played song list
    item_limit = 50
    after_ts = int(
        (
            datetime.combine(date.today(), time.min) - timedelta(days=30)
        ).timestamp()
        * 1000
    )

    data_response = httpx.get(
        "https://api.spotify.com/v1/me/player/recently-played",
        headers={"Authorization": f"Bearer {user_access_token.access_token}"},
        params={
            "limit": item_limit,
            "after": after_ts,
        },
    )

    if data_response.status_code != 200:
        logging.error(
            f"status code: {data_response.status_code}, on recently played"
        )

    recently_played_data: RecentlyPlayedResponse = data_response.json()

    engine = create_engine(app_config.database_url)

    with engine.connect() as conn:
        select_stmt = select(SongTable.c.timestamp)

        res = conn.execute(select_stmt)
        timestamp_set: set[int] = {row[0] for row in res.tuples()}

    insert_values: list[SongDBMapping] = []
    for item in recently_played_data["items"]:
        mapped_item = map_song_items(item)
        if mapped_item["timestamp"] not in timestamp_set:
            insert_values.append(mapped_item)

    if len(insert_values) == 0:
        print("No items to insert")
        return 0

    with engine.begin() as conn:
        insert_stmt = insert(SongTable)

        res = conn.execute(insert_stmt, parameters=insert_values)
        inserted_keys = res.inserted_primary_key_rows

    print(f"Inserted {len(inserted_keys)} values")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
