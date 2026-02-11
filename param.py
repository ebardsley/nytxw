import click
import dateparser


class Date(click.ParamType):
    name = "date"

    def convert(self, value, param, ctx):
        if value is None:
            return value
        d = dateparser.parse(value)
        if not d:
            self.fail(f"{value!r} is not a valid date", param, ctx)
        return d.date()
