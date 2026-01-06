#!/usr/bin/env pipenv-shebang
import contextlib
import sqlite3
import sys

import dateparser

import leaderboards


def main(argv):
    if len(argv) not in (2, 3):
        print(f"usage: {argv[0]} <file> [<date>]", file=sys.stderr)
        sys.exit(1)

    with contextlib.closing(sqlite3.connect(argv[1])) as conn:
        with contextlib.closing(conn.cursor()) as cursor:
            if argv[2:]:
                date = dateparser.parse(argv[2]).date().isoformat()
            else:
                res = cursor.execute(
                    "SELECT date FROM leaderboards ORDER BY date DESC LIMIT 1"
                )
                row = res.fetchone()
                if not row:
                    return
                (date,) = row

            print(
                leaderboards.format_message(
                    date, leaderboards.scores_for_date(cursor, date)
                )
            )


if __name__ == "__main__":
    main(sys.argv)
