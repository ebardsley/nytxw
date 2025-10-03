import format


def test_format(capfd):
    format.main(["format.py", "testdata/mini.sqlite3"])
    captured = capfd.readouterr()
    assert captured.out == "2025-10-03: spags 0:18, Bardsleys 0:26, shaggy 0:31\n"
