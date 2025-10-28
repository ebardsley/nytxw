import os
import pathlib
import re
import sys

__CACHE = None


def require_env(name):
    v = os.getenv(name)

    if not v:
        global __CACHE
        if __CACHE is None:
            rc = pathlib.Path(__file__).parent / ".envrc"
            if rc.exists():
                with open(rc) as f:
                    contents = f.read()
                pairs = re.findall(
                    r'^export\s+(\S+?)\s*=\s*"?(\S+?)"?$', contents, re.M
                )
                if pairs:
                    __CACHE = dict(pairs)
        if __CACHE:
            v = __CACHE.get(name)

    if not v:
        print(f"environment variable {name} is not specified", file=sys.stderr)
        sys.exit(1)

    return v
