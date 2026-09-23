"""Cross-check tests: the engine is compared against a deliberately
naive window scanner, plus hand-computed boundary and tie-break cases."""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api.rules import evaluate, select_violation, zone_of  # noqa: E402


# ---------------------------------------------------------------------------
# Independent naive reference implementation (plain nested-loop scanning).
# ---------------------------------------------------------------------------
def naive_first(readings, target, sigma):
    """Return (rule, end_index, evidence_tuple) by brute-force scan."""
    n = len(readings)
    best = None  # (end, rule, evidence)

    def consider(rule, end, ev):
        nonlocal best
        key = (end, rule, tuple(ev))
        if best is None or key < best:
            best = key

    for i in range(n):
        if abs(readings[i] - target) > 3 * sigma:
            consider(1, i, (i,))

    for j in range(n - 2):
        window = readings[j : j + 3]
        for sign in (1, -1):
            ev = [
                j + k
                for k, x in enumerate(window)
                if sign * (x - target) > 2 * sigma
            ]
            if len(ev) >= 2:
                consider(2, j + 2, tuple(ev))

    for j in range(n - 4):
        window = readings[j : j + 5]
        for sign in (1, -1):
            ev = [
                j + k
                for k, x in enumerate(window)
                if sign * (x - target) > sigma
            ]
            if len(ev) >= 4:
                consider(3, j + 4, tuple(ev))

    for j in range(n - 7):
        window = readings[j : j + 8]
        for sign in (1, -1):
            if all(sign * (x - target) > 0 for x in window):
                consider(4, j + 7, tuple(range(j, j + 8)))

    return best


def test_naive_scanner_matches_engine_on_random_cases():
    rng = random.Random(20260923)
    for _ in range(3000):
        n = rng.randint(2, 60)
        target = rng.randint(-20, 20)
        sigma = rng.randint(1, 5)
        readings = [target + rng.randint(-4 * sigma - 1, 4 * sigma + 1)
                    for _ in range(n)]
        got = select_violation(readings, target, sigma)
        want = naive_first(readings, target, sigma)
        if want is None:
            assert got is None, readings
        else:
            assert (got.end_index, got.rule, got.evidence) == want


# ---------------------------------------------------------------------------
# Hand-computed cases.
# ---------------------------------------------------------------------------
def test_boundary_equality_is_not_a_crossing_r1():
    # delta == +3sigma exactly: in control.
    res = evaluate([10, 16], 10, 2)
    assert res["in_control"] is True
    assert res["points"][1]["zone"] == "zone_a_2_3sigma"

    # delta == 3sigma + 1: out of control, R1 at index 1.
    res = evaluate([10, 17], 10, 2)
    assert res["in_control"] is False
    v = res["violation"]
    assert v["rule"] == 1 and v["end_index"] == 1
    assert v["evidence_indices"] == [1]
    assert v["evidence"][0]["zone"] == "beyond_3sigma"


def test_negative_side_boundary():
    res = evaluate([10, 4], 10, 2)   # delta -6 == -3sigma -> stable
    assert res["in_control"] is True
    res = evaluate([10, 3], 10, 2)   # delta -7 < -3sigma -> R1
    assert res["violation"]["rule"] == 1
    assert res["violation"]["evidence"][0]["side"] == "below"


def test_rule2_needs_two_of_three_beyond_2sigma_same_side():
    # deltas: 0, +5, +5  -> two beyond +2sigma(4) in window ending at 2.
    res = evaluate([10, 15, 15], 10, 2)
    v = res["violation"]
    assert v["rule"] == 2 and v["end_index"] == 2
    assert v["evidence_indices"] == [1, 2]

    # one above 2sigma, one below 2sigma -> sides differ, no R2.
    res = evaluate([10, 15, 5], 10, 2)
    assert res["in_control"] is True

    # exactly at +2sigma boundary does not count.
    res = evaluate([10, 14, 14], 10, 2)
    assert res["in_control"] is True


def test_rule3_four_of_five_beyond_1sigma_same_side():
    # deltas: +3,+3,+3,+3,0 with sigma=2: four beyond +1sigma(2).
    res = evaluate([13, 13, 13, 13, 10], 10, 2)
    v = res["violation"]
    assert v["rule"] == 3 and v["end_index"] == 4
    assert v["evidence_indices"] == [0, 1, 2, 3]

    # at +1sigma boundary does not count: deltas +2,+2,+2,+2,0 -> stable.
    res = evaluate([12, 12, 12, 12, 10], 10, 2)
    assert res["in_control"] is True


def test_rule4_eight_strictly_same_side():
    # 8 points all slightly above center; the +1 is not beyond 1sigma.
    res = evaluate([11] * 8, 10, 5)
    v = res["violation"]
    assert v["rule"] == 4 and v["end_index"] == 7
    assert v["evidence_indices"] == list(range(8))
    assert all(p["side"] == "above" for p in v["evidence"])

    # a point exactly on center breaks the run.
    res = evaluate([11, 11, 11, 11, 11, 11, 11, 10], 10, 5)
    assert res["in_control"] is True


def test_tie_break_smallest_end_index_wins():
    # R1 at index 2 (delta 7 > 6) and R4 ending at 7: earliest end is 2.
    readings = [11, 11, 17] + [11] * 5
    res = evaluate(readings, 10, 2)
    assert res["violation"]["rule"] == 1
    assert res["violation"]["end_index"] == 2


def test_tie_break_same_end_rule_order():
    # Window ending at 4: points 0..3 beyond +1sigma (R3), and point 4
    # beyond +3sigma (R1). Same end index -> R1 wins by rule order.
    readings = [13, 13, 13, 13, 17]
    res = evaluate(readings, 10, 2)
    v = res["violation"]
    assert v["rule"] == 1 and v["end_index"] == 4
    assert v["evidence_indices"] == [4]


def test_evidence_lexicographic_tiebreak_directly():
    # Two R3 hits on the same window (cannot really happen for the same
    # rule given >=4/5 split), so exercise the key ordering directly:
    # min() over fabricated candidates sorts by (end, rule, evidence).
    from api.rules import Violation
    cands = [
        Violation(4, 9, (2, 3, 4, 5, 6, 7, 8, 9)),
        Violation(2, 9, (8, 9)),
        Violation(1, 9, (9,)),
        Violation(1, 8, (8,)),
    ]
    chosen = min(cands, key=lambda v: (v.end_index, v.rule, v.evidence))
    assert chosen == Violation(1, 8, (8,))


def test_zone_partitions_are_half_open():
    sigma = 2
    assert zone_of(7, sigma) == "beyond_3sigma"
    assert zone_of(6, sigma) == "zone_a_2_3sigma"   # == 3sigma
    assert zone_of(5, sigma) == "zone_a_2_3sigma"
    assert zone_of(4, sigma) == "zone_b_1_2sigma"   # == 2sigma
    assert zone_of(3, sigma) == "zone_b_1_2sigma"
    assert zone_of(2, sigma) == "zone_c_0_1sigma"   # == 1sigma
    assert zone_of(1, sigma) == "zone_c_0_1sigma"
    assert zone_of(0, sigma) == "center"
    assert zone_of(-6, sigma) == "zone_a_2_3sigma"


def test_response_shape_shared_by_table_and_svg():
    res = evaluate([10, 17], 10, 2)
    assert set(res) >= {"target", "sigma", "in_control", "violation",
                        "points", "limits"}
    p = res["points"][1]
    assert set(p) == {"index", "value", "delta", "side", "zone"}
    assert res["limits"]["plus_3sigma"] == 16
    assert res["limits"]["minus_3sigma"] == 4
