from __future__ import annotations

from datetime import datetime
from typing import TypedDict

from sqlalchemy import MetaData
from sqlalchemy import Table
from sqlalchemy import Column
from sqlalchemy import BigInteger
from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String

from response_data import RecentlyPlayedItem

meta = MetaData()
SongTable = Table(
    "recently_played_song",
    meta,
    Column("timestamp", BigInteger(), primary_key=True),
    Column("id", String(32)),
    Column("name", String(256)),
    Column("artist", String(256)),
    Column("album", String(256)),
    Column("played_at", DateTime()),
    Column("popularity", Integer()),
    Column("explicit", Boolean()),
)


class SongDBMapping(TypedDict):
    """
    Dictionary structure used for database queries
    on SongTable
    """

    timestamp: int
    id: str
    name: str
    artist: str
    album: str
    played_at: datetime
    popularity: int
    explicit: bool


def map_song_items(item: RecentlyPlayedItem) -> SongDBMapping:
    played_at_str = item["played_at"]

    # replace utc symbol for compatibility
    if played_at_str.endswith(("Z", "z")):
        played_at_str = played_at_str[:-1] + "+00:00"

    played_at = datetime.fromisoformat(played_at_str)
    timestamp = int(played_at.timestamp() * 1000)
    song_id = item["track"]["id"]
    song_name = item["track"]["name"]
    artist = ", ".join([a["name"] for a in item["track"]["artists"]])
    album = item["track"]["album"]["name"]
    popularity = item["track"]["popularity"]
    explicit = item["track"]["explicit"]

    return {
        "timestamp": timestamp,
        "id": song_id,
        "name": song_name,
        "artist": artist,
        "album": album,
        "played_at": played_at,
        "popularity": popularity,
        "explicit": explicit,
    }
