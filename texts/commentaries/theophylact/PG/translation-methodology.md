# Theophylact — Translation Methodology

The translation methodology now lives in a reusable skill so it applies to **all**
Theophylact translation work, not just PG 123–124:

**→ `.claude/skills/translate-theophylact/SKILL.md`** (canonical — edit there).

Invoke it with `/translate-theophylact` (or it triggers automatically when
translating Theophylact Greek `.txt` files).

## Quick summary of the binding decisions
1. **Formal equivalence** — word-for-word, particles rendered, participles kept.
2. **Supplied words in *italics*** (`*word*`, KJV-style).
3. **Distinct lemma + comment** — scripture lemma as bold blockquote, exposition as prose.
4. **OCR gaps: flag `[?]`, never invent.**
5. **Translate Theophylact's own Greek — not any existing English Bible** (chronology + translation-bias reasons).
6. **Footnote genuine ambiguity and quote the Greek.**
- Output: sibling `.en.md` files, 1:1 with the Greek.
- QC: two-pass with an independent verifier.
- Rollout: pilot one chapter (Matthew Εʹ) first, then scale.

See the skill for the full rules, conventions, and procedure.
