import os
import sys

def require_env(name):
  v = os.getenv(name)
  if not v:
    print(f'environment variable {name} is not specified', file=sys.stderr)
    sys.exit(1)
  return v
