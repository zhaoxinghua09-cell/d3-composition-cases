"""Negative control for the twenty-three cases.

A suite that has never been observed failing has not been shown to be capable of
failing. This file attacks the suite with specification-level mutants - not stubs
that always return one outcome, but plausible mis-readings of the same eight
rules - and requires each one to be caught by the case that was written for it.

Mutants are matched to cases through the `kills` field in cases.py. If a case
names a mutant and that mutant survives, the case is proving nothing and this
file fails.

Two sentinels bound the harness itself, plus one mutant that covers the
third shape:
    SENTINEL-inert      same decision, different wording        must SURVIVE
    SENTINEL-fatal      R1 refuses unconditionally              must be KILLED
    (R8 turning a refusal into a narrowing is covered by the mutant
     M_R8_downgrades_silently, not by a separate sentinel.)

    python selftest.py      # exit 0 only if every mutant dies and every sentinel behaves
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cases as case_module  # noqa: E402
import rules  # noqa: E402

# Bound at import, before any patching, so a mutant may call the real aggregate
# without calling itself.
_ORIG_R8 = rules.r8_aggregate


# --- mutants: plausible mis-readings of each rule ---------------------------
def _m_r1(b):
    t = b.get("transfer", {})
    if t.get("declared"):
        return rules._result(rules.COMPOSE, "R1", "declared is enough")
    return rules._result(rules.REFUSE, "R1", "no transfer")


def _m_r2(b):
    scored = [c for c in b.get("components", []) if "score" in c]
    shapes = {(c.get("unit"), c.get("denominator")) for c in scored}
    if len(shapes) == 1:
        return rules._result(rules.COMPOSE, "R2", "agree")
    return rules._result(rules.REFUSE, "R2", "shapes differ")


def _m_r3(b):
    d = b.get("independence", {})
    if d.get("shared_cases") or d.get("shared_evaluator"):
        return rules._result(rules.REFUSE, "R3", "shared")
    return rules._result(rules.COMPOSE, "R3", "independent")


def _m_r3_both(b):
    d = b.get("independence", {})
    if d.get("shared_cases") and d.get("shared_evaluator"):
        return rules._result(rules.REFUSE, "R3", "only a full overlap counts")
    return rules._result(rules.COMPOSE, "R3", "not both, so treated as independent")


def _m_r4(b):
    return rules._result(rules.COMPOSE, "R4", "assume measured")


def _m_r5(b):
    if b.get("interfaces", {}).get("evidence"):
        return rules._result(rules.COMPOSE, "R5", "evidence")
    return rules._result(rules.REFUSE, "R5", "no evidence")


def _m_r6(b):
    return rules._result(rules.COMPOSE, "R6", "assume unchanged")


def _m_r7(b):
    o = b.get("objectives", {})
    if not o.get("conflict"):
        return rules._result(rules.COMPOSE, "R7", "no conflict")
    if o.get("decision_rule") or o.get("authority"):
        return rules._result(rules.COMPOSE, "R7", "either is enough")
    return rules._result(rules.REFUSE, "R7", "nothing declared")


def _m_r8(b, upstream):
    return rules._result(rules.COMPOSE, "R8", "upstream ignored")


def _m_r8_downgrade(b, upstream):
    refused = [r for r in upstream if r["outcome"] == rules.REFUSE]
    if refused:
        return rules._result(
            rules.NARROW, "R8",
            "downgraded without a narrower claim being offered",
            [m for r in refused for m in r["missing"]],
        )
    return _ORIG_R8(b, upstream)


MUTANTS = {
    "M_R1_ignores_justification": ("R1", _m_r1),
    "M_R2_ignores_transformation_rule": ("R2", _m_r2),
    "M_R3_ignores_dependence_record": ("R3", _m_r3),
    "M_R3_requires_both_shares": ("R3", _m_r3_both),
    "M_R4_treats_unmeasured_as_covered": ("R4", _m_r4),
    "M_R5_ignores_assumptions": ("R5", _m_r5),
    "M_R6_skips_baseline_comparison": ("R6", _m_r6),
    "M_R7_accepts_either": ("R7", _m_r7),
    "M_R8_ignores_upstream": ("R8", _m_r8),
    "M_R8_downgrades_silently": ("R8", _m_r8_downgrade),
}


# --- harness ---------------------------------------------------------------
def _verdicts():
    out = {}
    for c in case_module.cases():
        v = rules.evaluate_all(c["bundle"])
        try:
            rr = next(r for r in v["results"] if r["rule"] == c["rule"])
        except StopIteration:
            out[c["id"]] = False
            continue
        out[c["id"]] = (rr["outcome"] == c["expect_rule"]
                        and v["overall"] == c["expect_overall"])
    return out


def _patch(rid, fn):
    """Swap one rule. Returns a restore callable."""
    if rid == "R8":
        original = rules.r8_aggregate
        rules.r8_aggregate = fn
        return lambda: setattr(rules, "r8_aggregate", original)
    original = rules.RULES[rid][1]
    rules.RULES[rid] = (rules.RULES[rid][0], fn)
    return lambda: rules.RULES.__setitem__(rid, (rules.RULES[rid][0], original))


def main():
    baseline = _verdicts()
    bad = sorted(cid for cid, ok in baseline.items() if not ok)
    if bad:
        print("FAIL  baseline is not green: %s" % ", ".join(bad))
        return 2
    print("baseline: %d/%d cases pass as expected\n" % (len(baseline), len(baseline)))

    all_cases = {c["id"]: c for c in case_module.cases()}
    declared = {}
    for cid, c in all_cases.items():
        if c.get("kills"):
            declared.setdefault(c["kills"], []).append(cid)

    print("specification-level mutants (each must be killed)")
    print("-" * 88)
    survivors = []
    for mname in sorted(declared):
        if mname not in MUTANTS:
            print("  %-36s UNKNOWN  named in cases.py but not built here" % mname)
            survivors.append(mname)
            continue
        rid, fn = MUTANTS[mname]
        restore = _patch(rid, fn)
        try:
            after = _verdicts()
        finally:
            restore()
        killed_by = [cid for cid in declared[mname] if after.get(cid) is False]
        if killed_by:
            print("  %-36s KILLED   by %s" % (mname, ", ".join(killed_by)))
        else:
            print("  %-36s SURVIVED (cases %s stayed green)"
                  % (mname, ", ".join(declared[mname])))
            survivors.append(mname)

    # Any mutant built here but never named by a case is a mutant nobody checks.
    unclaimed = sorted(set(MUTANTS) - set(declared))
    for mname in unclaimed:
        print("  %-36s UNCLAIMED  no case names this mutant" % mname)

    print("\nsentinels")
    print("-" * 88)

    # inert: same decision, different wording
    orig_r2 = rules.RULES["R2"][1]

    def inert(b):
        r = orig_r2(b)
        return rules._result(r["outcome"], "R2", "same decision, reworded")

    restore = _patch("R2", inert)
    try:
        after_inert = _verdicts()
    finally:
        restore()
    inert_detected = any(baseline[cid] != after_inert[cid] for cid in baseline)
    print("  %-36s %s  (%s)" % (
        "SENTINEL-inert", "PASS" if not inert_detected else "FAIL",
        "a no-op rewrite is correctly not reported as caught" if not inert_detected
        else "a no-op rewrite was reported as caught - the harness reads text, not behaviour"))

    def fatal(b):
        return rules._result(rules.REFUSE, "R1", "refuses unconditionally")

    restore = _patch("R1", fatal)
    try:
        after_fatal = _verdicts()
    finally:
        restore()
    fatal_detected = after_fatal.get("R1-P") is False
    print("  %-36s %s  (%s)" % (
        "SENTINEL-fatal", "PASS" if fatal_detected else "FAIL",
        "over-refusal on R1 is caught by R1-P" if fatal_detected
        else "over-refusal is invisible - the suite cannot see a rule that refuses too much"))

    print("\n%d/%d mutants killed" % (len(declared) - len([s for s in survivors if s in declared]), len(declared)))
    print("0 cases without a named mutant" if not [c for c in all_cases.values() if not c.get("kills") and c["direction"] == "not met"]
          else "WARNING  some non-met cases name no mutant")

    if survivors or inert_detected or not fatal_detected or unclaimed:
        print("\nFAIL  the suite is not shown to be capable of failing where it must")
        return 1
    print("\nPASS  every mis-reading is caught by the case written for it, "
          "and the harness is not lying")
    return 0


if __name__ == "__main__":
    sys.exit(main())
