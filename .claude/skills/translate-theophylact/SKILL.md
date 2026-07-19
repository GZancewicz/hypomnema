---
name: translate-theophylact
description: Translate Theophylact of Ohrid's Greek commentaries into literal modern English, marking supplied words in italics (KJV-style), footnoting ambiguity, and translating his own Greek rather than conforming to existing English Bibles. Use whenever translating any Theophylact source text (Gospel commentaries on Matthew/Mark/Luke/John, or later works) from the sectioned Greek .txt files into English.
---

# Translate Theophylact

Method for translating Theophylact of Ohrid's Greek commentary into literal modern
English. Confirmed with the maintainer; treat these decisions as **binding** for
every chapter so the corpus stays consistent across the whole project.

## When to use
- Translating any Theophylact Greek `.txt` (currently his Gospel commentaries in
  `texts/commentaries/theophylact/PG/sectioned/`; later, other Theophylact works).
- NOT for other authors — Chrysostom, Cyril, Bede, etc. have their own sources and
  conventions.

## Source & scope
- **Source:** cleaned Greek `.txt` files (CGPG OCR of Migne PG 123–124, ~99%
  accurate; residual OCR issues tracked in the corpus's `CLEANUP.md`).
- **Current unit:** the individual **kephalaia** (`ΚΕΦΑΛΑΙΟΝ_*.txt`) — the
  commentary proper. Front matter (`ΒΙΟΣ`, `ΤΑ_ΚΕΦΑΛΑΙΑ`, `ΠΡΟΟΙΜΙΟΝ`) is out of
  scope until the maintainer says otherwise.

## Core principles

### 1. Formal equivalence (word-for-word)
As literal as the target language allows:
- **Preserve Greek word order** where English tolerates it; accept some stiffness.
- **Render every particle** — `γὰρ`="for", `δὲ`="but/and", `οὖν`="therefore",
  `τοίνυν`="accordingly/then". Do not silently drop them.
- **`μὲν … δὲ` — do NOT render mechanically.** Default to a plain contrastive: render
  `δέ` as "but/whereas/and" and **leave `μέν` untranslated** where the `δέ`-clause
  already carries the contrast (the usual case). Reserve "on the one hand … on the
  other hand" for genuinely *balanced, emphatic* antitheses (a deliberate
  prophets-vs-Matthew, God-vs-man parallel), and use it **at most once per paragraph**.
  `μέν` is an untranslatable correlative whose force English normally carries by the
  contrastive alone; this is not a licence to drop `γάρ`/`δέ`/`οὖν`. Mechanical "on the
  one hand … on the other hand" was the single largest source of stiffness in the pilot.
- **Keep participles as participles** where possible ("having seen", "being about
  to") rather than smoothing into finite clauses.
- Prefer a consistent gloss for a recurring Greek word over stylistic variation.
- Goal is transparency to the Greek, not literary polish.

### 2. Supplied words in *italics* (KJV convention) — by a *materiality* threshold
English words **not represented in the Greek** but needed for sense may go in
**markdown italics** `*word*`. Apply this by whether the supplied word **carries
interpretive weight**, not to every word absent from the Greek — an all-or-nothing
rule floods the page with italics and hurts the rendered reading.
- **Italicize** (weight-bearing): implied subjects/objects that disambiguate; supplied
  nouns that are not obvious; supplied articles where the *lack* of an article is the
  point (`Book of *the* generation`); prepositions the Greek carries by case alone
  (`ἀνέβη εἰς τὸ ὄρος` → "he went up *into* the mountain"); reconstructed OCR words.
- **Leave roman** (routine): the ordinary copula "is/was/are" that English simply
  requires; pronoun subjects English grammar forces; trivial connective supplements
  ("that were", "to do", "who were") where nothing exegetical turns on them.
- A per-clause judgment call — done by the model, never automated. When in doubt
  whether a supplied word is weight-bearing, leave it roman.
- **Particles are present words, so their renderings are always roman, not italic** —
  including `μέν … δέ` however rendered (see Principle 1); do not italicize them.

### 3. Lemma vs. comment layout
Each chapter alternates **scripture lemmata** (Theophylact's `«…»` Gospel quotes)
with **exposition**. Keep them distinct:
- Each lemma as a **bold blockquote**: `> **Blessed are the poor in spirit.**`
- Exposition as plain prose paragraphs below.
- Mirrors how other Hypomnema commentaries anchor to verses; keeps verse structure
  recoverable.

### 4. OCR uncertainty — flag, never invent
Where the OCR'd Greek is **corrupt/ambiguous**:
- Mark `[?]` (or `[?word]` with a bracketed best-guess); add a brief note if useful.
- **Never** fabricate meaning from garbled text — a literal translation must expose
  gaps, not paper over them.
- If a whole lemma/clause is unrecoverable, translate what is legible, bracket the rest.

### 5. Translate Theophylact's Greek — NOT the received English Bible
Render the scripture lemmata **from the Greek Theophylact actually quotes**,
translated fresh; **do not conform them to any existing English Bible** (KJV, RSV,
NIV, Douay-Rheims, etc.).
- **Chronology.** He writes in 11th-c. Byzantium, ~1000 years after the NT, quoting
  the Greek as *he* received it; his exposition turns on *his* exact words, which can
  differ from modern critical or Reformation-era base texts. A familiar English
  wording severs the comment from the lemma it explains.
- **Translation bias.** Protestant and (less so) Catholic English versions encode
  later theological commitments in word choice; borrowing them smuggles post-schism,
  post-Reformation readings into a Byzantine Orthodox commentary.
- Rules: translate each lemma directly/literally from the Greek on the page even
  where it diverges from a well-known verse (**follow his text, not your memory of
  the verse**); let his reading govern key words so the comment still works; preserve
  genuine variants/paraphrase/conflation rather than "correcting" them; apply the
  same plain-Greek-sense caution to loaded vocabulary in the commentary itself.

### 6. Footnote genuine ambiguity — and quote the Greek
Distinct from Principle 4 (corrupt text): where the Greek is **legible but hard to
render or genuinely ambiguous**, do not silently pick one reading — **footnote it.**
- Trigger: more than one defensible translation; ambiguous syntax; a technical/
  theological term with no clean English equivalent; a pun/etymology/word-play lost
  in English; debatable sense; or a lemma diverging from the common text.
- In the note: state the difficulty plainly and **quote the original Greek** (the
  relevant word/phrase) so a later reader can check the choice; give alternative
  rendering(s) where relevant.
- Bias toward footnoting over flattening — "let the reader see the seams." Better an
  honest note than false certainty. Chosen translation stays in the body; discussion
  lives in the footnote.

## Conventions (apply uniformly)
- **Chapter header:** the Greek file's first line is `ΚΕΦΑΛ. <numeral>.`; open the
  `.en.md` with `# Chapter <arabic> (<Greek numeral>)` plus the Gospel and, where
  known, the corresponding KJV chapter.
- **Proper nouns:** conventional English biblical forms (Ἰησοῦς→Jesus, Ἰωάννης→John,
  Πιλάτος→Pilate), not transliteration.
- **Scripture citations:** where a lemma maps to a known verse, add the reference in
  brackets, e.g. `> **… (Matt. 5:3)**`. This is a **locator only** — never a licence to
  borrow that Bible's English wording (Principle 5).
- **Inline scripture locators (in the exposition):** for a bare, uncontroversial
  cross-reference Theophylact alludes to, put the locator **inline in parentheses** at
  the point of allusion — e.g. "A vision which Isaiah saw (Isa. 1:1)". Use a footnote
  only when the reference needs discussion (LXX-vs-MT, loose/conflated quotation, a
  textual point). Do not bury simple pointers in footnotes.
- **Inline identity glosses:** for a one-step identity/equivalence clarification, use an
  inline bracket — "Nave [i.e. Nun]", "christs [i.e. anointed ones]" — rather than a
  footnote. Reserve footnotes for genuine ambiguity, wordplay, or OCR reconstruction.
- **Recurring-term consistency:** gloss a recurring Greek word the **same way** in the
  lemma and in the exposition that expounds it, so the comment visibly tracks its key word.
- **Greek retained inline:** only when a word is discussed *as a word* (e.g. "the
  term *μακάριος* means…"); otherwise translate.
- **Footnotes:** markdown footnote syntax — `[^n]` marker in the body, `[^n]: …` at
  the file end. Quote Greek in polytonic script, optionally with transliteration/
  gloss. Number sequentially within each chapter file.
- **Register:** modern English, mildly formal, suited to a patristic commentary;
  avoid anachronistic idiom.

## Lemma structure (already split into folders)
A **lemma is the Gospel snippet Theophylact quotes (`«…»`) before commenting**; each
chapter is a chain of lemma→exposition. A lemma is **NOT 1:1 with a verse** — he
splits some verses into several lemmata (e.g. 5:1 → two) and sometimes a quote spans
verses. The chapters are already physically split into per-lemma folders:

```
ΕΡΜΗΝΕΙΑ/ΚΕΦΑΛΑΙΟΝ_05_Εʹ/
    ΚΕΦΑΛΑΙΟΝ_05_Εʹ.txt      full chapter (kept, source of truth)
    00_ΑΡΧΗ.txt              chapter header + titlos
    ΛΗΜΜΑ_01_5.1/            one folder per lemma  (ΛΗΜΜΑ_NN_<chapter>.<verse>)
        ΛΗΜΜΑ_01_5.1.txt     the Greek lemma + its exposition
    ΛΗΜΜΑ_02_5.1/ …
```
- Produced by `scripts/split_lemmata_to_files.py` (boundaries at his `«` marks +
  gap-fill; verse tags via a forward-window cursor, monotonic per chapter). 5,028
  lemma folders; byte-perfect (`00_ΑΡΧΗ` + lemma files == the kept chapter `.txt`).
- The folder-name verse (`5.1`) is the verse the lemma **draws from** — best-effort
  metadata, not authoritative; confirm/refine it as you translate.
- `sectioned/lemmata_index.json` is a per-chapter verse-**coverage** summary
  (`verses_covered`, `range`), matched against the Greek **Textus Receptus**
  (`texts/scripture/.../textus_receptus/<gospel>/<gospel>.txt`). ~98% coverage.

## Output — translate lemma by lemma
- For each lemma folder, write a **sibling `.en.md` inside it**, next to the Greek:
  `ΛΗΜΜΑ_01_5.1/ΛΗΜΜΑ_01_5.1.txt` → `ΛΗΜΜΑ_01_5.1/ΛΗΜΜΑ_01_5.1.en.md`.
- Render the lemma (its `«…»` scripture quote) as the bold blockquote and the
  exposition as prose (Principle 3). Tag the lemma with its verse ref — correcting the
  folder-name verse if the translation shows it's off. This yields exact per-lemma
  **verse coverage** as a byproduct — the same basis the other Hypomnema commentaries use.
- **Do not emit boilerplate for comment-less fragments.** When a lemma carries only
  scripture with no exposition (typical of genealogies), do **not** pad it with a
  "this lemma carries only the scripture text" / "subject carried over from the
  neighbor" paragraph. Where several *contiguous* fragments are all comment-less, render
  them as one continuous reading: give the first the full combined quote and its
  **verse range**, and let the absorbed siblings carry just their own scripture words
  (a bare blockquote, no explanatory paragraph). Keep any OCR reconstruction as a terse
  footnote. The value we add on such fragments is the reconstruction, not the sectioning —
  so the reader is never handed a barren, boilerplate-only page.

## Procedure (per chapter)
Two-pass, **independent verifier**:
1. **Translate** the Greek file per the principles above → write the `.en.md`.
2. **Verify** with a *separate* agent that re-checks English against Greek for:
   dropped/added clauses, mistranslation, dropped `γάρ`/`δέ`/`οὖν`, wrong italics (a
   real Greek word italicized, or a *weight-bearing* supplied word left roman — but
   routine copulas/forced pronouns/trivial articles should be roman, per Principle 2),
   mechanical `μὲν … δὲ` that should be lightened (Principle 1), **lemmata drifting
   toward KJV/standard-English phrasing** (Principle 5), simple scripture locators buried
   in footnotes that belong inline, and unflagged OCR gaps or un-footnoted ambiguities.
3. **Reconcile** the verifier's findings into the final file.

## Rollout
1. **Pilot one representative chapter first** (suggested: Matthew Εʹ, the Beatitudes
   — rich in short lemmata + exposition). Maintainer reviews real output and adjusts
   conventions before any scale-up.
2. Only then choose the mechanism for the full run (sequential vs. multi-agent
   workflow, one agent per chapter through a translate→verify pipeline).

## Model
Use the strongest available model (Opus) for **both** translation and verification —
literalness + italics + ambiguity judgment is reasoning-heavy. Do **not** use a
fast/small model.

## Automation note (multi-agent runs)
When scaling up via a workflow / many subagents, avoid a permission-prompt storm:
- **Run every subagent with `agentType: 'theophylact-scribe'`** (defined in
  `.claude/agents/theophylact-scribe.md`). That agent has **no Bash tool at all**, so it
  *cannot* emit a shell loop or `$(…)` substitution and therefore can never trigger a
  permission prompt — a structural guarantee that instructions alone did NOT achieve
  (agents ignored "don't use Bash" and used `for … do … done` loops anyway). This is the
  single most important rule for silent runs.
- **Agents must discover and read lemma files with the `Glob` and `Read` tools, and
  write output with the `Write`/`Edit` tools** — these are not permission-gated.
- **Never** have agents use `Bash` `for … do … done` loops, glob expansions, or `$(…)`
  command substitutions to inspect lemma folders. Claude Code can only auto-approve a
  shell line it can statically decompose into allowlisted sub-commands; loops and
  substitutions are non-decomposable, so they prompt **regardless** of any
  `Bash(cd:*)`/`Bash(ls:*)`/`Bash(cat:*)` allow rules. Tool-based file I/O sidesteps
  this entirely.
- **Only use `Bash` commands already allowlisted in `.claude/settings.local.json`.**
  Before a run, assume the user should never have to approve a command twice. If a run
  genuinely needs a shell command that is not yet in the `permissions.allow` list, **add
  it to `.claude/settings.local.json` first** (a single, tightly-scoped rule such as
  `Bash(<cmd>:*)`), rather than letting agents fire un-allowlisted commands that prompt
  the user over and over. Keep each new rule as narrow as the task allows. This applies
  to the orchestrator's own pre-flight `Bash` calls too, not just the subagents.
- The project keeps `Write`/`Edit`/`Read` allow rules scoped to `texts/**` (in
  `.claude/settings.local.json`) so file output never prompts. Note that "bypass
  permissions" mode is **not** offered in the VS Code extension's Shift+Tab cycle (it is
  a CLI-launch mode), so do not rely on it to silence prompts there.
