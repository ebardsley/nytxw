import datetime
import sqlite3

import click
import dateparser

sqlite3.register_adapter(datetime.date, lambda t: t.isoformat())
sqlite3.register_adapter(datetime.datetime, lambda t: t.isoformat())


class Date(click.ParamType):
    name = "date"

    def convert(self, value, param, ctx):
        if value is None:
            return value
        d = dateparser.parse(value)
        if not d:
            self.fail(f"{value!r} is not a valid date", param, ctx)
        return d.date()


class DB(click.Path):
    name = "db"

    def __init__(self, *args, exists=True, **kwargs):
        super().__init__(*args, exists=exists, **kwargs)

    def convert(self, value, param, ctx):
        filename = super().convert(value, param, ctx)
        db = sqlite3.connect(filename)
        ctx.call_on_close(click.utils.safecall(db.close))
        return db
