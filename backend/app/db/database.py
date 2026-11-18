import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import declarative_base, sessionmaker


load_dotenv(Path(__file__).resolve().parents[2] / ".env")

Base = declarative_base()


@lru_cache(maxsize=1)
def get_engine():
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("Set DATABASE_URL in backend/.env before connecting.")

    # Explicitly use the installed psycopg2 driver for Neon PostgreSQL URLs.
    url = make_url(database_url)
    if url.drivername not in ("postgres", "postgresql", "postgresql+psycopg2"):
        raise RuntimeError("DATABASE_URL must be a PostgreSQL connection URL.")
    url = url.set(drivername="postgresql+psycopg2")
    if "sslmode" not in url.query:
        url = url.update_query_dict({"sslmode": "require"})

    return create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 10})


@lru_cache(maxsize=1)
def get_session_factory():
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)


def get_db():
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
