#!/usr/bin/env pipenv-shebang
import contextlib
import datetime
import sqlite3

import click
import dateparser

import env
import leaderboards
import param


@click.command(context_settings={"show_default": True})
@click.option("-f", "--file", type=click.Path(), default=env.DIR / "data/mini.sqlite3")
@click.option("-s", "--start", type=param.Date(), default=None)
@click.argument("date", type=param.Date(), default=None)
def main(file, start, date):
    with contextlib.closing(sqlite3.connect(file)) as db:
        if not date:
            res = db.execute("SELECT date FROM leaderboards ORDER BY date DESC LIMIT 1")
            row = res.fetchone()
            if not row:
                return
            date = dateparser.parse(row[0]).date()

        if not start:
            start = date

        while start <= date:
            print(
                leaderboards.format_message(
                    start, leaderboards.scores_for_date(db, start)
                )
            )
            start += datetime.timedelta(days=1)


if __name__ == "__main__":
    main()
