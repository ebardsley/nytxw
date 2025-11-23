#!/usr/bin/env pipenv-shebang
import json
import os
import sys

import click
import dateparser
import requests

import env


URL = "https://www.nytimes.com/svc/crosswords/v6/puzzle/{game}/{date}.json"


def puzzle_to_string(puzzle):
    if not puzzle:
        raise ValueError("no puzzle data")

    width = puzzle.get("dimensions", {}).get("width")
    if not width:
        raise ValueError("no width")

    ret = ""
    for i, cell in enumerate(puzzle.get("cells", []), start=1):
        ret += cell.get("answer") or " "
        if i % width == 0:
            ret = ret.strip()
            ret += os.linesep

    return ret


@click.command(context_settings={"show_default": True})
@click.option("-m", "--mini", is_flag=True, default=False)
@click.argument("date-arg", type=str)
def main(date_arg, mini):
    cookies = {"NYT-S": env.require_env("NYTXW_COOKIE")}
    parsed_date = dateparser.parse(sys.argv[1])
    date = parsed_date.strftime("%Y-%m-%d")
    url = URL.format(
        date=date,
        game="mini" if mini else "daily",
    )
    print("#", url)

    if os.path.exists(f"{date}.json"):
        contents = open(f"{date}.json").read()
    else:
        response = requests.get(url, cookies=cookies)
        response.raise_for_status()
        contents = response.text

    data = json.loads(contents)
    puzzle = data.get("body", [{}])[0]
    print(puzzle_to_string(puzzle))


if __name__ == "__main__":
    main()
