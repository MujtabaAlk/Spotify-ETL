from __future__ import annotations

from typing import TypedDict


class AccessTokenResponse(TypedDict):
    access_token: str
    expires_in: int
    refresh_token: str
