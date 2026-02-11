#!/usr/bin/env pipenv-shebang
import click

import param


@click.command(context_settings={"show_default": True})
@click.argument("db", type=param.DB(exists=False))
def main(db):
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS leaderboards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            name TEXT,
            time INTEGER,
            updated_ts INTEGER,
            updated_by TEXT
        )
    """
    )


if __name__ == "__main__":
    main()
