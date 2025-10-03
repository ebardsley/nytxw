import pytest

import leaderboards


@pytest.mark.parametrize(
    "input,expected",
    [
        ("2:00", 120),
        ("0:30", 30),
        (30, 30),
        (120, 120),
        ("", None),
        (0, None),
    ],
)
def test_time_in_seconds(input, expected):
    assert leaderboards.time_in_seconds(input) == expected


@pytest.mark.parametrize(
    "input,expected",
    [
        ("2:00", "2:00"),
        ("abc", "abc"),
        (30, "0:30"),
        (120, "2:00"),
        (5400, "90:00"),
    ],
)
def test_time_in_minutes(input, expected):
    assert leaderboards.time_in_minutes(input) == expected


@pytest.mark.parametrize(
    "date,scores,expected",
    [
        ("", {}, None),
        ("", {"Ed": 15}, "Ed 0:15"),
        ("today", {"Ed": 15}, "today: Ed 0:15"),
        (
            "",
            {"Ed": 15, "spags": 90},
            "Ed 0:15, spags 1:30",
        ),
    ],
)
def test_format_message(date, scores, expected):
    assert leaderboards.format_message(date, scores) == expected


def test_parse_json_and_format():
    data = open("testdata/mini-2025.json").read()
    parsed = leaderboards.parse_json(data)
    assert (
        leaderboards.format_message(
            parsed["date"], {s["name"]: s["time"] for s in parsed["scores"]}
        )
        == "2025-10-03: spags 0:18, Bardsleys 0:26, shaggy 0:31"
    )
