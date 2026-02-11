import click.testing

import format


def test_format():
    runner = click.testing.CliRunner()
    result = runner.invoke(format.main, ["testdata/mini.sqlite3"])
    assert result.output == "2025-10-03: spags 0:18, Bardsleys 0:26, shaggy 0:31\n"
    assert result.exit_code == 0
