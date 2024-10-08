#!/usr/bin/env pipenv-shebang

import contextlib
import json
import os
import pprint
import sqlite3
import sys

import requests

import botsay
import env


LEADERBOARD_URL = 'https://www.nytimes.com/svc/crosswords/v6/leaderboard/mini.json'
COOKIES = {'NYT-S': env.require_env('NYTXW_COOKIE')}
BOT_TOKEN = env.require_env('NYTXW_BOT')
CHANNEL_ID = [int(c) for c in os.getenv('NYTXW_CHANNELS', '').split(',') if c]
DB = os.getenv('NYTXW_SQLITE3', 'data/mini.sqlite3')

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

def time_in_minutes(t):
  if not isinstance(t, str):
    t = f'{t//60}:{t%60:02d}'
  return t

def format_message(data):
  scores = []
  for s in data['scores']:
    if s.get('name') and s.get('time'):
      scores.append((time_in_seconds(s['time']), f'{s["name"]} {time_in_minutes(s["time"])}'))

  if not scores:
    return None

  message = ''
  if data['date']:
    message = f'{data["date"]}: '
  message += ', '.join(x[1] for x in sorted(scores))

  return message

def main(argv):
  response = requests.get(LEADERBOARD_URL, cookies=COOKIES)
  response.raise_for_status()
  contents = response.text

  data = parse_json(contents)
  pprint.pprint(data)

  if DB:
    # DB is:
    #   CREATE TABLE leaderboards (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, name TEXT, time INTEGER);
    with contextlib.closing(sqlite3.connect(DB)) as conn:
      with contextlib.closing(conn.cursor()) as cursor:
        date = data['date']
        for score in data['scores']:
          if score['time']:
            cursor.execute(
              'INSERT INTO leaderboards (date, name, time) VALUES (?, ?, ?)',
              (date, score['name'], score['time']),
            )
      conn.commit()
    print('Updated', DB)

  message = format_message(data)
  if not message:
    print('No scores, exiting')
    return

  print(message)
  if CHANNEL_ID:
    botsay.say(BOT_TOKEN, CHANNEL_ID, message)

  return

def parse_json(contents):
  j = json.loads(contents)
  scores = [
    {'name': d.get('name'),
     'rank': d.get('rank'),
     'time': d.get('score', {}).get('secondsSpentSolving'),
    } for d in j.get('data', [])
  ]
  return {
    'date': j.get('printDate'),
    'scores': scores,
  }

if __name__ == '__main__':
  main(sys.argv)
