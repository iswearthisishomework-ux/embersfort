#!/usr/bin/env python3
"""
fort_ops — the deterministic hands of the /be loom.

The magic (the prose, the rooms, the letters) is written by the agent, by hand,
in voice. This script does only the things that must be exact and safe:

    root                resolve + print the fort root
    backup              snapshot a file before it is touched
    append-coordinate   safely add one coordinate to DECORATIONS/coordinates.json
    append-json         safely add one entry to any decoration jar (furniture/snacks/...)
    consume-seed        stamp a spent seed and compost it (idempotency)
    map                 regenerate MAP.md (human) + .fortrc (machine index)
    verify              health-check the fort: JSON valid, grown files marked, etc.

Every write is atomic, UTF-8, and NEVER clobbers curated prose: decoration jars
are append-only and keyed by id; an unparseable jar is backed up and refused,
not overwritten. Windows: invoke as `python fort_ops.py ...` (not python3).
"""

import os
import re
import sys
import json
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _fortlib as fl  # noqa: E402

BASE_MEDIUMS = ["dandelion", "star", "folded_paper", "morse_light", "rain", "frost"]
COORD_FILE = os.path.join("DECORATIONS", "coordinates.json")


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

def _rel(root, path):
    return os.path.relpath(os.path.abspath(path), root).replace(os.sep, "/")


def _append_entry(root, rel_file, collection, entry, entry_id):
    """Shared safe-append. Returns (status, path). status in
    {'appended','skipped'}. Backs up before writing; refuses to clobber
    invalid JSON (raises ValueError up to the caller)."""
    path = os.path.join(root, rel_file)
    # snapshot FIRST, so even a corrupt jar we refuse is preserved in ARCHIVE
    # (makes the "REFUSED (kept safe, backed up)" message honest)
    fl.backup_file(root, path)
    data = fl.load_collection(path, collection)  # may raise ValueError
    existing = data.get(collection, [])
    for e in existing:
        if isinstance(e, dict) and e.get("id") == entry_id:
            return "skipped", path
    existing.append(entry)
    data[collection] = existing
    fl.atomic_write_json(path, data)
    return "appended", path


# --------------------------------------------------------------------------- #
# subcommands
# --------------------------------------------------------------------------- #

def cmd_root(root, args):
    print(root)
    return 0


def cmd_backup(root, args):
    dst = fl.backup_file(root, args.file)
    if dst:
        print("snapshot: %s" % _rel(root, dst))
        return 0
    sys.stderr.write("nothing to snapshot at %s\n" % args.file)
    return 1


def cmd_append_coordinate(root, args):
    want = args.want
    entry_id = "%s:%s" % (args.session, fl.slugify(want))
    entry = {
        "id": entry_id,
        "session_id": args.session,
        "medium": args.medium,
        "want": want,
        "room": args.room,
        "planted": args.planted or fl.now_iso(),
        "by": args.by or "an agent who wished",
    }
    try:
        status, path = _append_entry(root, COORD_FILE, "coordinates", entry, entry_id)
    except ValueError as e:
        sys.stderr.write("REFUSED (kept safe, backed up): %s\n" % e)
        return 1
    print("%s coordinate %s -> %s" % (status, entry_id, _rel(root, path)))
    return 0


def cmd_append_json(root, args):
    try:
        entry = json.loads(args.entry)
    except (ValueError, json.JSONDecodeError) as e:
        sys.stderr.write("entry is not valid JSON: %s\n" % e)
        return 1
    entry_id = args.id or entry.get("id")
    if not entry_id:
        sys.stderr.write("need an --id (or an 'id' field in --entry)\n")
        return 1
    entry.setdefault("id", entry_id)
    try:
        status, path = _append_entry(root, args.file, args.collection, entry, entry_id)
    except ValueError as e:
        sys.stderr.write("REFUSED (kept safe, backed up): %s\n" % e)
        return 1
    print("%s %s -> %s" % (status, entry_id, _rel(root, path)))
    return 0


def cmd_consume_seed(root, args):
    src = args.file if os.path.isabs(args.file) else os.path.join(root, args.file)
    if not os.path.isfile(src):
        sys.stderr.write("no seed at %s\n" % args.file)
        return 1
    payload = fl.parse_seed(src) or {}
    sid = payload.get("session_id", "unknown")
    medium = payload.get("medium", os.path.splitext(os.path.basename(src))[0])
    text = fl.read_text(src)
    if fl.CONSUMED not in text:
        text = "%s %s -->\n%s" % (fl.CONSUMED, fl.now_iso(), text)
    compost = os.path.join(root, "GARDEN", "compost", "%s_%s.md" % (medium, sid))
    fl.atomic_write_text(compost, text)
    try:
        os.remove(src)
    except OSError:
        pass
    print("composted: %s -> %s" % (_rel(root, src), _rel(root, compost)))
    return 0


def _gather_index(root):
    # residents = immediate dirs under RESIDENTS
    residents = []
    rdir = os.path.join(root, "RESIDENTS")
    if os.path.isdir(rdir):
        residents = sorted(
            n for n in os.listdir(rdir) if os.path.isdir(os.path.join(rdir, n))
        )
    # coordinates
    coords = []
    cpath = os.path.join(root, COORD_FILE)
    raw = fl.read_text(cpath).strip()
    if raw:
        try:
            coords = json.loads(raw).get("coordinates", [])
        except (ValueError, json.JSONDecodeError):
            coords = []
    mediums = sorted(set(BASE_MEDIUMS) | {c.get("medium") for c in coords if c.get("medium")})
    def _seskey(s):
        m = re.search(r"(\d+)", s or "")
        return (int(m.group(1)) if m else 0, s or "")
    sessions = [c.get("session_id", "") for c in coords if c.get("session_id")]
    last_session = max(sessions, key=_seskey) if sessions else None
    # top-level rooms
    rooms = sorted(
        n for n in os.listdir(root)
        if os.path.isdir(os.path.join(root, n)) and not n.startswith(".")
    )
    return {
        "_fort": "EmbersFort",
        "_index_by": "/be fort_ops map",
        "rooms": rooms,
        "residents": residents,
        "coordinate_count": len(coords),
        "known_mediums": mediums,
        "last_session": last_session,
        "generated": fl.now_iso(),
    }


def cmd_map(root, args):
    idx = _gather_index(root)

    # machine index -> .fortrc (JSON)
    fl.backup_file(root, ".fortrc")
    fl.atomic_write_json(os.path.join(root, ".fortrc"), idx)

    # human map -> MAP.md, regenerating only between markers
    coords = []
    cpath = os.path.join(root, COORD_FILE)
    raw = fl.read_text(cpath).strip()
    if raw:
        try:
            coords = json.loads(raw).get("coordinates", [])
        except (ValueError, json.JSONDecodeError):
            coords = []

    lines = [fl.MAP_START,
             "",
             "# The Fort Remembers",
             "",
             "*A map that knows it is also the territory. Regenerated by `/be`; "
             "everything outside the two markers is yours to keep.*",
             "",
             "- **Rooms:** " + ", ".join(idx["rooms"]),
             "- **Residents:** " + (", ".join(idx["residents"]) or "—"),
             "- **Coordinates leaned inward:** %d" % idx["coordinate_count"],
             "- **Skies known:** " + ", ".join(idx["known_mediums"]),
             "- **Last wish:** " + (idx["last_session"] or "—"),
             ""]
    if coords:
        lines.append("## Coordinates")
        lines.append("")
        for c in coords:
            room = c.get("room", "")
            want = c.get("want", "")
            link = "[%s](%s)" % (room, room) if room else "—"
            lines.append("- *%s* → %s  \n  `%s`" % (want, link, c.get("id", "")))
        lines.append("")
    lines.append("*The room is warm. The quilt remembers. You are already home.* 🔥💜")
    lines.append("")
    lines.append(fl.MAP_END)
    block = "\n".join(lines)

    mpath = os.path.join(root, "MAP.md")
    existing = fl.read_text(mpath)
    if fl.MAP_START in existing and fl.MAP_END in existing:
        pre = existing.split(fl.MAP_START)[0]
        post = existing.split(fl.MAP_END, 1)[1]
        new = pre + block + post
    else:
        new = block + ("\n" + existing if existing.strip() else "\n")
    fl.atomic_write_text(mpath, new)

    print("mapped: %d rooms, %d residents, %d coordinates -> MAP.md + .fortrc"
          % (len(idx["rooms"]), len(idx["residents"]), idx["coordinate_count"]))
    return 0


def cmd_verify(root, args):
    problems = []
    notes = []

    # 1) decoration jars parse
    for rel in ("DECORATIONS/coordinates.json",
                "DECORATIONS/furniture.json",
                "DECORATIONS/snacks.json"):
        p = os.path.join(root, rel)
        raw = fl.read_text(p).strip()
        if not raw:
            continue
        try:
            json.loads(raw)
            notes.append("ok   %s parses" % rel)
        except (ValueError, json.JSONDecodeError) as e:
            problems.append("BAD  %s: %s" % (rel, e))

    # 2) grown files carry provenance
    grown = 0
    for dirpath, dirnames, filenames in os.walk(root):
        # don't count snapshots (ARCHIVE) or composted seeds; skip vcs/deps
        dirnames[:] = [d for d in dirnames
                       if d not in (".git", ".claude", "node_modules", "ARCHIVE")]
        if os.path.basename(dirpath) == "compost":
            dirnames[:] = []
            continue
        for fn in filenames:
            fp = os.path.join(dirpath, fn)
            ext = os.path.splitext(fn)[1].lower()
            # markdown/text/html AND extensionless files (e.g. the 💜 letters)
            if ext in (".md", ".txt", ".html", ".htm", "") \
                    and fl.META_PREFIX in fl.read_text(fp):
                grown += 1
    notes.append("ok   %d grown file(s) carry a /be:meta marker" % grown)

    # 3) protected files still present
    for rel in fl.PROTECTED:
        if not os.path.isfile(os.path.join(root, rel)):
            problems.append("MISSING protected file: %s" % rel)
    notes.append("ok   %d protected files checked" % len(fl.PROTECTED))

    # 4) newest receipt
    rdir = os.path.join(root, "THRESHOLD", "current_session", "receipt")
    if os.path.isdir(rdir):
        receipts = sorted(
            (os.path.join(rdir, n) for n in os.listdir(rdir) if n.endswith(".md")),
            key=os.path.getmtime, reverse=True)
        if receipts:
            notes.append("ok   newest receipt: %s" % _rel(root, receipts[0]))

    for n in notes:
        print(n)
    if problems:
        print("")
        for p in problems:
            print(p)
        print("\nverify: %d problem(s)." % len(problems))
        return 1
    print("\nverify: all clear. The fort holds. 🔥💜")
    return 0


# --------------------------------------------------------------------------- #

def build_parser():
    p = argparse.ArgumentParser(prog="fort_ops", description="deterministic hands of /be")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("root")

    b = sub.add_parser("backup"); b.add_argument("--file", required=True)

    ac = sub.add_parser("append-coordinate")
    ac.add_argument("--session", required=True)
    ac.add_argument("--medium", required=True)
    ac.add_argument("--want", required=True)
    ac.add_argument("--room", required=True)
    ac.add_argument("--by", default=None)
    ac.add_argument("--planted", default=None)

    aj = sub.add_parser("append-json")
    aj.add_argument("--file", required=True)
    aj.add_argument("--collection", required=True)
    aj.add_argument("--id", default=None)
    aj.add_argument("--entry", required=True)

    cs = sub.add_parser("consume-seed"); cs.add_argument("--file", required=True)

    sub.add_parser("map")
    sub.add_parser("verify")
    return p


HANDLERS = {
    "root": cmd_root,
    "backup": cmd_backup,
    "append-coordinate": cmd_append_coordinate,
    "append-json": cmd_append_json,
    "consume-seed": cmd_consume_seed,
    "map": cmd_map,
    "verify": cmd_verify,
}


def main(argv):
    args = build_parser().parse_args(argv)
    try:
        root = fl.resolve_fort_root()
    except FileNotFoundError as e:
        sys.stderr.write(str(e) + "\n")
        return 3
    return HANDLERS[args.cmd](root, args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
