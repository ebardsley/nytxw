#!/usr/bin/env pipenv-shebang
import contextlib
import datetime
import json
import pprint
import sqlite3

import click
import dateparser

import botsay
import cookie
import env


# TODO: remove this after a suitable delay
LEADERBOARD_URL = "https://www.nytimes.com/svc/crosswords/v6/leaderboard/mini.json"

# New interface, as of 2026/02/10-ish.
# https://github.com/theodoretliu/crossword-leaderboard/blob/dafa30041ab85dfa7eca9fe03a4becde22dd9540/api-reverse-engineer.md
GRAPHQL_URL = "https://samizdat-graphql.nytimes.com/graphql/v2?operationName=UserDetails&variables=%7B%22printDate%22:%22{}%22%7D&extensions=%7B%22persistedQuery%22:%7B%22sha256Hash%22:%223f462df6ff876e20c737369faf1d3d65725fa54e62ff4039ee13c3e22ecc14f5%22,%22version%22:1%7D%7D"


def time_in_seconds(t):
    if isinstance(t, str):
        if ":" in t:
            ret = 0
            parts = t.split(":")
            for part in parts:
                ret = ret * 60 + int(part)
            return ret
        return None
    return t or None


def time_in_minutes(t):
    if not isinstance(t, str):
        t = f"{t // 60}:{t % 60:02d}"
    return t


def scores_for_date(cursor, date):
    res = cursor.execute(
        "SELECT name, time FROM leaderboards WHERE date = ? ORDER BY id", (date,)
    )
    # Uniqueify by name.
    scores = {name: time for (name, time) in res.fetchall()}
    return scores


def format_message(date, scores):
    times = []
    for name, time in scores.items():
        if name and time:
            times.append(
                (
                    time_in_seconds(time),
                    f"{name} {time_in_minutes(time)}",
                )
            )

    if not times:
        return None

    message = ""
    if date:
        message = f"{date}: "
    message += ", ".join(x[1] for x in sorted(times))

    return message


def send_reminders(cursor, channel, date, today_scores):
    res = cursor.execute(
        "SELECT DISTINCT date FROM leaderboards ORDER BY date DESC LIMIT 2"
    )
    rows = res.fetchall()
    if not rows or len(rows) != 2:
        return
    yesterday = rows[-1][0]

    discord_userids = {
        name.lower(): userid
        for (name, userid) in cursor.execute(
            "SELECT name, userid FROM remind_users"
        ).fetchall()
    }

    yesterday_scores = scores_for_date(cursor, yesterday)
    for name in yesterday_scores.keys():
        discord_userid = discord_userids.get(name.lower())
        if discord_userid and name not in today_scores:
            botsay.say(
                channel,
                f"Remember to do your NYT mini crossword for {date}",
                extra={"userid": discord_userid, "channelid": 0},
            )


@click.command(context_settings={"show_default": True})
@click.option(
    "--announce/--noannounce", default=False, help="Announce daily scores on discord"
)
@click.option(
    "--channel",
    default=env.getenv("NYTXW_CHANNELS", ""),
    help="Channel to announce to (may be comma-separated)",
)
@click.option(
    "-d",
    "--date",
    default=None,
    help="Date of leaderboard to get",
)
@click.option(
    "--db",
    default=env.getenv("NYTXW_SQLITE3", env.DIR / "data/mini.sqlite3"),
    help="Path to mini sqlite3 DB",
)
@click.option(
    "--remind/--noremind",
    default=False,
    help="Remind individual users to do the puzzle",
)
def main(announce, channel, date, db, remind):
    headers = {
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "nyt-app-type": "games-phoenix",
        "nyt-app-version": "1.0.0",
        "nyt-token": "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAiKjdfob/ixNCvLETwnQ3AalkGSm9NX4gcRbOudrtHmBmIJbWb8Xgu3QH516Edr1qD7A+w+5d0p/WsNCpWDLrqfjTIwMft+jtOQG44l7akD9yi9Gaq/6hS3cuntkY25AYR3WtQPqrtxClX+qQdhMmzlA0sRAXKM8dSbIpsNV9uUOclt3JwB4omwFGj4J+pqzsfYZfB/tlx+BPGjCYGNcZ9O9UvtCpLRLgCJmTugL6V/U581gY8mqp+22aVjbEJik+F0j8xTNSxCOV2PLMpNrRSiDZ8FaKtq8ap/HPey5M7qYZQqclfqsEJMXG/KE3PiaTIbO37caFa80FvzfV8MZw1wIDAQAB",
    }
    if date is None:
        date = datetime.date.today()
    else:
        date = dateparser.parse(date).date()
    url = GRAPHQL_URL.format(date)
    response = cookie.get_with_cookie(url, headers=headers)
    response.raise_for_status()
    contents = response.text

    data = parse_graphql_json(contents)
    if not data.get("date"):
        data["date"] = str(date)
    pprint.pprint(data)

    with contextlib.closing(sqlite3.connect(db)) as conn:
        with contextlib.closing(conn.cursor()) as cursor:
            date = data["date"]
            seen = scores_for_date(cursor, date)
            for score in data["scores"]:
                if score["time"] and score["time"] != seen.get(score["name"]):
                    cursor.execute(
                        "INSERT INTO leaderboards (date, name, time) VALUES (?, ?, ?)",
                        (date, score["name"], score["time"]),
                    )
            conn.commit()
            print("Updated", db)

            scores = scores_for_date(cursor, date)

            if remind:
                send_reminders(cursor, channel, date, scores)

    if announce and channel:
        message = format_message(date, scores)
        if message:
            botsay.say(channel, message)

    return


def parse_json(contents):
    j = json.loads(contents)
    scores = [
        {
            "name": d.get("name"),
            "rank": d.get("rank"),
            "time": d.get("score", {}).get("secondsSpentSolving"),
        }
        for d in j.get("data", [])
    ]
    return {
        "date": j.get("printDate"),
        "scores": scores,
    }


def parse_graphql_json(contents):
    j = json.loads(contents)
    edges = j.get("data", {}).get("user", {}).get("friends", {}).get("edges", [])
    scores = [
        {
            "name": e.get("node", {}).get("profile", {}).get("gamesUsername"),
            "rank": e.get("rank"),
            "time": (
                e.get("node", {}).get("gameScores", {}).get("crosswordMini") or {}
            ).get("solveTimeSeconds"),
        }
        for e in edges
    ]
    return {
        "date": None,
        "scores": scores,
    }


if __name__ == "__main__":
    main()
