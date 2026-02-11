#!/usr/bin/env pipenv-shebang
import contextlib
import sqlite3

import click

import leaderboards
import param


@click.command(context_settings={"show_default": True})
@click.argument("file", type=click.Path(), required=True)
@click.argument("date", type=param.Date(), default=None)
def main(file, date):
    with contextlib.closing(sqlite3.connect(file)) as conn:
        with contextlib.closing(conn.cursor()) as cursor:
            if not date:
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
    main()
