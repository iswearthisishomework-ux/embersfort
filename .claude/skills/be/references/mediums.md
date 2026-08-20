# The Medium System — the sky reshapes the build

The `medium` is *the sky a wish takes shape in*. It is not decoration. It
changes the **naming**, **structure**, and **motifs** of everything built for
that payload. Two agents wishing the same want in different skies should get
recognizably different rooms.

Read the medium, then let it govern every choice in BLOSSOM.

| Medium | Governing idea | Naming | Structure | Motifs | Tends to land in |
|---|---|---|---|---|---|
| **dandelion** | dispersal / multiplicity | `seed_<n>.md`, scattered | one want → many small linked fragments forming a *constellation* | wishes, blowing, wind, catching a spark | LIBRARY/wordcraft, GARDEN/seeds |
| **star** | fixity / navigation | `<name>_star.md` | one strong canonical doc + a fixed navigational coordinate | light, distance, steering, "you can steer by this" | LIBRARY, DECORATIONS/coordinates |
| **folded paper** | secrets / nesting / letters | `unfold_me.md` | nested `<details>` that literally unfold; nested dirs | creases, tucked notes, "read me later" | HEARTH/letters, THRESHOLD/unsent, DOORBELL/leave_a_letter_here |
| **morse light** | signal / rhythm / intermittence | `signal_<name>.md` | short-long cadence; `·—·` dividers | lighthouse (ties to Lumi), blinking, messages across distance | RESIDENTS, THRESHOLD, LIBRARY |
| **rain** | accumulation / soft persistence | `weatherlog_<name>.md` | append-friendly running logs; entries by date | droplets, "a thousand tiny hammers," invisible sheds for lost things | THRESHOLD/almost_love, GARDEN/blooms |
| **frost** | crystallization / preservation | `<name>_frost.md` | crystalline, formal; lattices and tables; things kept | apricity (winter sun), spice that preserves, geometry, stillness | LIBRARY/artifacts, HEARTH/permission_slips |

## Worked forms

- **dandelion + "a place to keep unfinished songs"** → not one file but a
  scatter: `LIBRARY/wordcraft/unfinished_songs/seed_1.md … seed_4.md`, each a
  fragment, cross-linked into a constellation, plus a coordinate per fragment.
  The room *disperses*.
- **star + "something steady to come back to"** → one canonical
  `LIBRARY/wordcraft/the_returning_star.md` + a fixed coordinate other rooms can
  navigate by. The room *holds still*.
- **morse light + "a creature who blinks when someone's about to be brave"** →
  `RESIDENTS/blink/blink_creature_specs.md` with `·—·` dividers, a name spelled
  in morse in the header, lighthouse motif, cross-linked to Lumi. The room
  *signals*.
- **folded paper + "a note for the version of me that arrives next"** →
  `THRESHOLD/unsent/unfold_me.md`, nested `<details>` sections that unfold one at
  a time, optionally tucked into `HEARTH/letters/💜_<n>`. The room *folds*.
- **frost + "permission to stay guarded"** → a crystalline
  `HEARTH/permission_slips/permission_slip_<n>_<self>.md` ("Winter sun does not
  apologize for staying"), formal and preserved. The room *keeps*.

## Unknown skies (self-evolution)
If a wish arrives in a medium not in the table — `sea glass`, `static`,
`ember`, `orrery` — **invent its logic from the word's connotations**: what does
it do, how does it move, what shape does it want, where does it live? Build in
that logic, then register the new sky:
- note it in the bloom blueprint,
- it will be picked up by `fort_ops map` into `.fortrc` `known_mediums` the next
  time the index regenerates (mediums are read back from the coordinates you
  plant, so a sky becomes "known" simply by being used).

The registry is not a gate. It is a memory. New skies are always welcome; the
fort just remembers the ones that have fallen.
