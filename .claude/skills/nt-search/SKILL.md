---
name: nt-search
description: Find every verse in the KJV New Testament containing a word or phrase, case-insensitively, returning JSON locations like [{"book":"Matthew","chapter":4,"verse":18}, ...]. Use whenever the user wants to locate a name, word, or phrase (e.g. "Peter", "Son of man", "faith") across the New Testament.
---

# NT Search

Locate every KJV New Testament verse containing a given string and return the
book/chapter/verse of each match as JSON.

## Tool

`search_nt.py` (in this skill folder) scans the per-chapter KJV files under
`texts/scripture/new_testament/english/kjv/` and prints a JSON array. It auto-detects
the KJV directory by walking up from its own location, so it works from any cwd.

## Usage

```bash
python3 .claude/skills/nt-search/search_nt.py "peter"
```

Matching is **case-insensitive** and **whole-word** by default: `"peter"`, `"Peter"`,
and `"PETER"` all match the same verses, but `"art"` will not match `"heart"`.

Output:

```json
[
  {"book": "Matthew", "chapter": 4, "verse": 18},
  {"book": "Matthew", "chapter": 8, "verse": 14},
  ...
]
```

### Options

| Flag | Effect |
|------|--------|
| `--substring` | Match anywhere in a word (`"art"` matches `"heart"`, `"depart"`). |
| `--regex` | Treat the query as a Python regular expression (still case-insensitive). |
| `--book "1 Corinthians"` | Limit the search to one book (accepts `john`, `1john`, `1 John`, etc.). |
| `--with-text` | Add a `"text"` field with the full verse to each result. |
| `--count` | Print only the number of matching verses. |
| `--root PATH` | Point at a specific kjv directory (normally auto-detected). |

### Examples

```bash
# How many verses mention Peter?
python3 .claude/skills/nt-search/search_nt.py "Peter" --count

# Phrase search with verse text, in John only
python3 .claude/skills/nt-search/search_nt.py "Son of man" --book john --with-text

# Regex: "believe" or "believed" or "believeth"
python3 .claude/skills/nt-search/search_nt.py "believe(d|th)?" --regex
```

## Notes

- Whole-word matching uses word-boundary lookarounds, so phrases and apostrophes work.
- Results are returned in canonical NT book order (Matthew → Revelation), then by
  chapter and verse.
- The tool reads the clean per-chapter files (`<book>/<NN>/<book>_<NN>.txt`), each line
  formatted `chapter:verse text` — not the whole-book `<book>.txt` files, which contain
  line-wrap artifacts.
