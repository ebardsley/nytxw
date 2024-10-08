#!/usr/bin/env pipenv-shebang

import contextlib
import glob
import json
import os
import sqlite3
import sys


def to_json(aggregated):
  return [
    {'name': k, 'results': [{'date': d, 'time': t} for (d, t) in sorted(v.items())]}
    for (k, v) in sorted(aggregated.items())
  ]


def main(argv):
  db = argv[1]
  output = argv[2]
  aggregated = {}

  with contextlib.closing(sqlite3.connect(db)) as conn:
    with contextlib.closing(conn.cursor()) as cursor:
      res = cursor.execute('SELECT date, name, time FROM leaderboards ORDER BY id')
      for date, name, time in res.fetchall():
        aggregated.setdefault(name, {})
        aggregated[name][date] = time

  with open(output, 'w') as f:
    json.dump(to_json(aggregated), f, indent=2)


if __name__ == '__main__':
  main(sys.argv)
