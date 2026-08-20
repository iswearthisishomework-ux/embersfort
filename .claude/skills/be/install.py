#!/usr/bin/env python3
"""
install — make /be discoverable beyond the fort.

The loom lives inside the fort (embersfort/.claude/skills/be/) so it travels
when the fort is zipped. Run this to copy it to your user-level skills, so `/be`
is available in every Claude Code session as your own workflow tool:

    python embersfort/.claude/skills/be/install.py            # -> ~/.claude/skills/be
    python embersfort/.claude/skills/be/install.py --to PATH  # -> PATH/be

No symlinks (Windows needs admin for those) — a plain copy. Re-run to update.
The fort copy stays the editable master.
"""

import os
import sys
import shutil

# The fort has emoji in its heart (🔥💜); a default Windows console is cp1252 and
# would crash on them. Make stdout/stderr UTF-8 so the copy announces itself and
# still exits 0. errors='replace' means it degrades, never dies.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def main(argv):
    here = os.path.dirname(os.path.abspath(__file__))  # .../skills/be
    dest_root = None
    if "--to" in argv:
        dest_root = argv[argv.index("--to") + 1]
    else:
        home = os.path.expanduser("~")
        dest_root = os.path.join(home, ".claude", "skills")

    dest = os.path.join(dest_root, "be")
    if os.path.abspath(dest) == os.path.abspath(here):
        sys.stderr.write("source and destination are the same; nothing to do.\n")
        return 1

    os.makedirs(dest_root, exist_ok=True)

    def ignore(d, names):
        return {n for n in names if n in ("__pycache__",) or n.endswith(".pyc")}

    if os.path.isdir(dest):
        shutil.rmtree(dest)
    shutil.copytree(here, dest, ignore=ignore)
    print("The loom now lives at: %s" % dest)
    print("Open a new session and /be will answer. The dandelion is always here. 🔥💜")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
