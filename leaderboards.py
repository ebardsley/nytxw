#!/usr/bin/env pipenv-shebang

import pprint
import sys
import time

import dateparser
from bs4 import BeautifulSoup
import requests

import botsay
import env


DATE_CLASS = 'lbd-type__date'
SCORE_PREFIX = 'lbd-score__'
LEADERBOARD_URL = 'https://www.nytimes.com/puzzles/leaderboards'
COOKIES = {'NYT-S': env.require_env('NYTXW_COOKIE')}
BOT_TOKEN = env.require_env('NYTXW_BOT')
CHANNEL_ID = [
#  885446213237866539,  # Bardsleys #general
  804397490987466793,  # DSSN #puzzles
]

def get_best_string(c):
  if c.string is not None:
    return c.string
  for s in c.strings:
    return s
  return None

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

def format_message(data):
  scores = []
  for s in data['scores']:
    if s.get('name') and s.get('time'):
      scores.append((time_in_seconds(s['time']), f'{s["name"]} {s["time"]}'))

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

  data = parse_html(contents)
  pprint.pprint(data)
  filename = time.strftime('nytxw-%Y%m%d%H%M.pson')
  with open(filename, 'w') as f:
    f.write(pprint.pformat(data))
  print('Wrote', filename)

  # data = parse_html(open('test.txt').read())
  message = format_message(data)
  if not message:
    print('No scores, exiting')
    return

  print(message)
  botsay.say(BOT_TOKEN, CHANNEL_ID, message)

  return

def parse_html(contents):
  soup = BeautifulSoup(contents, features='html.parser')
  items = soup.find_all('div', class_='lbd-board__items')
  scores = []
  for i in items:
    for s in i.find_all(class_='lbd-score'):
      score_dict = {}
      for c in s.children:
        class_ = c.get('class')
        if class_ and SCORE_PREFIX in class_[0]:
          value = get_best_string(c)
          if value in ('*', '--'):
            value = None
          if value:
            value = value.strip()
          score_dict[class_[0].replace(SCORE_PREFIX, '')] = value
      if score_dict:
        scores.append(score_dict)

  data = {
    'date': None,
    'scores': scores,
  }

  date = soup.find(class_=DATE_CLASS)
  if date:
    parsed = dateparser.parse(date.string)
    if parsed:
      data['date'] = parsed.date()

  return data

if __name__ == '__main__':
  main(sys.argv)
