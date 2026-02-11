#!/usr/bin/env pipenv-shebang
import contextlib
import json
import os
import sqlite3

import click


def to_json(aggregated):
    return [
        {"name": k, "results": [{"date": d, "time": t} for (d, t) in sorted(v.items())]}
        for (k, v) in sorted(aggregated.items())
    ]


@click.command(context_settings={"show_default": True})
@click.argument("filename", type=click.Path(exists=True))
@click.argument("output", type=click.File("w"))
def main(filename, output):
    aggregated = {}

    with contextlib.closing(sqlite3.connect(filename)) as db:
        res = db.execute("SELECT date, name, time FROM leaderboards ORDER BY id")
        for date, name, time in res.fetchall():
            aggregated.setdefault(name, {})
            aggregated[name][date] = time

    json.dump(to_json(aggregated), output, indent=2)
    output.write(os.linesep)


if __name__ == "__main__":
    main()
