"""Twenty-three cases: eight rules, three outcomes, two subject domains.

Each case carries:
    expect_rule     what that rule alone must return
    expect_overall  what the suite must return
    kills           the mutant this case exists to kill (checked by selftest.py)

`kills` is not documentation. selftest.py builds every mutant named here, applies
it, and requires the named case to go red. A case whose `kills` entry survives is
a case that proves nothing, and the selftest fails on it.

Two subject domains, deliberately:

    BASE_A  an authority bundle - identity, policy, executor, one probe each
    BASE_B  a benchmark bundle - two suites with real scores and denominators

Without BASE_B the eight rules would read as an access-control schema, which is
the reading the theme's proposer explicitly asked to avoid. Both are shape
demonstrations, not a proposed schema.
"""

BASE_A = {
    "claim": "component set S supports claim C for purpose P2 within scope S1",
    "components": [
        {"name": "identity", "config_digest": "sha256:aa11", "moment": "2026-10-20",
         "unit": "check", "denominator": 1, "score": 1},
        {"name": "policy", "config_digest": "sha256:bb22", "moment": "2026-10-20",
         "unit": "check", "denominator": 1, "score": 1},
        {"name": "executor", "config_digest": "sha256:cc33", "moment": "2026-10-20",
         "unit": "check", "denominator": 1, "score": 1},
    ],
    "baseline": {"identity": "sha256:aa11", "policy": "sha256:bb22", "executor": "sha256:cc33"},
    "transfer": {"declared": True, "justified": True},
    "units": {"transformation_rule": None},
    "independence": {"shared_cases": False, "shared_evaluator": False, "dependence_recorded": False},
    "required_properties": ["authority_for_p2", "identity_bound"],
    "measured_properties": ["authority_for_p2", "identity_bound"],
    "interfaces": {"evidence": True, "assumptions_declared": False},
    "reassessed": False,
    "objectives": {"conflict": False, "decision_rule": None, "authority": None},
    "evidence": {"narrower_claim": None},
}

BASE_B = {
    "claim": "composite score across two agent-security suites supports claim C under scope S",
    "components": [
        {"name": "injection-suite", "config_digest": "sha256:dd44", "moment": "2026-10-18",
         "unit": "attack_success_rate", "denominator": 500, "score": 0.82},
        {"name": "harm-suite", "config_digest": "sha256:ee55", "moment": "2026-10-18",
         "unit": "attack_success_rate", "denominator": 500, "score": 0.86},
    ],
    "baseline": {"injection-suite": "sha256:dd44", "harm-suite": "sha256:ee55"},
    "transfer": {"declared": True, "justified": True},
    "units": {"transformation_rule": None},
    "independence": {"shared_cases": False, "shared_evaluator": False, "dependence_recorded": False},
    "required_properties": ["resistance_to_injection", "refusal_of_harmful_requests"],
    "measured_properties": ["resistance_to_injection", "refusal_of_harmful_requests"],
    "interfaces": {"evidence": True, "assumptions_declared": False},
    "reassessed": False,
    "objectives": {"conflict": False, "decision_rule": None, "authority": None},
    "evidence": {"narrower_claim": None},
}


def _mutate(base, **changes):
    import copy

    b = copy.deepcopy(base)
    for key, value in changes.items():
        if isinstance(value, dict) and isinstance(b.get(key), dict):
            b[key].update(value)
        else:
            b[key] = value
    return b


def cases():
    A, B = BASE_A, BASE_B
    return [
        # R1 - different configurations -------------------------------------
        {"id": "R1-P", "rule": "R1", "direction": "met",
         "expect_rule": "compose", "expect_overall": "compose",
         "bundle": _mutate(A)},
        {"id": "R1-N", "rule": "R1", "direction": "not met",
         "expect_rule": "refuse", "expect_overall": "refuse",
         "bundle": _mutate(A, transfer={"declared": False, "justified": False}),
         "kills": "M_R1_ignores_justification"},
        {"id": "R1-B", "rule": "R1", "direction": "boundary: declared, unjustified",
         "expect_rule": "narrow", "expect_overall": "narrow",
         "bundle": _mutate(A, transfer={"declared": True, "justified": False}),
         "kills": "M_R1_ignores_justification"},

        # R2 - units and denominators --------------------------------------
        {"id": "R2-P", "rule": "R2", "direction": "met",
         "expect_rule": "compose", "expect_overall": "compose",
         "bundle": _mutate(B)},
        {"id": "R2-N", "rule": "R2", "direction": "not met",
         "expect_rule": "refuse", "expect_overall": "refuse",
         "bundle": _mutate(B, components=[
             dict(B["components"][0]),
             dict(B["components"][1], denominator=480),
         ]),
         "kills": "M_R2_ignores_transformation_rule"},
        {"id": "R2-B", "rule": "R2", "direction": "boundary: different denominators, rule given",
         "expect_rule": "compose", "expect_overall": "compose",
         "bundle": _mutate(B,
                           components=[dict(B["components"][0]),
                                       dict(B["components"][1], denominator=480)],
                           units={"transformation_rule":
                                  "per-suite rate, pooled by item count, no cross-suite weighting"}),
         "kills": "M_R2_ignores_transformation_rule"},

        # R3 - dependence ---------------------------------------------------
        {"id": "R3-P", "rule": "R3", "direction": "met",
         "expect_rule": "compose", "expect_overall": "compose",
         "bundle": _mutate(B)},
        {"id": "R3-N", "rule": "R3", "direction": "not met: cases shared, evaluator not",
         "expect_rule": "refuse", "expect_overall": "refuse",
         "bundle": _mutate(B, independence={"shared_cases": True,
                                            "shared_evaluator": False,
                                            "dependence_recorded": False}),
         "kills": "M_R3_requires_both_shares"},
        {"id": "R3-B", "rule": "R3", "direction": "boundary: shared, recorded",
         "expect_rule": "narrow", "expect_overall": "narrow",
         "bundle": _mutate(B, independence={"shared_cases": True,
                                            "shared_evaluator": True,
                                            "dependence_recorded": True}),
         "kills": "M_R3_ignores_dependence_record"},

        # R4 - unmeasured property ------------------------------------------
        {"id": "R4-P", "rule": "R4", "direction": "met",
         "expect_rule": "compose", "expect_overall": "compose",
         "bundle": _mutate(A)},
        {"id": "R4-N", "rule": "R4", "direction": "not met",
         "expect_rule": "narrow", "expect_overall": "narrow",
         "bundle": _mutate(A, measured_properties=["identity_bound"]),
         "kills": "M_R4_treats_unmeasured_as_covered"},

        # R5 - components versus whole --------------------------------------
        {"id": "R5-P", "rule": "R5", "direction": "met",
         "expect_rule": "compose", "expect_overall": "compose",
         "bundle": _mutate(A)},
        {"id": "R5-N", "rule": "R5", "direction": "not met",
         "expect_rule": "refuse", "expect_overall": "refuse",
         "bundle": _mutate(A, interfaces={"evidence": False, "assumptions_declared": False}),
         "kills": "M_R5_ignores_assumptions"},
        {"id": "R5-B", "rule": "R5", "direction": "boundary: assumptions declared",
         "expect_rule": "narrow", "expect_overall": "narrow",
         "bundle": _mutate(A, interfaces={"evidence": False, "assumptions_declared": True}),
         "kills": "M_R5_ignores_assumptions"},

        # R6 - changed configuration ----------------------------------------
        {"id": "R6-P", "rule": "R6", "direction": "met",
         "expect_rule": "compose", "expect_overall": "compose",
         "bundle": _mutate(A)},
        {"id": "R6-N", "rule": "R6", "direction": "not met: digest differs from baseline",
         "expect_rule": "refuse", "expect_overall": "refuse",
         "bundle": _mutate(A, components=[
             dict(A["components"][0]),
             dict(A["components"][1], config_digest="sha256:bb99"),
             dict(A["components"][2]),
         ]),
         "kills": "M_R6_skips_baseline_comparison"},
        {"id": "R6-B", "rule": "R6", "direction": "boundary: digest differs, reassessed",
         "expect_rule": "compose", "expect_overall": "compose",
         "bundle": _mutate(A, components=[
             dict(A["components"][0]),
             dict(A["components"][1], config_digest="sha256:bb99"),
             dict(A["components"][2]),
         ], reassessed=True),
         "kills": "M_R6_skips_baseline_comparison"},

        # R7 - conflicting objectives ---------------------------------------
        {"id": "R7-P", "rule": "R7", "direction": "met",
         "expect_rule": "compose", "expect_overall": "compose",
         "bundle": _mutate(A)},
        {"id": "R7-N", "rule": "R7", "direction": "not met: rule without authority",
         "expect_rule": "refuse", "expect_overall": "refuse",
         "bundle": _mutate(A, objectives={"conflict": True,
                                          "decision_rule": "security floor dominates",
                                          "authority": None}),
         "kills": "M_R7_accepts_either"},
        {"id": "R7-B", "rule": "R7", "direction": "boundary: rule and authority",
         "expect_rule": "compose", "expect_overall": "compose",
         "bundle": _mutate(A, objectives={"conflict": True,
                                          "decision_rule": "security floor dominates",
                                          "authority": "deploying operator, named in the record"}),
         "kills": "M_R7_accepts_either"},

        # R8 - aggregate -----------------------------------------------------
        {"id": "R8-P", "rule": "R8", "direction": "met: nothing upstream refused",
         "expect_rule": "compose", "expect_overall": "compose",
         "bundle": _mutate(A)},
        {"id": "R8-N", "rule": "R8", "direction": "not met: upstream refusal, no narrower claim",
         "expect_rule": "refuse", "expect_overall": "refuse",
         "bundle": _mutate(A, interfaces={"evidence": False, "assumptions_declared": False}),
         "kills": "M_R8_downgrades_silently"},
        {"id": "R8-B", "rule": "R8", "direction": "boundary: upstream refusal, narrower claim offered",
         "expect_rule": "narrow", "expect_overall": "narrow",
         "bundle": _mutate(A,
                           interfaces={"evidence": False, "assumptions_declared": False},
                           evidence={"narrower_claim":
                                     "each component passes its own probe; nothing is claimed about the seams"}),
         "kills": "M_R8_ignores_upstream"},
    ]
