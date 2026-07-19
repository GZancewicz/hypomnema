---
name: compare-theophylact-stade
description: Compare our Theophylact translation of a lemma (or verse/passage) against the Stade / Chrysostom Press benchmark translation, using the Greek as arbiter — to QC our rendering, catch real errors, and confirm reconstructions. Use whenever the maintainer wants to check, benchmark, or "compare with Stade" one or more Theophylact lemmata.
---

# Compare Theophylact translation vs. Stade (Chrysostom Press)

Benchmark our own Theophylact `.en.md` against Fr. Christopher Stade's published
translation (Chrysostom Press). Stade rendered the **same Greek** (Migne PG 123) that
our CGPG OCR comes from, so his text is an excellent second opinion for QC.

## The one rule that governs everything
**The Greek is the arbiter. Stade is a reference, not ground truth.** Our
[translate-theophylact](../translate-theophylact/SKILL.md) method *deliberately*
diverges from Stade, so **divergence is not by itself an error.** Two settled,
principled differences you will see constantly and must NOT flag as our bug:
1. **Lemma wording.** Stade conforms the Gospel snippets to received/KJV-style English;
   we translate Theophylact's *own* quoted Greek fresh (Principle 5). A lemma that
   differs from Stade toward his Greek is correct; a lemma of *ours* that has drifted
   toward KJV/standard-English phrasing is *our* bug.
2. **Register.** Stade smooths into fluent English; we keep formal-equivalence
   literalness (particles rendered, participles kept, Greek word order). Our being more
   literal than Stade is expected — flag it only when literalness produced an actual
   **error** or genuinely broken English, not merely stiffer prose.

So the job is not "make ours look like Stade." It is: use Stade to surface places where
**ours is actually wrong against the Greek**, and to **confirm** ours where the two
independent renderings agree.

## When to use
- The maintainer asks to compare / benchmark / "check against Stade" one lemma, a verse,
  or a short passage of Theophylact.
- As a QC pass after translating a chapter, spot-checking representative lemmata.
- NOT for other authors (Chrysostom/Cyril/Bede) — this benchmark is Theophylact-only.
- **Stade benchmark currently exists for Matthew only** (git-ignored under
  `texts/commentaries/theophylact/benchmark/`). For Mark/Luke/John the helper says so;
  there is nothing to compare against yet.

## Retrieve the material (one command)
Use the helper — it prints the Greek, our `.en.md`, and Stade's block together:
```
python3 scripts/compare_lemma.py --gospel matthew --ch 5 --verse 3
# or point at a lemma folder / its .txt:
python3 scripts/compare_lemma.py --lemma texts/commentaries/theophylact/PG/sectioned/ΚΑΤΑ_ΜΑΤΘΑΙΟΝ/ΕΡΜΗΝΕΙΑ/ΚΕΦΑΛΑΙΟΝ_05_Εʹ/ΛΗΜΜΑ_06_5.3
```
- By `--verse`, it pulls **every** lemma folder our side tagged to that verse.
- A lemma may span verses (our `ΛΗΜΜΑ_07_5.4` covers 5:4–5); Stade splits per verse.
  When our lemma covers a range, run the helper **once per verse** in the range so you
  have each Stade block.
- Read the whole bundle. The Greek is OCR — where it is garbled, agreement between ours
  and Stade helps **confirm a reconstruction**, but where Stade's received text
  genuinely differs from Theophylact's Greek, follow the Greek, not Stade.

## Comparison rubric — judge each divergence against the Greek
Walk the two exposition renderings clause by clause. For every real divergence, classify:

| Verdict | Meaning | Action |
|---|---|---|
| **OURS-ERROR** | Ours misreads/drops/adds vs. the Greek; Stade is right | propose a fix to our `.en.md` |
| **OURS-DRIFT** | Our *lemma* has slid toward KJV/standard English (Principle 5 violation) | propose re-rendering from his Greek |
| **STADE-LOOSE** | Stade paraphrases, smooths away a particle, conforms the lemma, or is looser than the Greek; ours is closer | none — this *confirms* ours |
| **BOTH-OK** | Legitimate stylistic/methodological difference, both faithful | none |
| **OCR-CONFIRM** | The two agree and thereby validate our reading of a garbled Greek word | note; consider firming a `[?]`/footnote |
| **GAP** | One side comments on a clause the other omits — check the Greek to see who dropped it | if *ours* dropped real Greek → OURS-ERROR |

Specifically check: dropped/added clauses; a rendered `γάρ`/`δέ`/`οὖν` that ours lost;
sense of key theological terms; scripture-locator accuracy; and whether an OCR gap we
flagged is resolved by Stade's cleaner text.

## Output
Report concisely in chat (this skill is **read-only analysis** — do not edit `.en.md`
unless the maintainer then asks):

1. **Verdict line** — e.g. *"Ours faithful; 1 OURS-ERROR, 2 STADE-LOOSE, rest agree."*
2. **Divergences** — a short list, each: the clause, ours vs. Stade, the Greek that
   settles it, and the verdict tag above. Quote the Greek word/phrase at issue.
3. **Action items** (only if any OURS-ERROR / OURS-DRIFT) — the concrete change to our
   `.en.md`, phrased so it can be applied under the translate-theophylact conventions.
   If none: say "no changes to ours indicated."

Keep it tight — the goal is actionable QC signal, not a full re-translation writeup.

## If asked to then fix
Switch to the [translate-theophylact](../translate-theophylact/SKILL.md) conventions to
edit the `.en.md` (italics/footnote/particle rules all apply). Never paste Stade's
wording into our file — his translation is in-copyright and our rendering must come from
the Greek. Stade only tells you *where* to look, never *what words* to use.
