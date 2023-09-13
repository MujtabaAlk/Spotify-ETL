from __future__ import annotations

from sqlalchemy import create_engine

from database import meta


def main() -> int:
    engine = create_engine("sqlite:///data.db")
    meta.create_all(engine)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
