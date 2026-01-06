import os
import pathlib
import re
import sys

__CACHE = None

DIR = pathlib.Path(__file__).parent
RCFILE = DIR / ".envrc"


def getenv(name, default=None):
    v = os.getenv(name)

    if not v:
        global __CACHE
        if __CACHE is None:
            if RCFILE.exists():
                __CACHE = dict()
                with open(RCFILE) as f:
                    for line in f.readlines():
                        if not re.match(r"\s*export\s+", line):
                            continue
                        pairs = re.findall(
                            r'\s*?(\S+?)\s*=\s*"?(\S+?)"?(?:\s|$)',
                            line,
                        )
                        if pairs:
                            __CACHE.update(dict(pairs))
        if __CACHE:
            v = __CACHE.get(name)

    if not v:
        return default

    return v


def require_env(name):
    v = getenv(name)

    if not v:
        print(f"environment variable {name} is not specified", file=sys.stderr)
        sys.exit(1)

    return v
