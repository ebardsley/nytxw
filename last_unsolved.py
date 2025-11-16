#!/usr/bin/env pipenv-shebang
import contextlib
import datetime
import os
import pathlib
import pprint
import sqlite3
import sys
import time

import click
import dateparser
import dateutil
import requests

import env


BASE_URL = "https://www.nytimes.com/svc/crosswords"
LIST_URL = (
    BASE_URL + "/v3/puzzles.json?publish_type=daily&date_start={start}&date_end={end}"
)
DIR = pathlib.Path(sys.argv[0]).parent
FIRST_PUZZLE = datetime.date(1993, 11, 21)


def month_start_date(date: datetime.date) -> datetime.date:
    return datetime.date(date.year, date.month, 1)


def month_end_date(date: datetime.date) -> datetime.date:
    next_year, next_month = date.year, date.month + 1
    if next_month > 12:
        next_year += 1
        next_month = 1
    return datetime.date(next_year, next_month, 1) - datetime.timedelta(days=1)


def _select_date(cursor, *args):
    res = cursor.execute(*args)
    last_unsolved = res.fetchone()
    if last_unsolved:
        return dateparser.parse(last_unsolved[0]).date()
    return None


def last_unsolved(cursor, min_date=None):
    if min_date:
        return _select_date(
            cursor,
            "SELECT date FROM solved WHERE solved = ? AND date >= ? ORDER BY date DESC",
            (False, min_date.strftime("%Y-%m-%d")),
        )
    return _select_date(
        cursor, "SELECT date FROM solved WHERE solved = ? ORDER BY date DESC", (False,)
    )


def first_solved(cursor):
    return _select_date(
        cursor,
        "SELECT date FROM solved WHERE solved = ? ORDER BY date ASC",
        (True,),
    )


@click.command(context_settings={"show_default": True})
@click.option(
    "--db", default=DIR / "data/unsolved.sqlite3", help="Path to unsolved sqlite3 DB"
)
@click.option("--debug/--nodebug", default=False, help="Debug mode")
@click.option("--open/--noopen", default=False, help="Open URL in browser")
@click.option("--stats/--nostats", default=True, help="Show stats")
@click.option("--start", default=None, help="date to start on")
def main(db, debug, open, start, stats):
    cookies = {"NYT-S": env.require_env("NYTXW_COOKIE")}

    with contextlib.closing(sqlite3.connect(db)) as conn:
        with contextlib.closing(conn.cursor()) as cursor:
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS solved "
                "(id INTEGER PRIMARY KEY AUTOINCREMENT, date STRING, solved INTEGER)"
            )
            cursor.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS date_index ON solved(date)"
            )
            conn.commit()

            date = None
            if start:
                date = dateparser.parse(start).date()
            if not date:
                date = last_unsolved(conn)
            if not date:
                date = first_solved(conn)
                if date:
                    date = date - datetime.timedelta(days=1)
            if not date:
                date = datetime.date.today()

            if stats:
                num_solved = cursor.execute(
                    "SELECT COUNT(*) FROM solved WHERE solved=1"
                ).fetchone()[0]
                total_puzzles = (datetime.date.today() - FIRST_PUZZLE).days + 1
                print(
                    f"Solved {num_solved}(ish) of {total_puzzles} puzzles since {FIRST_PUZZLE} ({100 * num_solved / total_puzzles:.2f}%)"
                )
                print()

        while True:
            with contextlib.closing(conn.cursor()) as cursor:
                url = LIST_URL.format(
                    start=month_start_date(date),
                    end=month_end_date(date),
                )

                if debug:
                    print(f"Fetching {url}", file=sys.stderr)

                response = requests.get(url, cookies=cookies)
                response.raise_for_status()
                contents = response.json()
                if debug:
                    pprint.pprint(contents)

                for result in contents["results"]:
                    cursor.execute(
                        "INSERT INTO solved (date, solved) VALUES (?, ?) "
                        "ON CONFLICT(date) DO UPDATE SET solved = excluded.solved;",
                        (result["print_date"], result["solved"]),
                    )
                conn.commit()

                last = last_unsolved(conn, min_date=month_start_date(date))
                if last:
                    leaderboard = f"https://www.nytimes.com/crosswords/archive/daily/{last.year}/{last.month:02d}"
                    print(leaderboard)
                    game = f"https://www.nytimes.com/crosswords/game/daily/{last.year}/{last.month:02d}/{last.day:02d}"
                    print(game)
                    if open:
                        os.system(f"open {game}")
                    break

                date = date - dateutil.relativedelta.relativedelta(months=1)
                time.sleep(0.5)
            conn.commit()


if __name__ == "__main__":
    main()
