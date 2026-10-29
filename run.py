"""Run the twenty-three composition cases. Exit code carries the verdict.

    python run.py            # human table
    python run.py --json     # machine-readable

Exit codes
    0  every case produced the outcome named in advance
    1  at least one did not
    2  the run did not execute the expected number of cases, or the suite is
       structurally incapable of a verdict (unbalanced, or nothing ever refuses)

Code 2 exists because a suite is itself a gate, and the failure mode of a gate is
to pass while checking nothing: a renamed file, a broken import or a truncated
case list would otherwise leave an empty loop and exit 0. A missing module fails
earlier, at import, with the interpreter's own non-zero code - which is why the
guard covers the count rather than the import.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cases as case_module  # noqa: E402
import rules  # noqa: E402

EXPECTED_CASE_COUNT = 23


def run():
    rows = []
    for c in case_module.cases():
        verdict = rules.evaluate_all(c["bundle"])
        rule_result = next(r for r in verdict["results"] if r["rule"] == c["rule"])
        rows.append(
            {
                "id": c["id"],
                "rule": c["rule"],
                "direction": c["direction"],
                "expected_rule": c["expect_rule"],
                "actual_rule": rule_result["outcome"],
                "expected_overall": c["expect_overall"],
                "actual_overall": verdict["overall"],
                "missing": rule_result["missing"],
                "kills": c.get("kills"),
                "ok": (rule_result["outcome"] == c["expect_rule"]
                       and verdict["overall"] == c["expect_overall"]),
            }
        )
    return rows


def main():
    rows = run()

    if len(rows) != EXPECTED_CASE_COUNT:
        print("FAIL  collected %d cases, expected %d - no verdict can be drawn "
              "from a partial run" % (len(rows), EXPECTED_CASE_COUNT))
        return 2

    per_rule = {}
    for r in rows:
        per_rule.setdefault(r["rule"], set()).add(r["direction"].startswith("met"))
    for rid in rules.all_rule_ids():
        if per_rule.get(rid) != {True, False}:
            print("FAIL  rule %s does not carry both a met and a non-met case" % rid)
            return 2

    non_met_outcomes = {r["actual_rule"] for r in rows if not r["direction"].startswith("met")}
    if not non_met_outcomes & {rules.REFUSE, rules.NARROW}:
        print("FAIL  no non-compose outcome appeared in any non-met case")
        return 2

    if "--json" in sys.argv:
        print(json.dumps({"cases": rows, "passed": all(r["ok"] for r in rows)}, indent=2))
        return 0 if all(r["ok"] for r in rows) else 1

    print("D3 composition cases - %d cases over %d rules, two subject domains"
          % (len(rows), len(rules.all_rule_ids())))
    print("=" * 104)
    print("%-6s %-4s %-34s %-8s %-8s %-8s %s"
          % ("case", "rule", "direction", "expect", "actual", "overall", "verdict"))
    print("-" * 104)
    for r in rows:
        print("%-6s %-4s %-34s %-8s %-8s %-8s %s"
              % (r["id"], r["rule"], r["direction"][:34], r["expected_rule"],
                 r["actual_rule"], r["actual_overall"], "PASS" if r["ok"] else "FAIL"))
    print("-" * 104)

    failed = [r for r in rows if not r["ok"]]
    tally = {}
    for r in rows:
        tally[r["actual_rule"]] = tally.get(r["actual_rule"], 0) + 1
    print("%d cases: %d compose, %d narrow, %d refuse"
          % (len(rows), tally.get("compose", 0), tally.get("narrow", 0), tally.get("refuse", 0)))

    if failed:
        print("\nFAILED")
        for r in failed:
            print("  %s expected %s, got %s (missing: %s)"
                  % (r["id"], r["expected_rule"], r["actual_rule"],
                     "; ".join(r["missing"]) or "none named"))
        return 1
    print("\nPASS  every case reached the outcome named in advance")
    return 0


if __name__ == "__main__":
    sys.exit(main())
