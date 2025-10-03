#!/usr/bin/env pipenv-shebang
import json
import os
import sys

import dateparser
import requests

import env


URL = "https://www.nytimes.com/svc/crosswords/v6/puzzle/daily/{date}.json"
COOKIES = {"NYT-S": env.require_env("NYTXW_COOKIE")}


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


def main(argv):
    parsed_date = dateparser.parse(sys.argv[1])
    date = parsed_date.strftime("%Y-%m-%d")
    url = URL.format(date=date)
    print("#", url)

    if os.path.exists(f"{date}.json"):
        contents = open(f"{date}.json").read()
    else:
        response = requests.get(url, cookies=COOKIES)
        response.raise_for_status()
        contents = response.text

    data = json.loads(contents)
    puzzle = data.get("body", [{}])[0]
    print(puzzle_to_string(puzzle))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
