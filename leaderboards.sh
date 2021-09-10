#!/bin/bash

set -e

cd "$(dirname "$0")"
direnv exec . ./leaderboards.py
