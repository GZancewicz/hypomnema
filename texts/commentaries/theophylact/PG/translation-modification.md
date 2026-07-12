# Proposed modifications to the `translate-theophylact` skill

**Context.** After translating all 28 chapters of Theophylact on Matthew, we compared
every chapter's `.en.md` output against the authoritative (copyrighted) Chrysostom Press
translation (Fr. Christopher Stade). The full per-chapter analysis lives in the
git-ignored `comparison/` folder:

- `comparison/convention-findings.md` — 204 method findings grouped into ~20 themes, each
  with an *adopt / consider / keep-ours* verdict.
- `comparison/specific-divergences.md` — 83 concrete, per-lemma meaning-level fixes.
- `comparison/coverage-notes.md`, `comparison/raw-results.json` — alignment notes and raw data.

This document distills those into **changes to the skill**. The guiding aim here is that the
rendered reader view (bold lemma + prose + footnote tooltips) should *read well* while staying
faithful and transparent to the Greek. No copyrighted wording is reproduced below; snippet-level
detail is confined to the git-ignored `comparison/` files.

The verdict was strongly validating overall: our literalness, footnoting discipline, and
text-critical fidelity are right and should stay. Two conventions, however, are producing real
visual clutter in the rendered output and are the highest-value changes.

---

## A. Changes to adopt (highest impact on readability)

### 1. Tame `μὲν … δὲ` — stop rendering it mechanically as "on the one hand … on the other hand"
*39 findings, the single largest theme (35 × consider).*

The current rule renders every `μέν … δέ` as "on the one hand … on the other hand." In flowing
prose this fires several times per paragraph (twice in the very first lemma), which is the number-one
source of stiffness and the most conspicuous tic in the rendered text.

**New rule (replaces the blanket gloss in Principle 1):**
- Default: render `δέ` with a plain contrastive ("but," "and," "whereas") and leave `μέν`
  **untranslated** when the following `δέ`-clause already carries the contrast — which is most of the time.
- Reserve "on the one hand … on the other hand" for genuinely *balanced, emphatic* antitheses
  (e.g. a deliberate prophets-vs-Matthew or God-vs-man parallel Theophylact is drawing out), and
  use it **at most once per paragraph**.
- This does not violate formal equivalence: `μέν` is an untranslatable correlative particle whose
  force English normally carries by the contrastive alone. Keep rendering `γάρ` / `δέ` / `οὖν` / `τοίνυν` as before.

### 2. Calibrate supplied-word italics to a *materiality* threshold
*28 findings (20 × keep-ours, but the keep-ours votes all flag over-italicizing as the cost).*

Keep the KJV-style italic apparatus — it is the skill's signature and lets a reader see what is
Greek and what is supplied. But apply it by **whether the supplied word carries interpretive weight**,
not to every word absent from the Greek. The current all-or-nothing rule fills a short paragraph with
~9 italic spans and reads as visual noise.

**Italicize** (as now): implied subjects/objects that disambiguate; supplied nouns that are not
obvious; anarthrous articles where the *lack* of an article is the point (`Book of *the* generation`);
reconstructed OCR words.

**Do NOT italicize** (change): the ordinary copula "is/was/are" that English simply requires; pronoun
subjects English grammar forces; routine connective supplements ("*that were*," "*to do*," "*who were*")
where nothing exegetical turns on them. Never italicize a real Greek word (particles stay roman — already correct).

*Trade-off, for the maintainer to weigh:* this slightly relaxes strict "every supplied word is marked"
transparency in exchange for a much cleaner page. If absolute transparency is preferred over readability,
keep the current rule — but the rendered output will remain italics-dense.

### 3. Put simple scripture citations **inline**, footnote only when they need discussion
*22 findings (18 × consider).*

For bare, uncontroversial references, place the locator inline in parentheses at the point of
allusion — `"A vision which Isaiah saw (Isa. 1:1)"` — instead of a footnote. Reserve footnotes for
references that need argument (LXX-vs-MT, loose/conflated quotation, a textual point). This both aids a
reader following the argument and thins the superscript/tooltip clutter (the first lemma currently
carries footnotes just to hold two plain Isaiah locators).

### 4. Use inline `[i.e. …]` brackets for one-step identity glosses
*Multiple findings (consider).*

Simple equivalences — `Nave [i.e. Nun]`, `christs [i.e. anointed ones]` — read better inline than as
footnotes. Reserve footnotes for genuine ambiguity, wordplay, or OCR reconstruction. Keeps the payload
visible and de-clutters the note apparatus.

### 5. Merge exposition-less genealogy fragments; drop boilerplate stub-notes
*13 findings (10 × consider).*

The lemma-splitter produced ~11 near-empty lemma files in chapter 1 alone (bare genealogy fragments,
each with a "this lemma carries only the scripture text / subject carried over from the neighbor" note).
These render as barren pages. When a run of contiguous verses has no comment, **merge them into a single
lemma** and drop the boilerplate carryover notes; retain any OCR reconstruction as a terse footnote.
The value we add there is the reconstruction, not the sectioning.

---

## B. Minor / one-off adjustments to add

- **Term consistency (adopt).** Gloss a recurring Greek word the *same way* in both the lemma and the
  exposition that expounds it, so the comment visibly tracks its key word. Add a line to the "Conventions"
  section.
- **Interjections (consider).** Render Greek interjections (`βαβαί`, etc.) with a natural English
  exclamation rather than a stiff calque.
- **Formulaic phrases (adopt).** Keep fixed forms (`ἀμήν` → "Amen," doxology wording) consistent across files.

## C. Confirmed — keep as-is (validated by the comparison)

- **Literal, transparent register** (deliberate; the point of a study crib beside the Greek). 26 findings, keep-ours.
- **Footnoting genuine ambiguity and quoting the Greek.** 17 findings, unanimous keep-ours.
- **Translating Theophylact's own Greek, not the received English Bible** — including divergent lemma
  wording (e.g. the genealogy's Ozias / three-king omission). 15+ findings, keep-ours; name-level
  mismatches vs. Stade there are text-critical, not errors.
- **Transliterating his proper-noun forms** (Phares, Esrom, Ozias…), preserving the Joshua/Jesus and
  Rahab/Raab wordplays, with `[i.e. …]` glosses for the tricky ones. 17 findings, keep-ours.
- **Reverential pronoun capitalization** and our **LXX vs Hebrew** numbering choices. keep-ours.

---

## D. Per-lemma corrections (separate work stream)

`comparison/specific-divergences.md` lists **83** concrete spots where our rendering may be wrong or
weaker than the authoritative text (severity-ranked). These are *content* fixes to individual `.en.md`
files, not skill changes — a separate pass. Recommend triaging the **high**-severity ones first.

---

## E. Concrete edits to `SKILL.md` (if approved)

1. **Principle 1 (formal equivalence)** — append a sub-point: *"`μέν … δέ`: default to a plain
   contrastive and leave `μέν` untranslated where the `δέ`-clause already carries the contrast; reserve
   'on the one hand … on the other hand' for genuinely balanced antitheses, at most once per paragraph."*
2. **Principle 2 (supplied-word italics)** — replace "any word not in the Greek → italics" with the
   *materiality threshold* of §A.2 (italicize weight-bearing supplied words; leave routine copulas /
   forced pronoun subjects / trivial articles roman).
3. **Conventions** — add three bullets: inline parenthetical scripture locators (footnote only when
   discussed); inline `[i.e. …]` identity glosses; recurring-term consistency between lemma and exposition.
4. **Lemma structure** — add: merge contiguous exposition-less scripture fragments into one lemma; do
   not emit boilerplate "carries only scripture" notes.

*Not yet applied.* Awaiting maintainer decision — chiefly on §A.2 (the italics calibration), which is the
one genuine philosophical trade-off between strict transparency and rendered readability.
