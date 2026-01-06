#!/usr/bin/env pipenv-shebang
import contextlib
import datetime
import sqlite3

import click
import requests

import env

DB = env.getenv("NYTXW_COOKIE_SQLITE3", env.DIR / "data/cookie.sqlite3")

sqlite3.register_adapter(datetime.date, lambda t: t.isoformat())
sqlite3.register_adapter(datetime.datetime, lambda t: t.isoformat())


def login_get_cookie(username, password):
    login_resp = requests.post(
        "https://myaccount.nytimes.com/svc/ios/v2/login",
        data={
            "login": username,
            "password": password,
        },
        headers={
            "User-Agent": "Crosswords/20191213190708 CFNetwork/1128.0.1 Darwin/19.6.0",
            "client_id": "ios.crosswords",
        },
    )
    login_resp.raise_for_status()
    for cookie in login_resp.json()["data"]["cookies"]:
        if cookie["name"] == "NYT-S":
            return cookie["cipheredValue"]
    raise ValueError("NYT-S cookie not found")


def get_cookie(login=True, filename=DB):
    with contextlib.closing(sqlite3.connect(filename)) as conn:
        with conn:
            res = conn.execute(
                "SELECT cookie FROM cookies WHERE valid=? ORDER BY date DESC", (True,)
            )
            ret = res.fetchone()
            if ret:
                return ret[0], True

            username = env.getenv("NYTXW_USERNAME")
            password = env.getenv("NYTXW_PASSWORD")
            if login and username and password:
                cookie = login_get_cookie(username, password)
                conn.execute(
                    "INSERT INTO cookies (cookie, valid, date) VALUES(?, ?, ?)",
                    (cookie, True, datetime.datetime.now()),
                )
                return cookie, False

    raise ValueError("no cookie")


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    if ctx.invoked_subcommand:
        return
    cookie, from_db = get_cookie()
    print(f"cookie: {cookie} (from_db {from_db})")


@main.command()
@click.argument("filename", default=DB)
def initialize(filename):
    with contextlib.closing(sqlite3.connect(filename)) as conn:
        with contextlib.closing(conn.cursor()) as cursor:
            cursor.execute(
                """
      CREATE TABLE cookies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TIMESTAMP,
        cookie TEXT,
        valid INTEGER
      );
      """
            )


def invalidate(cookie, filename=DB):
    with contextlib.closing(sqlite3.connect(filename)) as conn:
        with conn:
            conn.execute("UPDATE cookies SET VALID=? WHERE cookie=?", (False, cookie))


def get_with_cookie(url):
    headers = {
        "User-Agent": "Crosswords/20191213190708 CFNetwork/1128.0.1 Darwin/19.6.0",
        "client_id": "ios.crosswords",
    }

    cookie, from_db = env.getenv("NYTXW_COOKIE"), False
    if not cookie:
        cookie, from_db = get_cookie()

    # Get a new cookie and refresh if necessary.
    response = requests.get(url, cookies={"NYT-S": cookie}, headers=headers)
    if from_db and 500 > response.status_code >= 400:
        invalidate(cookie)
        cookie, from_db = get_cookie()
        response = requests.get(url, cookies={"NYT-S": cookie}, headers=headers)

    return response


if __name__ == "__main__":
    main()
