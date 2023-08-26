from __future__ import annotations

from typing import NamedTuple


class ClientCreds(NamedTuple):
    client_id: str
    client_secret: str


class UserAuth(NamedTuple):
    access_token: str
    refresh_token: str
    expires_in: int
    expires_at: float
