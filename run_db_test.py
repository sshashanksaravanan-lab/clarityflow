# This is a simple script to initialize the database for testing purposes.

from app.db import init_db, DB_PATH

if __name__ == "__main__":
    init_db()
    print(" DB initialized at:", DB_PATH)
