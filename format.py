#!/usr/bin/env pipenv-shebang

import datetime
import os
import sys

import leaderboards

def main(argv):
  if len(argv) != 2:
    print(f'usage: {argv[0]} <file>', file=sys.stderr)
    sys.exit(1)
    
  with open(argv[1]) as f:
    data = eval(f.read())

  print(leaderboards.format_message(data))
  

if __name__ == '__main__':
  main(sys.argv)