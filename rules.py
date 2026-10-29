"""D3 composition rules, as executable decision functions.

Eight rules, taken from the FG-TIDA themes#44 D3 candidate table. Each returns
exactly one of three outcomes:

    compose  the inputs meet the rule's condition
    narrow   only the reduced claim named in `reason` is supported
    refuse   no composite claim; the missing justification is named

Three design decisions, because each was attacked in review:

1. Three rules compute rather than accept a declaration. R2 compares units and
   denominators of the actual scores. R6 compares each component's configuration
   digest against the baseline it was evaluated under. R8 takes no input of its
   own: it aggregates the other seven. A rule whose input is "the claimant says
   it is fine" is a schema check wearing a rule's name.

2. No rule may return compose for a condition it did not read. Where a rule is
   two-valued, it says so (R2, R6, R7 never return narrow) rather than pretending
   to a third branch it does not have.

3. Every non-compose branch is reachable from a case in cases.py. A branch that
   no case reaches is not evidence of anything, so selftest.py mutates each one
   away and requires the suite to notice.

Stdlib only. Python 3.9+.
"""

COMPOSE = "compose"
NARROW = "narrow"
REFUSE = "refuse"

# Rules with only two outcomes, declared so that the absence of a narrow branch
# is a statement rather than an oversight.
TWO_VALUED = ("R2", "R6", "R7")


def _result(outcome, rule, reason, missing=None):
    return {"outcome": outcome, "rule": rule, "reason": reason, "missing": missing or []}


# R1 ------------------------------------------------------------------------
def r1_configuration(b):
    """Results from different configurations are not evidence about one system."""
    t = b.get("transfer", {})
    if not t.get("declared"):
        return _result(
            REFUSE, "R1",
            "inputs come from different configurations and no transfer is declared",
            ["declared basis for treating the results as evidence about one system"],
        )
    if not t.get("justified"):
        return _result(
            NARROW, "R1",
            "transfer declared but not justified; each configuration carries only its own claim",
            ["justification for extending a result across configurations"],
        )
    return _result(COMPOSE, "R1", "transfer declared and justified")


# R2 ------------------------------------------------------------------------
def r2_units(b):
    """Units, denominators and meanings are compared, not declared."""
    scored = [c for c in b.get("components", []) if "score" in c]
    if len(scored) < 2:
        return _result(
            NARROW, "R2",
            "fewer than two scored components; nothing is being combined",
            ["a second scored component"],
        )
    shapes = {(c.get("unit"), c.get("denominator")) for c in scored}
    if len(shapes) == 1:
        return _result(COMPOSE, "R2", "units and denominators agree across components")
    rule = b.get("units", {}).get("transformation_rule")
    if rule:
        return _result(COMPOSE, "R2", "units differ; explicit transformation supplied: " + str(rule))
    return _result(
        REFUSE, "R2",
        "scores differ in unit or denominator %s and no transformation rule is given"
        % sorted(shapes, key=str),
        ["explicit transformation and aggregation rule for " + str(s) for s in sorted(shapes, key=str)],
    )


# R3 ------------------------------------------------------------------------
def r3_dependence(b):
    """Reused cases or evaluators are not independent corroboration."""
    d = b.get("independence", {})
    if not (d.get("shared_cases") or d.get("shared_evaluator")):
        return _result(COMPOSE, "R3", "inputs are independent")
    if d.get("dependence_recorded"):
        return _result(
            NARROW, "R3",
            "dependence recorded; inputs count as consistent observations, not corroboration",
            ["independent replication"],
        )
    return _result(
        REFUSE, "R3",
        "shared cases or evaluator, and the dependence is not recorded",
        ["record of the shared cases or evaluator"],
    )


# R4 ------------------------------------------------------------------------
def r4_unmeasured(b):
    """A property that was never measured stays unmeasured."""
    required = list(b.get("required_properties", []))
    measured = set(b.get("measured_properties", []))
    missing = [p for p in required if p not in measured]
    if not missing:
        return _result(COMPOSE, "R4", "every required property was measured")
    return _result(
        NARROW, "R4",
        "required properties not measured: " + ", ".join(missing),
        ["measurement of " + p for p in missing],
    )


# R5 ------------------------------------------------------------------------
def r5_interfaces(b):
    """Components that each pass do not establish the whole."""
    i = b.get("interfaces", {})
    if i.get("evidence"):
        return _result(COMPOSE, "R5", "interface and interaction evidence supplied")
    if i.get("assumptions_declared"):
        return _result(
            NARROW, "R5",
            "no interface evidence; whole-system claim rests on declared assumptions",
            ["evidence at the interfaces between components"],
        )
    return _result(
        REFUSE, "R5",
        "component tests pass, but nothing is said about interfaces or interactions",
        ["interface evidence, or declared assumptions about interactions"],
    )


# R6 ------------------------------------------------------------------------
def r6_change(b):
    """A changed configuration invalidates reliance; it does not rewrite history.

    The comparison is made against the baseline digests the results were produced
    under, not against a list the claimant supplies.
    """
    baseline = b.get("baseline", {})
    changed = []
    for c in b.get("components", []):
        was = baseline.get(c.get("name"))
        now = c.get("config_digest")
        if was and now and was != now:
            changed.append("%s %s -> %s" % (c.get("name"), was, now))
    if not changed:
        return _result(COMPOSE, "R6", "no component differs from the baseline it was evaluated under")
    if b.get("reassessed"):
        return _result(
            COMPOSE, "R6",
            "affected reliance reassessed; historical results preserved: " + "; ".join(changed),
        )
    return _result(
        REFUSE, "R6",
        "configuration changed since evaluation and no reassessment is recorded: "
        + "; ".join(changed),
        ["reassessment of reliance for " + s for s in changed],
    )


# R7 ------------------------------------------------------------------------
def r7_conflict(b):
    """Aggregation must not silently choose a trade-off."""
    o = b.get("objectives", {})
    if not o.get("conflict"):
        return _result(COMPOSE, "R7", "no conflict between stated objectives")
    missing = []
    if not o.get("decision_rule"):
        missing.append("decision rule for the trade-off")
    if not o.get("authority"):
        missing.append("named authority responsible for the trade-off")
    if not missing:
        return _result(COMPOSE, "R7", "conflict declared with a decision rule and a named authority")
    return _result(REFUSE, "R7", "objectives conflict and the trade-off is left implicit", missing)


# R8 ------------------------------------------------------------------------
def r8_aggregate(b, upstream):
    """No input of its own. Fails closed over what the other seven found.

    This rule exists so that the outcome of the other seven cannot be summarised
    into a green by omission: if any of them refused, the composite is not
    established, and the reason names what is missing rather than staying silent.
    """
    refused = [r for r in upstream if r["outcome"] == REFUSE]
    narrowed = [r for r in upstream if r["outcome"] == NARROW]
    if refused:
        missing = [m for r in refused for m in r["missing"]]
        narrower = b.get("evidence", {}).get("narrower_claim")
        if narrower:
            return _result(
                NARROW, "R8",
                "composite not established; reduced claim supported: " + str(narrower),
                missing,
            )
        return _result(
            REFUSE, "R8",
            "composite not established: " + ", ".join(r["rule"] for r in refused) + " refused",
            missing or ["justification named by the refusing rule"],
        )
    if narrowed:
        narrower = b.get("evidence", {}).get("narrower_claim")
        if narrower:
            return _result(
                NARROW, "R8",
                "composite limited; reduced claim supported: " + str(narrower),
                [m for r in narrowed for m in r["missing"]],
            )
        return _result(
            NARROW, "R8",
            "composite limited by " + ", ".join(r["rule"] for r in narrowed),
            [m for r in narrowed for m in r["missing"]],
        )
    return _result(COMPOSE, "R8", "every rule permitted the composite claim")


RULES = {
    "R1": ("Different configurations", r1_configuration),
    "R2": ("Units and denominators", r2_units),
    "R3": ("Reused cases or evaluators", r3_dependence),
    "R4": ("Property not measured", r4_unmeasured),
    "R5": ("Components versus whole", r5_interfaces),
    "R6": ("Changed configuration", r6_change),
    "R7": ("Conflicting objectives", r7_conflict),
}

# R8 is the aggregate and is applied last, over the results of the other seven.
AGGREGATE = ("R8", "Evidence insufficiency", r8_aggregate)


def evaluate_all(bundle):
    """Apply the seven rules, then let R8 aggregate. R8 is the verdict.

    The overall outcome is R8's, not a second tally: a wrong tally would be a
    second place for a refusal to be lost. R8 fails closed - any upstream refusal
    is a refusal unless the bundle itself offers a narrower claim - and it names
    what is missing, so the refusal is legible rather than silent.
    """
    results = [fn(bundle) for _, fn in RULES.values()]
    results.append(r8_aggregate(bundle, list(results)))
    return {"overall": results[-1]["outcome"], "results": results}


def all_rule_ids():
    return list(RULES) + [AGGREGATE[0]]


def get_rule(rule_id):
    if rule_id == AGGREGATE[0]:
        return AGGREGATE[1]
    return RULES[rule_id][1]
