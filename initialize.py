import contextlib
import sqlite3
import sys

if len(sys.argv) != 2:
    print(f"usage: {sys.argv[0]} <file>", file=sys.stderr)
    sys.exit(1)

with contextlib.closing(sqlite3.connect(sys.argv[1])) as conn:
    with contextlib.closing(conn.cursor()) as cursor:
        cursor.execute(
            """
      CREATE TABLE leaderboards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        name TEXT,
        time INTEGER,
        updated_ts INTEGER,
        updated_by TEXT,
      );
      """
        )
