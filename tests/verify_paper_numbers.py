#!/usr/bin/env python3
"""Independent verification of every numerical claim in the English manuscript.

This script deliberately does *not* import the `hocomb` package.  It re-implements
the definitions of Sections 2--6 directly from the paper, so that the numbers
printed in the translated manuscript can be checked without trusting the
repository code.  A separate run of `examples/run_all.py` checks the repository
itself (see the verification section of `README.md`).

Run:  python3 tests/verify_paper_numbers.py
"""

from fractions import Fraction
from itertools import combinations


# --------------------------------------------------------------------------- #
# Core definitions from Section 2
# --------------------------------------------------------------------------- #
def B(*elements):
    return frozenset(elements)


def pairs_of(block):
    return frozenset(combinations(sorted(block, key=str), 2))


def pair_counts(system):
    out = {}
    for block in system:
        for p in pairs_of(block):
            out[p] = out.get(p, 0) + 1
    return out


def singleton_counts(system):
    out = {}
    for block in system:
        if len(block) == 1:
            e = next(iter(block))
            out[e] = out.get(e, 0) + 1
    return out


def quotas(system):
    out = {}
    for block in system:
        for e in block:
            out[e] = out.get(e, 0) + 1
    return out


def t(system, subset):
    subset = frozenset(subset)
    return sum(1 for block in system if subset <= block)


def higher_counts(system, h):
    out = {}
    for block in system:
        if len(block) >= h:
            for sub in combinations(sorted(block, key=str), h):
                s = frozenset(sub)
                out[s] = out.get(s, 0) + 1
    return out


def total_h(system, h):
    from math import comb
    return sum(comb(len(block), h) for block in system if len(block) >= h)


def distance(x, y, h):
    hx, hy = higher_counts(x, h), higher_counts(y, h)
    keys = set(hx) | set(hy)
    return Fraction(sum(abs(hx.get(s, 0) - hy.get(s, 0)) for s in keys),
                    2 * total_h(x, h))


def pair_table(system, universe):
    pc = pair_counts(system)
    return {tuple(sorted(p, key=str)): pc.get(tuple(sorted(p, key=str)), 0)
            for p in combinations(universe, 2)}


def loss(system, pair_targets, single_targets, weights=None, lam=1):
    weights = weights or {}
    value = Fraction(0)
    pc, sc = pair_counts(system), singleton_counts(system)
    for p, target in pair_targets.items():
        value += weights.get(p, 1) * (pc.get(p, 0) - target) ** 2
    sum_single = sum((sc.get(e, 0) - target) ** 2
                     for e, target in single_targets.items())
    return value + lam * sum_single


# --------------------------------------------------------------------------- #
# Section 1 and Section 4: the motivating four-triple example
# --------------------------------------------------------------------------- #
def check_intro_and_zero_sum():
    XA = [B(1, 2, 3), B(1, 4, 5), B(2, 4, 6), B(3, 5, 6)]
    XB = [B(1, 2, 4), B(1, 3, 5), B(2, 3, 6), B(4, 5, 6)]
    V = [1, 2, 3, 4, 5, 6]

    assert quotas(XA) == quotas(XB) == {i: 2 for i in V}, "Section 1 quotas"
    assert pair_counts(XA) == pair_counts(XB), "Section 1 pair counts"
    assert len(pair_counts(XA)) == 12 and set(pair_counts(XA).values()) == {1}
    assert t(XA, {1, 2, 3}) == 1 and t(XB, {1, 2, 3}) == 0
    assert t(XA, {1, 2, 4}) == 0 and t(XB, {1, 2, 4}) == 1

    # Section 4: two switches, signatures r1 = e5 - e2 and r2 = -r1, delta = 0.
    A, Bb = XA[0], XA[1]           # {1,2,3}, {1,4,5}; exchange 3 and 4
    A0, B0 = A - {3}, Bb - {4}
    r1 = {e: int(e in B0) - int(e in A0) for e in {1, 2, 3, 4, 5}}
    # The paper orders this switch as A = {3,5,6} and B = {2,4,6}, a = 3, b = 4.
    C, D = XA[3], XA[2]            # {3,5,6}, {2,4,6}; exchange 3 and 4
    C0, D0 = C - {3}, D - {4}
    r2 = {e: int(e in D0) - int(e in C0) for e in {1, 2, 3, 4, 5, 6}}
    assert {k: v for k, v in r1.items() if v} == {5: 1, 2: -1}
    assert {k: v for k, v in r2.items() if v} == {2: 1, 5: -1}
    assert all(r1.get(e, 0) + r2.get(e, 0) == 0 for e in V)
    delta1 = int(len(Bb) == 1) - int(len(A) == 1)
    delta2 = int(len(D) == 1) - int(len(C) == 1)
    assert delta1 == delta2 == 0

    induced = [B(1, 2, 4), B(1, 3, 5), XA[2], XA[3]]
    assert [sym(A, 3, 4), sym(Bb, 4, 3)] == [B(1, 2, 4), B(1, 3, 5)]
    assert induced == [B(1, 2, 4), B(1, 3, 5), B(2, 4, 6), B(3, 5, 6)]
    final = [B(1, 2, 4), B(1, 3, 5), B(2, 3, 6), B(4, 5, 6)]
    assert final == XB
    assert pair_counts(XA) == pair_counts(XB)
    assert singleton_counts(XA) == singleton_counts(XB) == {}
    assert set(higher_counts(XA, 3)) & set(higher_counts(XB, 3)) == set()
    l1 = sum(abs(higher_counts(XA, 3).get(s, 0) - higher_counts(XB, 3).get(s, 0))
             for s in set(higher_counts(XA, 3)) | set(higher_counts(XB, 3)))
    assert l1 == 8 and total_h(XA, 3) == 4
    assert distance(XA, XB, 3) == 1

    print(f"[PASS] Section 1: quotas = pair counts = 12 distinct pairs; "
          f"t_123 = {t(XA, {1, 2, 3})}/{t(XB, {1, 2, 3})}, "
          f"t_124 = {t(XA, {1, 2, 4})}/{t(XB, {1, 2, 4})}")
    print(f"[PASS] Section 4: r_1 = e5 - e2, r_2 = e2 - e5, delta_1 = delta_2 = 0; "
          f"|S3 cap| = 0, ||dH3||_1 = {l1}, T3 = {total_h(XA, 3)}, d3 = {distance(XA, XB, 3)}")


def sym(block, leave, enter):
    return frozenset((set(block) - {leave}) | {enter})


# --------------------------------------------------------------------------- #
# Section 3.4: exact local delta for the singleton/pair cross-stratum switch
# --------------------------------------------------------------------------- #
def check_local_delta():
    X = [B(1), B(2, 3)]
    Xp = [B(3), B(1, 2)]
    target_pairs = {tuple(sorted(p, key=str)): v for p, v in
                    {(1, 2): 1, (1, 3): 0, (2, 3): 0}.items()}
    target_singles = {1: 0, 2: 0, 3: 1}
    e0, e1 = loss(X, target_pairs, target_singles), loss(Xp, target_pairs, target_singles)
    assert (e0, e1) == (4, 0)

    # Paper formula (3.12), computed from residuals and local increments only.
    A, Bb = X[0], X[1]
    a, b = 1, 3                      # element 1 leaves A, element 3 leaves B
    A0, B0 = A - {a}, Bb - {b}
    pc, sc = pair_counts(X), singleton_counts(X)
    tgt_pc = {tuple(sorted(p, key=str)): v for p, v in
              {(1, 2): 1, (1, 3): 0, (2, 3): 0}.items()}
    delta_e = Fraction(0)
    for z in A0 ^ B0:
        d = int(z in B0) - int(z in A0)
        for x, dx in ((a, d), (b, -d)):
            p = tuple(sorted((x, z), key=str))
            r = pc.get(p, 0) - tgt_pc.get(p, 0)
            delta_e += 2 * r * dx + dx * dx
    da = int(len(Bb) == 1) - int(len(A) == 1)
    for x, dx in ((a, da), (b, -da)):
        u = sc.get(x, 0) - target_singles.get(x, 0)
        delta_e += 2 * u * dx + dx * dx
    assert delta_e == -4 == e1 - e0

    print(f"[PASS] Section 3: E(X) = {e0}, E(X') = {e1}, "
          f"predicted local delta E = {delta_e}, direct delta = {e1 - e0}")
    print(f"       pairs {pair_table(X, [1, 2, 3])} -> {pair_table(Xp, [1, 2, 3])}; "
          f"singletons {singleton_counts(X)} -> {singleton_counts(Xp)}")


# --------------------------------------------------------------------------- #
# Section 5: complete construction example
# --------------------------------------------------------------------------- #
def check_directed_example():
    X0 = [B(1, 2, 3), B(1, 4, 5), B(2, 4, 6), B(3, 5, 6)]
    V = [1, 2, 3, 4, 5, 6]
    pairs = list(combinations(V, 2))
    target_pairs = {p: t(X0, p) for p in pairs}
    target_singles = {i: 0 for i in V}
    assert t(X0, {1, 2, 4}) == 0 and t(X0, {4, 5, 6}) == 0
    assert loss(X0, target_pairs, target_singles) == 0

    induced = [sym(X0[0], 3, 4), sym(X0[1], 4, 3), X0[2], X0[3]]
    assert induced == [B(1, 2, 4), B(1, 3, 5), B(2, 4, 6), B(3, 5, 6)]
    assert t(induced, {1, 2, 4}) == 1
    e_ind = loss(induced, target_pairs, target_singles)
    assert e_ind == 4

    frozen = [B(1, 2, 4)]
    free = induced[1:]
    d1 = {i: quotas(X0)[i] - quotas(frozen).get(i, 0) for i in V}
    assert d1 == {1: 1, 2: 1, 3: 2, 4: 1, 5: 2, 6: 2}
    m3 = 4 - sum(1 for blk in frozen if len(blk) == 3)
    assert m3 == 3

    residual = {p: target_pairs[p] - t(frozen, p) for p in pairs}
    four = [(2, 3), (2, 4), (3, 5), (4, 5)]
    assert [residual[p] for p in four] == [1, 0, 1, 1]
    assert [t(free, p) for p in four] == [0, 1, 2, 0]

    def residual_loss(system):
        return loss(system, residual, target_singles)

    assert residual_loss(free) == 4 == loss(induced, target_pairs, target_singles)

    # Step 3: exchange 4 and 3 between {2,4,6} and {3,5,6}.
    free2 = [induced[1], sym(induced[2], 4, 3), sym(induced[3], 3, 4)]
    assert free2 == [B(1, 3, 5), B(2, 3, 6), B(4, 5, 6)]
    assert residual_loss(free2) == 0
    committed = frozen + free2
    assert committed == [B(1, 2, 4), B(1, 3, 5), B(2, 3, 6), B(4, 5, 6)]
    assert loss(committed, target_pairs, target_singles) == 0
    assert pair_counts(committed) == pair_counts(X0)
    assert singleton_counts(committed) == singleton_counts(X0)
    assert t(committed, {1, 2, 4}) == 1 and t(committed, {4, 5, 6}) == 1

    frozen2 = [committed[0], committed[3]]
    remaining = [committed[1], committed[2]]
    d2 = {i: quotas(committed)[i] - quotas(frozen2).get(i, 0) for i in V}
    assert d2 == {1: 1, 2: 1, 3: 2, 4: 0, 5: 1, 6: 1}
    assert total_h(remaining, 3) == 2 == total_h(committed, 3) - total_h(frozen2, 3)
    assert Fraction(total_h(free, 3), total_h(committed, 3)) == Fraction(3, 4)
    assert Fraction(total_h(remaining, 3), total_h(committed, 3)) == Fraction(1, 2)

    # Proposition 5.3 bound, with the common frozen block {1,2,4}.
    frozen_one = [committed[0]]
    free_a = [b for b in induced if b != frozen_one[0]]
    free_b = [b for b in committed if b != frozen_one[0]]
    assert sorted(map(len, free_a)) == sorted(map(len, free_b))
    assert distance(induced, committed, 3) <= Fraction(3, 4)

    print(f"[PASS] Section 5: E(X0) = {loss(X0, target_pairs, target_singles)}, "
          f"E(X~) = {e_ind}, E(X') = {loss(committed, target_pairs, target_singles)}")
    print(f"       d^(1) = {tuple(d1[i] for i in V)}, M3^(1) = {m3}, "
          f"tau^(1)(23,24,35,45) = {tuple(residual[p] for p in four)}, "
          f"actual = {tuple(t(free, p) for p in four)}")
    print(f"       E1(R~0) = {residual_loss(free)}, E1(R') = {residual_loss(free2)}; "
          f"F^(2) sizes, d^(2) = {tuple(d2[i] for i in V)}, T3(R2) = {total_h(remaining, 3)}")
    print(f"       frozen h3 bounds: {Fraction(total_h(free, 3), 4)} -> "
          f"{Fraction(total_h(remaining, 3), 4)}; d3(X~,X') = "
          f"{distance(induced, committed, 3)} <= 3/4")


# --------------------------------------------------------------------------- #
# Proposition 5.1 (residual identity) tested on every frozen subset
# --------------------------------------------------------------------------- #
def check_residual_identity():
    X0 = [B(1, 2, 3), B(1, 4, 5), B(2, 4, 6), B(3, 5, 6)]
    V = [1, 2, 3, 4, 5, 6]
    pairs = list(combinations(V, 2))
    target_pairs = {p: t(X0, p) for p in pairs}
    target_singles = {i: 0 for i in V}
    committed = [B(1, 2, 4), B(1, 3, 5), B(2, 3, 6), B(4, 5, 6)]
    checked = 0
    for r in range(5):
        for ids in combinations(range(4), r):
            frozen = [committed[i] for i in ids]
            free = [committed[i] for i in range(4) if i not in ids]
            residual = {p: target_pairs[p] - t(frozen, p) for p in pairs}
            assert loss(committed, target_pairs, target_singles) == \
                   loss(free, residual, target_singles)
            checked += 1
    print(f"[PASS] Proposition 5.1 identity verified on all {checked} frozen subsets")


# --------------------------------------------------------------------------- #
# Section 6: clique candidate vs finite resources, and reachability
# --------------------------------------------------------------------------- #
def legal_switches(system):
    """All legal 2-switches (no forbidden pairs in this paper's examples)."""
    out = []
    for i, j in combinations(range(len(system)), 2):
        A, Bb = system[i], system[j]
        for a in sorted(A - Bb, key=str):
            for b in sorted(Bb - A, key=str):
                new = system[:]
                new[i] = frozenset((A - {a}) | {b})
                new[j] = frozenset((Bb - {b}) | {a})
                out.append((i, j, a, b, new))
    return out


def apply_switch(system, i, j, a, b):
    new = list(system)
    new[i] = frozenset((system[i] - {a}) | {b})
    new[j] = frozenset((system[j] - {b}) | {a})
    return new


def finite_models(universe, size_counts, quota_map):
    """All multisets of blocks with the given size distribution and quotas."""
    from math import comb
    types = []
    for k, count in size_counts.items():
        for _ in range(count):
            types.append(k)
    choices = [list(combinations(universe, k)) for k in types]
    results = []

    def rec(pos, used, chosen):
        if pos == len(choices):
            if all(used.get(e, 0) == quota_map[e] for e in universe):
                results.append(list(chosen))
            return
        for block in choices[pos]:
            nxt = dict(used)
            ok = True
            for e in block:
                nxt[e] = nxt.get(e, 0) + 1
                if nxt[e] > quota_map[e]:
                    ok = False
                    break
            if ok:
                chosen.append(frozenset(block))
                rec(pos + 1, nxt, chosen)
                chosen.pop()

    rec(0, {}, [])
    # Different choice orders can produce the same multiset; keep one copy.
    unique = {}
    for model in results:
        unique.setdefault(tuple(sorted(model, key=lambda b: sorted(b, key=str))), model)
    return list(unique.values())


def check_section6():
    universe = ["a", "b", "c", "d"]
    XC = [B("a", "b", "d"), B("a", "c"), B("b", "c")]
    assert quotas(XC) == {"a": 2, "b": 2, "c": 2, "d": 1}
    assert {k: v for k, v in
            {s: sum(1 for blk in XC if len(blk) == s) for s in (2, 3)}.items()} == {2: 2, 3: 1}
    support = sorted(pair_counts(XC))
    assert len(support) == 5
    triangles = [S for S in combinations(universe, 3)
                 if all(tuple(sorted(p)) in support for p in combinations(S, 2))]
    assert [tuple(sorted(S)) for S in triangles] == [("a", "b", "c"), ("a", "b", "d")]

    models = finite_models(universe, {3: 1, 2: 2}, {"a": 2, "b": 2, "c": 2, "d": 1})
    covered = [m for m in models if all(t(m, p) >= 1 for p in support)]
    assert covered, "coverage-constrained models must exist"
    best = max(t(m, ("a", "b", "c")) for m in covered)
    assert best == 0
    relaxed = max(t(m, ("a", "b", "c")) for m in models)
    assert relaxed == 1

    # Reachability: XA -> XB.
    XA = [B(1, 2, 3), B(1, 4, 5), B(2, 4, 6), B(3, 5, 6)]
    XB = [B(1, 2, 4), B(1, 3, 5), B(2, 3, 6), B(4, 5, 6)]
    base_pairs = pair_counts(XA)
    moves = legal_switches(XA)
    assert moves, "XA must admit legal switches"
    exact_steps = [m for m in moves if pair_counts(m[4]) == base_pairs]
    assert exact_steps == [], "no nontrivial single switch preserves all pair counts"

    # Two ordinary switches reach XB.
    first = [m for m in moves if m[4] != XA]
    two_step = False
    for m in first:
        mid = m[4]
        for i, j in combinations(range(len(mid)), 2):
            A, Bb = mid[i], mid[j]
            for a in sorted(A - Bb, key=str):
                for b in sorted(Bb - A, key=str):
                    if apply_switch(mid, i, j, a, b) == XB:
                        two_step = True
    assert two_step

    # One matched zero-sum trade reaches XB.
    def signature(system, mv):
        """Full low-order change D, as in (4.1) and (4.3)."""
        i, j, a, b, _ = mv
        A, Bb = system[i], system[j]
        A0, B0 = A - {a}, Bb - {b}
        dp = {}
        for z in A0 | B0:
            d = int(z in B0) - int(z in A0)
            if d:
                dp[tuple(sorted((a, z), key=str))] = d
                dp[tuple(sorted((b, z), key=str))] = -d
        delta = int(len(Bb) == 1) - int(len(A) == 1)
        ds = {a: delta, b: -delta} if delta else {}
        return dp, ds

    trade_hits = 0
    for m1 in moves:
        d1p, d1s = signature(XA, m1)
        for m2 in moves:
            if len({m1[0], m1[1], m2[0], m2[1]}) != 4:
                continue
            d2p, d2s = signature(XA, m2)
            keys = set(d1p) | set(d2p)
            if all(d1p.get(p, 0) + d2p.get(p, 0) == 0 for p in keys) \
                    and all(d1s.get(e, 0) + d2s.get(e, 0) == 0
                            for e in set(d1s) | set(d2s)):
                out = apply_switch(apply_switch(XA, *m1[:4]), *m2[:4])
                assert pair_counts(out) == base_pairs
                assert singleton_counts(out) == singleton_counts(XA)
                if out == XB:
                    trade_hits += 1
    assert trade_hits >= 1

    # The finite integer model with exact pair counts admits t_124 >= 1 (witness XB).
    assert pair_counts(XB) == pair_counts(XA)
    assert quotas(XB) == quotas(XA)
    assert t(XB, (1, 2, 4)) == 1

    print(f"[PASS] Section 6: support edges = {len(support)}; triangles = "
          f"{[tuple(sorted(S)) for S in triangles]}")
    print(f"       coverage-feasible models = {len(covered)}; U(abc) = {best}; "
          f"relaxed U(abc) = {relaxed}")
    print(f"       nontrivial pair-preserving single switches from XA = {len(exact_steps)}; "
          f"two ordinary switches reach XB; matched zero-sum trades reaching XB = {trade_hits}")


# --------------------------------------------------------------------------- #
# Proposition 3.1: numerical sanity check of the lower bound
# --------------------------------------------------------------------------- #
def check_lower_bound():
    X = [B(1), B(2, 3)]
    M, V = 2, [1, 2, 3]
    c = quotas(X)
    target_pairs = {(1, 2): 1, (1, 3): 0, (2, 3): 0}
    target_singles = {1: 0, 2: 0, 3: 1}
    lower = Fraction(0)
    for i, j in combinations(V, 2):
        lo, hi = max(0, c[i] + c[j] - M), min(c[i], c[j])
        target = target_pairs[(i, j)]
        dist = 0 if lo <= target <= hi else min(abs(target - lo), abs(target - hi))
        lower += dist ** 2
    m1 = sum(1 for blk in X if len(blk) == 1)
    for e in V:
        lo, hi = 0, min(c[e], m1)
        target = target_singles[e]
        dist = 0 if lo <= target <= hi else min(abs(target - lo), abs(target - hi))
        lower += dist ** 2
    assert lower <= loss(X, target_pairs, target_singles)
    print(f"[PASS] Proposition 3.1: lower bound = {lower} <= E(X) = "
          f"{loss(X, target_pairs, target_singles)}")


def main():
    check_intro_and_zero_sum()
    check_local_delta()
    check_lower_bound()
    check_directed_example()
    check_residual_identity()
    check_section6()
    print("\nALL PAPER NUMBERS VERIFIED INDEPENDENTLY.")


if __name__ == "__main__":
    main()
