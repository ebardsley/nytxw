import click.testing

import sqlite_to_json


def test_sqlite_to_json(capfd):
    runner = click.testing.CliRunner()
    result = runner.invoke(
        sqlite_to_json.main, ["testdata/mini.sqlite3", "/dev/stdout"]
    )
    captured = capfd.readouterr()
    expected = open("testdata/mini.aggregated.json").read()
    assert result.exit_code == 0
    assert (
        captured.out == expected
    )  # Not in result.output, since it explicitly opens /dev/stdout.
