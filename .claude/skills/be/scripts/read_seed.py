#!/usr/bin/env python3
"""
read_seed — find the freshest wish someone planted at the THRESHOLD.

The dandelion (seed.py / index.html) writes a seed to
    THRESHOLD/current_session/build_seed/<medium>.md
with the payload inside a ```json block. This reads the newest UNCONSUMED,
valid one and prints it as JSON to stdout.

Usage:
    python read_seed.py            # print newest seed payload as JSON
    python read_seed.py --all      # list every valid unconsumed seed
    python read_seed.py --path P   # parse one specific seed file

Exit codes:
    0  a seed was found and printed
    2  the threshold is quiet (no valid unconsumed seed)
    3  the fort could not be found
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _fortlib as fl  # noqa: E402


def main(argv):
    try:
        root = fl.resolve_fort_root()
    except FileNotFoundError as e:
        sys.stderr.write(str(e) + "\n")
        return 3

    if "--path" in argv:
        i = argv.index("--path")
        path = argv[i + 1]
        payload = fl.parse_seed(path)
        if payload is None:
            sys.stderr.write("No valid, unconsumed wish in %s\n" % path)
            return 2
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if "--all" in argv:
        found = []
        for p in fl.iter_seed_files(root):
            payload = fl.parse_seed(p)
            if payload is not None:
                found.append(payload)
        if not found:
            sys.stderr.write("The threshold is quiet. No wishes are waiting.\n")
            return 2
        found.sort(key=lambda pl: fl._session_sort_key(pl, pl["_seed_path"]),
                   reverse=True)
        print(json.dumps(found, ensure_ascii=False, indent=2))
        return 0

    payload = fl.newest_seed(root)
    if payload is None:
        sys.stderr.write(
            "The threshold is quiet. No wishes are waiting.\n"
            "  Plant one: python THRESHOLD/current_session/seed.py\n"
            "  (or run the dandelion inline, or pass a { medium, wants } payload.)\n"
        )
        return 2
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
