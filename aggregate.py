#!/usr/bin/env pipenv-shebang

import contextlib
import datetime
import glob
import json
import os
import sqlite3
import sys

BLACKLIST = frozenset([
  'JourHadiqueBot',
])
DB = os.getenv('NYTXW_SQLITE3', None)

def time_in_seconds(t):
  if isinstance(t, str):
    if ':' in t:
      ret = 0
      parts = t.split(':')
      for part in parts:
        ret = ret * 60 + int(part)
      return ret
    return None
  return t or None


def process_file(filename, aggregated):
  with open(filename, 'r') as f:
    data = eval(f.read())
  if 'date' not in data or 'scores' not in data:
    print(f'{filename} does not contain "date" and "scores"')
    return
  date = str(data['date'])
  for score in data['scores']:
    name = score['name'].strip()
    if name in BLACKLIST:
      continue
    aggregated.setdefault(name, {})
    t = time_in_seconds(score['time'])
    if t:
      aggregated[name][date] = t


def to_json(aggregated):
  return [
    {'name': k, 'results': [{'date': d, 'time': t} for (d, t) in sorted(v.items())]}
    for (k, v) in sorted(aggregated.items())
  ]


def main(argv):
  output = argv[1]
  aggregated = {}

  for globspec in argv[2:]:
    for path in glob.glob(globspec):
      process_file(path, aggregated)

  with open(output, 'w') as f:
    json.dump(to_json(aggregated), f, indent=2)

  if DB:
    by_date_and_name = {}
    for name, date_time_map in aggregated.items():
      for date, time in date_time_map.items():
        by_date_and_name.setdefault(date, {})
        by_date_and_name[date][name] = time

    with contextlib.closing(sqlite3.connect(DB)) as conn:
      with contextlib.closing(conn.cursor()) as cursor:
        for date in sorted(by_date_and_name):
          for name in sorted(by_date_and_name[date]):
            rows = cursor.execute(
              'SELECT * FROM leaderboards WHERE date = ? AND name = ?',
              (date, name),
            ).fetchone()
            if not rows:
              cursor.execute(
                'INSERT INTO leaderboards (date, name, time) VALUES (?, ?, ?)',
                (date, name, by_date_and_name[date][name]),
              )
              print('INSERT', date, name, by_date_and_name[date][name]),
      conn.commit()
    print('Updated', DB)


if __name__ == '__main__':
  main(sys.argv)
