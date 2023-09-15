from __future__ import annotations
import json

from sqlalchemy import create_engine

from data import AppConfig
from database import meta


def main() -> int:
    with open("config.json") as file:
        app_config = AppConfig(**json.load(file))
    engine = create_engine(app_config.database_url)
    meta.create_all(engine)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
