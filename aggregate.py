#!/usr/bin/env pipenv-shebang

import datetime
import json
import os
import pprint
import sys

BLACKLIST = frozenset([
  'JourHadiqueBot',
])

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

  for path in argv[2:]:
    process_file(path, aggregated)

  with open(output, 'w') as f:
    json.dump(to_json(aggregated), f, indent=2)
  # pprint.pprint(to_json(aggregated))

if __name__ == '__main__':
  main(sys.argv)
