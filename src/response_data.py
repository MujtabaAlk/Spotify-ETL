from __future__ import annotations

from typing import TypedDict


class AccessTokenResponse(TypedDict):
    access_token: str
    expires_in: int
    refresh_token: str


class RecentlyPlayedResponse(TypedDict):
    next: str | None
    cursors: RecentlyPlayedCursors
    items: list[RecentlyPlayedItem]


class RecentlyPlayedCursors(TypedDict):
    after: str
    before: str


class RecentlyPlayedItem(TypedDict):
    track: _RecentlyPlayedItemTrack
    played_at: str


class _RecentlyPlayedItemTrack(TypedDict):
    album: _TrackAlbum
    artists: list[_TrackArtist]
    duration_ms: int
    explicit: bool
    external_urls: _ResponseExternalUrls
    href: str
    id: str
    name: str
    popularity: int
    uri: str


class _TrackAlbum(TypedDict):
    total_tracks: int
    external_urls: _ResponseExternalUrls
    href: str
    id: str
    name: str
    release_date: str
    uri: str


class _TrackArtist(TypedDict):
    external_urls: _ResponseExternalUrls
    href: str
    id: str
    name: str
    uri: str


class _ResponseExternalUrls(TypedDict):
    spotify: str
