#!/usr/bin/env pipenv-shebang
import contextlib
import json
import os
import pprint
import sqlite3

import click
import requests

import botsay
import env


LEADERBOARD_URL = "https://www.nytimes.com/svc/crosswords/v6/leaderboard/mini.json"
COOKIES = {"NYT-S": env.require_env("NYTXW_COOKIE")}
CHANNEL_ID = os.getenv("NYTXW_CHANNELS", "")
DB = os.getenv("NYTXW_SQLITE3", "data/mini.sqlite3")


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


def send_reminders(cursor, date, today_scores):
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
                CHANNEL_ID,
                f"Remember to do your NYT mini crossword for {date}",
                extra={"userid": discord_userid, "channelid": 0},
            )


@click.command()
@click.option(
    "--announce/--noannounce", default=False, help="Announce daily scores on discord"
)
@click.option(
    "--remind/--noremind",
    default=False,
    help="Remind individual users to do the puzzle",
)
def main(announce, remind):
    response = requests.get(LEADERBOARD_URL, cookies=COOKIES)
    response.raise_for_status()
    contents = response.text

    data = parse_json(contents)
    pprint.pprint(data)

    with contextlib.closing(sqlite3.connect(DB)) as conn:
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
            print("Updated", DB)

            scores = scores_for_date(cursor, date)

            if remind:
                send_reminders(cursor, date, scores)

    if announce and CHANNEL_ID:
        message = format_message(date, scores)
        if message:
            botsay.say(CHANNEL_ID, message)

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


if __name__ == "__main__":
    main()
