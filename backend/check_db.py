from sqlalchemy import text

if __package__:
    from .app.db.database import get_engine
else:
    from app.db.database import get_engine


def main():
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1")).scalar_one()
    except Exception:
        # Connection errors can include credentials; keep command output generic.
        print("Database connection failed. Check DATABASE_URL in backend/.env and network access.")
        return 1
    print("Connected to Neon PostgreSQL successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
