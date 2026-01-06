#!/usr/bin/env pipenv-shebang
import collections
import contextlib
import datetime
import os
import pprint
import sqlite3
import sys
import time

import click
import dateparser
import dateutil

import cookie
import env


BASE_URL = "https://www.nytimes.com/svc/crosswords"
LIST_URL = (
    BASE_URL + "/v3/puzzles.json?publish_type=daily&date_start={start}&date_end={end}"
)
FIRST_PUZZLE = datetime.date(1993, 11, 21)

sqlite3.register_adapter(datetime.date, lambda t: t.isoformat())


def month_start_date(date: datetime.date) -> datetime.date:
    return datetime.date(date.year, date.month, 1)


def month_end_date(date: datetime.date) -> datetime.date:
    next_year, next_month = date.year, date.month + 1
    if next_month > 12:
        next_year += 1
        next_month = 1
    return datetime.date(next_year, next_month, 1) - datetime.timedelta(days=1)


def month_solvable_days(date: datetime.date) -> int:
    end = min(datetime.date.today(), month_end_date(date))
    return (end - month_start_date(date)).days + 1


def month_solved_count(cursor, date: datetime.date) -> int:
    return cursor.execute(
        "SELECT COUNT(*) FROM solved WHERE solved=1 AND ? <= date AND date <= ?",
        (month_start_date(date), month_end_date(date)),
    ).fetchone()[0]


def _select_date(cursor, *args) -> datetime.date | None:
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
    "--db",
    default=env.DIR / "data/unsolved.sqlite3",
    help="Path to unsolved sqlite3 DB",
)
@click.option("--debug/--nodebug", default=False, help="Debug mode")
@click.option("--open/--noopen", default=False, help="Open URL in browser")
@click.option("--stats/--nostats", default=True, help="Show stats")
@click.option(
    "--summary/--nosummary", default=False, help="Show even more stats, summary by year"
)
@click.option("--start", default=None, help="date to start on")
def main(db, debug, open, start, stats, summary):
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

        while True:
            with contextlib.closing(conn.cursor()) as cursor:
                solvable_days = month_solvable_days(date)
                solved_days = month_solved_count(cursor, date)
                should_refresh_month = solved_days < solvable_days

                if debug:
                    print(
                        f"{date}: solved {solved_days} of {solvable_days}, {should_refresh_month=}"
                    )

                if should_refresh_month:
                    url = LIST_URL.format(
                        start=month_start_date(date),
                        end=month_end_date(date),
                    )

                    if debug:
                        print(f"Fetching {url}", file=sys.stderr)

                    response = cookie.get_with_cookie(url)
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
                if should_refresh_month:
                    time.sleep(0.5)
            conn.commit()

        if stats:
            num_solved = conn.execute(
                "SELECT COUNT(*) FROM solved WHERE solved=1"
            ).fetchone()[0]
            total_puzzles = (datetime.date.today() - FIRST_PUZZLE).days + 1
            print()
            print(
                f"Solved {num_solved}(ish) of {total_puzzles} puzzles since {FIRST_PUZZLE} "
                f"({100 * num_solved / total_puzzles:.2f}%)"
            )

        if summary:
            by_year = collections.defaultdict(int)
            for r in conn.execute("SELECT date FROM solved WHERE solved=1"):
                by_year[r[0][0:4]] += 1
            print()
            print(", ".join(f"{y}: {c}" for y, c in reversed(sorted(by_year.items()))))


if __name__ == "__main__":
    main()
