"""Exact small-instance integer feasibility (paper Section 6).

z_B counts whole block types. This is an exact integer search with memoization,
NOT a general-purpose industrial MILP solver. It supports multiplicities,
capacities, forbidden pairs, positive-support coverage, and optional exact
pair and singleton counts.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from itertools import combinations
from typing import Iterable, Mapping

from .core import Element, Pair, System, ordered, pair, pairs


@dataclass(frozen=True)
class FeasibilityResult:
    feasible: bool
    max_count: int | None
    witness: System | None
    states_explored: int
    type_count: int


def support_pairs(x: System) -> frozenset[Pair]:
    return frozenset(p for p, count in x.pair_counts().items() if count > 0)


def clique_candidates(
    universe: Iterable[Element], edges: Iterable[Pair], h: int
) -> tuple[tuple[Element, ...], ...]:
    if h < 2:
        raise ValueError("Clique order must be >= 2")
    support = frozenset(pair(a, b) for a, b in edges)
    return tuple(
        group for group in combinations(ordered(universe), h)
        if all(p in support for p in combinations(group, 2))
    )


def maximize_occurrences(
    universe: Iterable[Element],
    quotas: Mapping[Element, int],
    size_counts: Mapping[int, int],
    required_pairs: Iterable[Pair] = (),
    target: Iterable[Element] = (),
    forbidden: Iterable[Pair] = (),
    exact_pairs: Mapping[Pair, int] | None = None,
    exact_singletons: Mapping[Element, int] | None = None,
) -> FeasibilityResult:
    """Maximize t_target subject to Section 6's finite integer constraints.

    None max_count means the overall constraint system is INFEASIBLE;
    0 means the system is feasible but the specified target is impossible.
    Empty target is allowed for feasibility-only queries and scores 0.
    """
    elements = ordered(universe)
    q0 = tuple(int(quotas.get(e, 0)) for e in elements)
    if any(q < 0 for q in q0) or len(set(elements)) != len(elements):
        raise ValueError("Invalid universe or quota")
    sizes = tuple(sorted(k for k, v in size_counts.items() if v > 0))
    if any(k < 1 or k > len(elements) for k in sizes):
        raise ValueError("Invalid record size")
    slots0 = tuple(int(size_counts[k]) for k in sizes)
    if sum(q0) != sum(k * size_counts[k] for k in sizes):
        return FeasibilityResult(False, None, None, 0, 0)

    forbid = frozenset(pair(*p) for p in forbidden)
    require = tuple(sorted((pair(*p) for p in required_pairs),
                           key=lambda p: (elements.index(p[0]), elements.index(p[1]))))
    target_set = frozenset(target)
    if not target_set <= set(elements):
        raise ValueError("Target outside universe")
    pair_keys = pairs(elements) if exact_pairs is not None else ()
    exact_pair0 = (
        tuple(int(exact_pairs.get(p, 0)) for p in pair_keys)
        if exact_pairs is not None else ()
    )
    exact_single0 = (
        tuple(int(exact_singletons.get(e, 0)) for e in elements)
        if exact_singletons is not None else ()
    )
    if any(v < 0 for v in exact_pair0 + exact_single0):
        return FeasibilityResult(False, None, None, 0, 0)

    # Each type is an allowed full block. Repeated types are represented
    # by integer multiplicities, not duplicated binary decision variables.
    types = tuple(
        B for k in reversed(sizes)
        for B in combinations(elements, k)
        if all(p not in forbid for p in combinations(B, 2))
    )
    eidx = {e: i for i, e in enumerate(elements)}
    kidx = {k: i for i, k in enumerate(sizes)}
    type_meta = []
    for B in types:
        bset = frozenset(B)
        cover_mask = sum(1 << j for j, p in enumerate(require) if set(p) <= bset)
        type_meta.append((
            tuple(eidx[e] for e in B),
            kidx[len(B)],
            cover_mask,
            tuple(1 if set(p) <= bset else 0 for p in pair_keys),
            tuple(1 if len(B) == 1 and e in bset else 0 for e in elements),
            int(bool(target_set) and target_set <= bset),
        ))

    NEG = -10**9
    decisions: dict[tuple, tuple[int, tuple]] = {}
    states_explored = 0

    @lru_cache(maxsize=None)
    def dp(state: tuple) -> int:
        nonlocal states_explored
        states_explored += 1
        pos, q, slots, uncovered, rem_pair, rem_single = state
        if any(v < 0 for v in q + slots + rem_pair + rem_single):
            return NEG
        if sum(q) != sum(sizes[j] * slots[j] for j in range(len(sizes))):
            return NEG
        if any(v > sum(slots) for v in q):
            return NEG
        if pos == len(types):
            if not any(q + slots + rem_pair + rem_single) and uncovered == 0:
                return 0
            return NEG

        members, ki, coverage, pvec, svec, target_gain = type_meta[pos]
        max_z = min([slots[ki]] + [q[m] for m in members])
        if rem_pair:
            bounds = [rem_pair[j] // pvec[j]
                      for j in range(len(pvec)) if pvec[j]]
            if bounds:
                max_z = min(max_z, *bounds)
        if rem_single:
            bounds = [rem_single[j] // svec[j]
                      for j in range(len(svec)) if svec[j]]
            if bounds:
                max_z = min(max_z, *bounds)
        best, choice = NEG, None
        for z in range(max_z, -1, -1):
            next_q = list(q)
            for i in members:
                next_q[i] -= z
            next_slots = list(slots)
            next_slots[ki] -= z
            next_state = (
                pos + 1, tuple(next_q), tuple(next_slots),
                uncovered & (~coverage if z else -1),
                tuple(r - z * d for r, d in zip(rem_pair, pvec)),
                tuple(r - z * d for r, d in zip(rem_single, svec)),
            )
            rest = dp(next_state)
            if rest != NEG:
                value = rest + z * target_gain
                if value > best:
                    best, choice = value, (z, next_state)
        if choice is not None:
            decisions[state] = choice
        return best

    initial = (
        0, q0, slots0, (1 << len(require)) - 1,
        exact_pair0, exact_single0,
    )
    score = dp(initial)
    if score == NEG:
        return FeasibilityResult(False, None, None, states_explored, len(types))
    records = []
    state = initial
    while state[0] < len(types):
        z, next_state = decisions[state]
        records.extend([types[state[0]]] * z)
        state = next_state
    witness = System.create(records, universe=elements)
    if witness.quotas() != {e: quotas.get(e, 0) for e in elements}:
        # Counter equality ignores missing zero entries; the explicit check
        # above is intentionally conservative.
        assert all(witness.quotas()[e] == quotas.get(e, 0) for e in elements)
    assert all(witness.pair_counts()[p] >= 1 for p in require)
    assert witness.count(target_set) == score if target_set else score == 0
    return FeasibilityResult(True, score, witness, states_explored, len(types))
