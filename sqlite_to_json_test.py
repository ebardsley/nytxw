import sqlite_to_json


def test_sqlite_to_json(capfd):
    sqlite_to_json.main(["sqlite_to_json.py", "testdata/mini.sqlite3", "/dev/stdout"])
    captured = capfd.readouterr()
    expected = open("testdata/mini.aggregated.json").read()
    assert captured.out == expected
