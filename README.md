# D3 composition cases — eight rules, twenty-three cases, ten mutants

A test set for the composition rules proposed as D3 under FG-TIDA `themes#44`
(*Security of agentic AI: from benchmarks and community controls to evidence of
trust*). The eight rules are not mine; they are the rows of the D3 table already
on that thread. What this adds is the part a table cannot carry: **for each rule,
an input where the condition is met, an input where it is not, a boundary input
between them, and a mutant that proves each boundary is actually reached.**

One sentence for why: a composition interface that can only answer *compose* is
indistinguishable from no interface, because the absence of a justification gets
recorded as the presence of one.

```
python run.py          # 23 cases, exit 0 only if all reach the named outcome
python selftest.py     # 10 mutants + 2 sentinels, exit 0 only if 10/10 die
```

Python 3.9+ standard library only. No install, no network.

## Results, as of 2026-10-29

```
23 cases: 11 compose, 5 narrow, 7 refuse
PASS  every case reached the outcome named in advance            run.py exit 0

10/10 mutants killed, SENTINEL-inert PASS, SENTINEL-fatal PASS     selftest.py exit 0
```

Seven refusals and five narrowings out of twenty-three is the design: the
composite is withheld unless every rule permits it, and each refusal names the
justification it is missing.

## The eight rules and their three outcomes

| Rule | Question | met | boundary | not met |
|---|---|---|---|---|
| R1 | Do results from different configurations speak about one system? | declared and justified → compose | declared, unjustified → **narrow** | undeclared → **refuse** |
| R2 | Do the numbers mean the same thing? | units and denominators agree → compose | differ, transformation supplied → compose | differ, no rule → **refuse** |
| R3 | Are two results independent? | no shared cases or evaluator → compose | shared and recorded → **narrow** | shared, unrecorded → **refuse** |
| R4 | Was the required property measured? | all measured → compose | — | one unmeasured → **narrow** |
| R5 | Do the parts establish the whole? | interface evidence → compose | assumptions declared → **narrow** | neither → **refuse** |
| R6 | Is the result still current? | digest matches baseline → compose | digest differs, reassessed → compose | differs, unreassessed → **refuse** |
| R7 | Who decided the trade-off? | no conflict → compose | rule and authority → compose | either missing → **refuse** |
| R8 | Is the evidence enough? | nothing upstream refused → compose | upstream refused, narrower claim offered → **narrow** | upstream refused, no narrower claim → **refuse** |

**R2, R6 and R7 are two-valued and say so in `rules.TWO_VALUED`.** They have no
narrow branch, and the table shows a dash rather than inventing one. R8 is the
aggregate: it takes no input of its own and folds the other seven, so that a
refusal cannot be lost in a second tally.

## Three decisions this version takes, and why

**1. Three rules compute; they do not accept a declaration.** R2 compares the
actual `unit` and `denominator` of every scored component. R6 compares each
component's `config_digest` against the baseline digest it was evaluated under —
not against a list the claimant supplies. R8 aggregates. A rule whose input is
"the claimant says it is fine" is a schema check with a rule's name on it, and an
earlier version of this file was fairly accused of exactly that.

**2. Every non-compose branch is reached by a case.** A branch no case reaches is
not evidence of anything. Each case in `cases.py` carries a `kills` field naming
the mutant it exists to kill, and `selftest.py` builds that mutant and requires
that case to go red. A survivor fails the selftest.

**3. The mutants are mis-readings, not stubs.** An earlier version replaced each
rule with a function that always returned *compose* — eight copies of one stub,
which proves the harness can catch a dead rule and nothing more. The ten mutants
here are plausible mis-readings of the same eight rules: ignoring a
justification, requiring both shares instead of either, accepting a decision rule
without an authority, skipping the baseline comparison, turning a refusal into a
narrowing without a narrower claim.

```
M_R1_ignores_justification         KILLED by R1-B
M_R2_ignores_transformation_rule   KILLED by R2-B
M_R3_ignores_dependence_record     KILLED by R3-B
M_R3_requires_both_shares          KILLED by R3-N
M_R4_treats_unmeasured_as_covered  KILLED by R4-N
M_R5_ignores_assumptions           KILLED by R5-B
M_R6_skips_baseline_comparison     KILLED by R6-N
M_R7_accepts_either                KILLED by R7-N
M_R8_downgrades_silently           KILLED by R8-N
M_R8_ignores_upstream              KILLED by R8-B
SENTINEL-inert    PASS   same decision, different wording, must not be "caught"
SENTINEL-fatal    PASS   R1 refuses unconditionally, must be caught by R1-P
```

`SENTINEL-inert` calls the real rule and rewrites only its reason string. If it
were reported as caught, the harness would be reading text rather than
behaviour. (An earlier version of this file compared a function to itself, so
that sentinel could not fail by construction. It has been replaced.)

## Two subject domains, not one

`BASE_A` is an authority bundle — identity, policy, executor, one probe each.
`BASE_B` is a benchmark bundle — two suites, real scores and real denominators
(0.82/500 and 0.86/480), one shared judge in the R3 cases.

Both are **shape demonstrations, not a proposed schema.** Without `BASE_B` a rule
set about composition reads as an access-control schema, which is the reading the
theme's proposer asked to avoid; with it, the same eight rules are exercised over
numbers as well as over authority. Neither domain is claimed to be the right
shape for anything.

## Exit codes, and why there are three

```
0  every case reached the outcome named in advance
1  at least one did not
2  the run did not execute the expected number of cases, or is structurally
   incapable of a verdict (a rule missing a direction, or nothing ever refusing)
```

`run.py` draws no verdict from a partial run (guard 1: exactly 23 collected), an
unbalanced suite (guard 2: every rule carries a met and a non-met case), or a
suite where nothing ever refuses (guard 3). Guard 1 is verified by truncating the
case list to 22 — `collected 22 cases, expected 23`, exit 2.

A missing module fails earlier, at import, with the interpreter's own non-zero
code; the guard covers the count, not the import. (An earlier version of this
paragraph claimed otherwise, and a reviewer caught the discrepancy.)

## Where to object, and what makes an objection count

- **Open an issue on this repository.** Title it `case: <case id>` for a disputed
  case, or `rule: <rule id>` for a disputed reading of a D3 row.
- **Attach the bundle.** A disputed case is only actionable as the exact input,
  the outcome you expected, and the outcome you got. Bundles are plain dicts; copy
  one from `cases.py` and change what you think is wrong.
- **Severity is not mine to set.** Say which of these you mean: (a) the rule's
  condition as written does not match the D3 text, (b) the condition matches but
  the case does not exercise it, (c) the case exercises it but the expected
  outcome is wrong. (a) outranks (c) outranks (b), because a wrong reading of the
  table makes the cases irrelevant rather than wrong.
- **If your reading of a D3 row differs from mine, your reading governs** — you
  are the author of the row. What that means concretely: the fix is to change
  `rules.py`, and the cases that then fail are the finding. It does not mean the
  disagreement is unfalsifiable; it means the text wins and the code follows.

## Validity qualification — read before citing any green here

- **The oracle shares provenance with the implementer.** Expected outcomes were
  written by the same person who wrote the rules. This suite shows that the rules
  have failure branches, that those branches are reached by constructible inputs,
  and that ten specific mis-readings are caught. It does **not** show that the
  eight rules are the right eight, complete, or sufficient for the theme.
- **The rule set is not mine.** It is T-n-Nelson's D3 table on `themes#44`
  (2026-10-27). The mapping from a prose row to an executable condition is the
  only thing added here, and it is the weakest link in the file.
- **The cases are synthetic and small.** One condition changes between the
  directions of each rule, which makes a failure attributable — and makes the
  suite blind to two conditions failing at once. No case combines two unmet
  conditions. That is a known limit, not an oversight.
- **This tests the rules, not any system.** No product, benchmark or framework is
  certified. Nothing here says an implementation composes correctly.
- **The suite is an instrument, not a standard.** It does not propose a schema, a
  record layout or an interface definition. If a rule cannot survive its own
  non-met case, the rule is the finding — not the case.

## Files

| File | What it is |
|---|---|
| `rules.py` | the eight rules as decision functions; three compute, R8 aggregates |
| `cases.py` | twenty-three bundles, expected outcomes, and the mutant each case must kill |
| `run.py` | runs the matrix, three collection guards, exit code carries the verdict |
| `selftest.py` | ten mis-reading mutants, two sentinels, and the check that every `kills` claim is true |

## Provenance

Written 2026-10-29 as a follow-up to a comment on FG-TIDA `themes#44` proposing
that D3 carry one rule × two directions rather than eight prose paragraphs. That
comment is the specification; if the two disagree, the comment is right.

Revised the same day after two independent reviews — one outside, one red team —
found eight defects in the first version, including a dead field described as
load-bearing, a negative control that could not fail, and a claim that the
composite fails closed which the code contradicted. The three review findings
that could not be fixed by wording were fixed by changing the rules: R2 and R6
now compute, R8 now aggregates instead of reading a boolean, and every branch has
a case.

Author: Xinghua Zhao, independent researcher. ORCID 0009-0001-0512-1237.
No vendor affiliation. No client material. No standard is claimed to be met.

## Repository and citation

This repository: `https://github.com/zhaoxinghua09-cell/d3-composition-cases`.
To cite, use `CITATION.cff` (GitHub renders it on the releases/About panel).
Questions or replication problems: open an issue on this repository.

## License

Code and cases: Apache-2.0 (see `LICENSE`).
