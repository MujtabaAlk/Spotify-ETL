from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy import Table
from sqlalchemy import Column
from sqlalchemy import BigInteger
from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String

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
