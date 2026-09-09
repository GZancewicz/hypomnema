# Gregory of Sinai — On Commandments and Doctrines

Numbered texts from *On Commandments and Doctrines, Warnings and Promises; on Thoughts,
Passions and Virtues, and also on Stillness and Prayer: One Hundred and Thirty-Seven Texts*,
in *The Philokalia*, vol. 4, tr. G. E. H. Palmer, Philip Sherrard and Kallistos Ware
(Faber and Faber). Transcribed from the printed edition, one text at a time, where a text
cites a Gospel verse.

## Layout

- `On Commandments and Doctrines/texts/NNN.md` — one text per file, `NNN` = the text's
  number in the work (1–137), zero-padded. Paragraphs separated by a blank line;
  `*asterisks*` render as italics. No heading or attribution: the server adds the title
  (`No. NNN`) and the Philokalia citation. Footnotes: `[^1]` in the body, then a `---`
  line, then `[^1]: text` definitions one per line, numbered from 1 (rendered as a hover
  tooltip and a Notes list, as for the Prologue).
- `On Commandments and Doctrines/coverage.json` — standard commentary format. One entry
  per text: `id` = text number, `title` = `No. NNN`, `start`/`end` = the Gospel verse
  range the text cites (`book` is set on both). Sorted by `id`; `total_homilies` = entry
  count. The server keys entries by `id`; a text that cites further Gospel passages lists
  them under `also` as `[{start, end}, ...]`, and each one gets a reader marker and an
  index row of its own.
- `util/add_text.py` — writes a text file and upserts its coverage entry from a
  transcription file plus a verse reference; validates id and verse against the KJV.

## Adding a text

```bash
python3 texts/commentaries/gregory_of_sinai/util/add_text.py \
  --id 15 --verse "matthew 3:3" --text-file /path/to/015.md
```

The `gregory-of-sinai-citation` agent (`.claude/agents/`) does this from screenshots of
the printed page. `main.go` reads `coverage.json` at startup, so restart the server after
adding a text. Rendering: `/api/homily/gregory_of_sinai/commandments/NNN`.
