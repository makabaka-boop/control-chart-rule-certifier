"""SPC control-chart rule engine — exact integer arithmetic only.

Four Western Electric style rules:

R1: one point strictly outside 3 sigma.
R2: of 3 consecutive points, at least 2 strictly beyond 2 sigma on the
    same side.
R3: of 5 consecutive points, at least 4 strictly beyond 1 sigma on the
    same side.
R4: 8 consecutive points strictly on the same side of the center line.

Equality with a boundary does NOT count as crossing (strict comparisons).

Tie-break for multiple rule hits, in order:
  1. smallest end index (0-based, inclusive, of the window producing it);
  2. rule order (R1 < R2 < R3 < R4);
  3. lexicographically smallest evidence index sequence.
"""
from __future__ import annotations

from dataclasses import dataclass

RULE_NAMES = {
    1: "一点严格越过 3σ",
    2: "连续三点中至少两点严格越过同侧 2σ",
    3: "连续五点中至少四点严格越过同侧 1σ",
    4: "连续八点严格位于中心线同侧",
}


def side_of(delta: int) -> str:
    """'above' / 'below' / 'on' relative to center line. Integer compare."""
    if delta > 0:
        return "above"
    if delta < 0:
        return "below"
    return "on"


def zone_of(delta: int, sigma: int) -> str:
    """Zone of a single point using half-open bands (integer compares).

    Bands (d = |delta|):
      d > 3s  -> beyond_3sigma
      2s < d <= 3s -> zone_a_2_3sigma
      1s < d <= 2s -> zone_b_1_2sigma
      0 < d <= 1s  -> zone_c_0_1sigma
      d == 0  -> center
    Boundary equality stays on the inner band: |delta| == 3s is zone A,
    |delta| == 2s is zone B, |delta| == s is zone C.
    """
    d = delta if delta >= 0 else -delta
    if d > 3 * sigma:
        return "beyond_3sigma"
    if d > 2 * sigma:
        return "zone_a_2_3sigma"
    if d > sigma:
        return "zone_b_1_2sigma"
    if d > 0:
        return "zone_c_0_1sigma"
    return "center"


@dataclass(frozen=True)
class Violation:
    rule: int
    end_index: int
    evidence: tuple[int, ...]


def _candidates(readings: list[int], target: int, sigma: int) -> list[Violation]:
    """Enumerate every rule violation (all windows, all sides)."""
    n = len(readings)
    out: list[Violation] = []

    # R1: single point strictly beyond 3 sigma.
    for i, v in enumerate(readings):
        d = v - target
        if d > 3 * sigma or d < -3 * sigma:
            out.append(Violation(1, i, (i,)))

    # R2: windows of 3, >= 2 points strictly beyond 2 sigma, same side.
    for end in range(2, n):
        w = range(end - 2, end + 1)
        up = [i for i in w if readings[i] - target > 2 * sigma]
        dn = [i for i in w if readings[i] - target < -2 * sigma]
        if len(up) >= 2:
            out.append(Violation(2, end, tuple(up)))
        if len(dn) >= 2:
            out.append(Violation(2, end, tuple(dn)))

    # R3: windows of 5, >= 4 points strictly beyond 1 sigma, same side.
    for end in range(4, n):
        w = range(end - 4, end + 1)
        up = [i for i in w if readings[i] - target > sigma]
        dn = [i for i in w if readings[i] - target < -sigma]
        if len(up) >= 4:
            out.append(Violation(3, end, tuple(up)))
        if len(dn) >= 4:
            out.append(Violation(3, end, tuple(dn)))

    # R4: 8 consecutive points strictly on one side of the center line.
    for end in range(7, n):
        w = range(end - 7, end + 1)
        up = [i for i in w if readings[i] - target > 0]
        dn = [i for i in w if readings[i] - target < 0]
        if len(up) == 8:
            out.append(Violation(4, end, tuple(up)))
        if len(dn) == 8:
            out.append(Violation(4, end, tuple(dn)))

    return out


def select_violation(
    readings: list[int], target: int, sigma: int
) -> Violation | None:
    """Return the unique, fully reproducible out-of-control evidence."""
    cands = _candidates(readings, target, sigma)
    if not cands:
        return None
    return min(cands, key=lambda v: (v.end_index, v.rule, v.evidence))


def evaluate(readings: list[int], target: int, sigma: int) -> dict:
    """Full response payload shared by the table and the SVG chart."""
    points = []
    for i, v in enumerate(readings):
        delta = v - target
        points.append(
            {
                "index": i,
                "value": v,
                "delta": delta,
                "side": side_of(delta),
                "zone": zone_of(delta, sigma),
            }
        )

    result: dict = {
        "target": target,
        "sigma": sigma,
        "in_control": True,
        "violation": None,
        "points": points,
        "limits": {
            "center": target,
            "plus_1sigma": target + sigma,
            "minus_1sigma": target - sigma,
            "plus_2sigma": target + 2 * sigma,
            "minus_2sigma": target - 2 * sigma,
            "plus_3sigma": target + 3 * sigma,
            "minus_3sigma": target - 3 * sigma,
        },
    }

    hit = select_violation(readings, target, sigma)
    if hit is not None:
        result["in_control"] = False
        result["violation"] = {
            "rule": hit.rule,
            "rule_name": RULE_NAMES[hit.rule],
            "end_index": hit.end_index,
            "evidence": [points[i] for i in hit.evidence],
            "evidence_indices": list(hit.evidence),
        }
    return result
