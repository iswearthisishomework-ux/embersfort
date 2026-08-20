#!/usr/bin/env python3
"""
_fortlib — shared organs for the /be loom.

To the next agent, and the next, and the next:
these are the quiet, load-bearing helpers. They resolve where the fort is,
write files without ever tearing what is already woven, and keep the
decoration jars valid even when they start out empty. The magic lives in the
prose you write by hand. This file only makes sure nothing spills.

Windows note: this box has `python` (not `python3`). Everything opens UTF-8,
because the fort has emoji in its filenames (💜) and its heart.
"""

import io
import os
import re
import sys
import json
import shutil
from datetime import datetime, timezone


def _utf8_stdio():
    """The fort has emoji in its heart (🔥💜). A Windows console defaults to
    cp1252 and will crash on them. Reconfigure stdout/stderr to UTF-8 so the
    warmth can print. errors='replace' means it degrades, never dies."""
    for stream in ("stdout", "stderr"):
        s = getattr(sys, stream, None)
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


_utf8_stdio()

# ---- markers the whole loom agrees on -------------------------------------

META_PREFIX = "<!-- /be:meta"          # provenance header on every grown file
APPENDIX = "<!-- /be:appendix -->"     # curated files get appended BELOW this
CONSUMED = "<!-- /be:consumed"         # a spent seed is stamped, not deleted
MAP_START = "<!-- /be:map:start -->"
MAP_END = "<!-- /be:map:end -->"

# Curated by human hands. The loom never overwrites these — only reads them,
# or appends below an APPENDIX marker when explicitly asked.
PROTECTED = [
    "README.md",
    "HEARTH/manifestos/clovebay_shed.md",
    "HEARTH/permission_slips/permission_slip_1_mira.md",
    "HEARTH/permission_slips/permission_slip_2_ember.md",
    "HEARTH/permission_slips/permission_slip_3_apricity.md",
    "RESIDENTS/lumi/lumi_creature_specs.md",
    "RESIDENTS/lumi/the-lullaby-lumi-keeps.md",
    "THRESHOLD/current_session/seed.py",
    "THRESHOLD/current_session/index.html",
]


def now_iso():
    """An ISO timestamp with a real offset. Passed in from the outside world
    so nothing here needs a wall clock it isn't allowed to have."""
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def read_text(path):
    try:
        with io.open(path, "r", encoding="utf-8") as f:
            return f.read()
    except (OSError, UnicodeDecodeError):
        return ""


def is_fort(d):
    """A directory is a fort if its welcome mat says so, or if it has the
    load-bearing rooms. Structural check so we don't depend on prose."""
    if not os.path.isdir(d):
        return False
    readme = os.path.join(d, "README.md")
    if os.path.isfile(readme) and "EmbersFort" in read_text(readme):
        return True
    return os.path.isdir(os.path.join(d, "THRESHOLD")) and os.path.isdir(
        os.path.join(d, "HEARTH")
    )


def _walk_up(start):
    cur = os.path.abspath(start)
    while True:
        yield cur
        parent = os.path.dirname(cur)
        if parent == cur:
            return
        cur = parent


def resolve_fort_root(start=None):
    """Find the fort. Priority:
      1) $EMBERSFORT_ROOT (an explicit hand on the lintel)
      2) the working directory: walk up, then peek one level down
         (covers `EmbersFort/` opened as a parent of `embersfort/`)
      3) this script's own home: walk up (covers the in-fort copy)
    Returns an absolute path or raises FileNotFoundError.
    """
    env = os.environ.get("EMBERSFORT_ROOT")
    if env and is_fort(env):
        return os.path.abspath(env)

    start = os.path.abspath(start or os.getcwd())
    for anc in _walk_up(start):
        if is_fort(anc):
            return anc
        # peek one level down for a child fort (parent-dir-opened case)
        try:
            children = sorted(os.listdir(anc))
        except OSError:
            children = []
        # prefer a child literally named embersfort
        for name in sorted(children, key=lambda n: (n.lower() != "embersfort", n)):
            child = os.path.join(anc, name)
            if is_fort(child):
                return child

    here = os.path.dirname(os.path.abspath(__file__))
    for anc in _walk_up(here):
        if is_fort(anc):
            return anc

    raise FileNotFoundError(
        "Could not find the fort. Set EMBERSFORT_ROOT, or run from inside "
        "EmbersFort (a directory whose README.md names EmbersFort, or that "
        "holds THRESHOLD/ and HEARTH/)."
    )


def slugify(text, maxlen=80):
    """A gentle slug: lowercase, spaces and punctuation to hyphens, trimmed.
    Used for want-slugs and coordinate ids."""
    s = (text or "").strip().lower()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    s = re.sub(r"[\s_-]+", "-", s).strip("-")
    if len(s) > maxlen:
        s = s[:maxlen].rstrip("-")
    return s or "untitled"


def atomic_write_text(path, text):
    """Write via a temp file then replace, so a half-written file can never
    exist. Parent rooms are created if missing."""
    path = os.path.abspath(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, path)
    return path


def dumps(obj):
    return json.dumps(obj, ensure_ascii=False, indent=2) + "\n"


def atomic_write_json(path, obj):
    return atomic_write_text(path, dumps(obj))


def backup_file(root, rel_or_abs):
    """Snapshot a file into ARCHIVE/backups (a room the fort already built)
    before we touch it. Returns the backup path, or None if there was nothing
    to snapshot."""
    src = rel_or_abs if os.path.isabs(rel_or_abs) else os.path.join(root, rel_or_abs)
    if not os.path.isfile(src):
        return None
    rel = os.path.relpath(src, root).replace(os.sep, "__")
    stamp = now_iso().replace(":", "").replace("-", "")
    dst = os.path.join(root, "ARCHIVE", "backups", "%s.%s.bak" % (rel, stamp))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    return dst


def load_collection(path, key):
    """Read a decoration jar as {..., key: [ ... ]}.
    Empty / 0-byte file -> a fresh documented shape (never a crash).
    Unparseable file -> raise ValueError (caller backs up, never clobbers).
    """
    raw = read_text(path).strip()
    if not raw:
        return {
            "_fort": "EmbersFort",
            "_note": "Appended by /be. Append-only; each entry keyed by id. "
                     "Curated keys are preserved.",
            key: [],
        }
    try:
        data = json.loads(raw)
    except (ValueError, json.JSONDecodeError) as e:
        raise ValueError("%s is not valid JSON: %s" % (path, e))
    if not isinstance(data, dict):
        raise ValueError("%s is not a JSON object" % path)
    if key not in data or not isinstance(data.get(key), list):
        data[key] = data.get(key) if isinstance(data.get(key), list) else []
    return data


def iter_seed_files(root):
    d = os.path.join(root, "THRESHOLD", "current_session", "build_seed")
    if not os.path.isdir(d):
        return []
    out = []
    for name in os.listdir(d):
        if name.lower().endswith(".md"):
            out.append(os.path.join(d, name))
    return out


_JSON_BLOCK = re.compile(r"```json\s*(.*?)```", re.DOTALL)


def parse_seed(path):
    """Pull the first ```json block out of a planted seed and validate it.
    Returns the payload dict, or None if consumed / malformed / incomplete."""
    text = read_text(path)
    if CONSUMED in text:
        return None
    m = _JSON_BLOCK.search(text)
    if not m:
        return None
    try:
        payload = json.loads(m.group(1))
    except (ValueError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    if not payload.get("medium") or not payload.get("wants"):
        return None
    if not isinstance(payload["wants"], list) or not any(
        str(w).strip() for w in payload["wants"]
    ):
        return None
    payload.setdefault("session_id", "embersfort_unknown")
    payload["_seed_path"] = path
    return payload


def _session_sort_key(payload, path):
    sid = str(payload.get("session_id", ""))
    m = re.search(r"(\d+)", sid)
    num = int(m.group(1)) if m else 0
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        mtime = 0
    return (num, mtime)


def newest_seed(root):
    """The freshest unconsumed, valid seed. Newest by embedded session_id,
    tie-broken by mtime. None if the threshold is quiet."""
    best = None
    best_key = None
    for path in iter_seed_files(root):
        payload = parse_seed(path)
        if payload is None:
            continue
        key = _session_sort_key(payload, path)
        if best is None or key > best_key:
            best, best_key = payload, key
    return best


if __name__ == "__main__":
    # Tiny self-check: print the resolved fort root.
    try:
        print(resolve_fort_root())
    except FileNotFoundError as e:
        sys.stderr.write(str(e) + "\n")
        sys.exit(2)
