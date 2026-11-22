"""Legal 2-switches, exact local loss deltas, and zero-sum paired trades."""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Iterable, Iterator

from .core import Element, Pair, LossSpec, System, order_key, ordered, pair


@dataclass(frozen=True)
class Swap:
    i: int
    j: int
    a: Element  # Leaves record i
    b: Element  # Leaves record j


@dataclass(frozen=True)
class Signature:
    """Sparse low-order change D, including singleton diagonal terms."""
    pairs: tuple[tuple[Pair, int], ...]
    singles: tuple[tuple[Element, int], ...]

    def opposite(self) -> "Signature":
        return Signature(
            tuple((p, -d) for p, d in self.pairs),
            tuple((e, -d) for e, d in self.singles),
        )


@dataclass(frozen=True)
class Trade:
    first: Swap
    second: Swap
    result: System
    distance: float


def legal(x: System, s: Swap, forbidden: Iterable[Pair] = ()) -> bool:
    if s.i == s.j or not (0 <= s.i < len(x.blocks) and 0 <= s.j < len(x.blocks)):
        return False
    A, B = x.blocks[s.i], x.blocks[s.j]
    if s.a not in A - B or s.b not in B - A:
        return False
    forbidden_set = set(forbidden)
    A1, B1 = (A - {s.a}) | {s.b}, (B - {s.b}) | {s.a}
    return all(
        pair(u, v) not in forbidden_set
        for block in (A1, B1) for u, v in combinations(ordered(block), 2)
    )


def apply(x: System, s: Swap, forbidden: Iterable[Pair] = ()) -> System:
    if not legal(x, s, forbidden):
        raise ValueError(f"Illegal 2-switch: {s}")
    return x.replace(s.i, s.j, s.a, s.b)


def all_swaps(
    x: System,
    forbidden: Iterable[Pair] = (),
    mutable_ids: Iterable[int] | None = None,
) -> Iterator[Swap]:
    indices = sorted(range(len(x.blocks)) if mutable_ids is None else set(mutable_ids))
    for i, j in combinations(indices, 2):
        for a in ordered(x.blocks[i] - x.blocks[j]):
            for b in ordered(x.blocks[j] - x.blocks[i]):
                s = Swap(i, j, a, b)
                if legal(x, s, forbidden):
                    yield s


def count_delta(x: System, s: Swap) -> tuple[dict[Pair, int], dict[Element, int]]:
    """Equation (3): local deltas without recounting the complete system."""
    if not legal(x, s):
        raise ValueError("Cannot calculate delta for invalid swap")
    A0 = x.blocks[s.i] - {s.a}
    B0 = x.blocks[s.j] - {s.b}
    dp: dict[Pair, int] = {}
    for z in A0 | B0:
        d = int(z in B0) - int(z in A0)
        if d:
            dp[pair(s.a, z)] = d
            dp[pair(s.b, z)] = -d
    ds: dict[Element, int] = {}
    d = int(len(x.blocks[s.j]) == 1) - int(len(x.blocks[s.i]) == 1)
    if d:
        ds[s.a], ds[s.b] = d, -d
    return dp, ds


def signature(x: System, s: Swap) -> Signature:
    dp, ds = count_delta(x, s)
    return Signature(
        tuple(sorted(dp.items(), key=lambda item:
                     (order_key(item[0][0]), order_key(item[0][1])))),
        tuple(sorted(ds.items(), key=lambda item: order_key(item[0]))),
    )


def local_loss_delta(x: System, s: Swap, spec: LossSpec) -> float:
    """Exact delta E: sum w * (2r*delta+delta^2), no full loss recomputation."""
    dp, ds = count_delta(x, s)
    pc, sc = x.pair_counts(), x.singleton_counts()
    pair_delta = sum(
        spec.pair_weights.get(p, 1.0) *
        (2 * (pc[p] - spec.pair_targets.get(p, 0.0)) * d + d * d)
        for p, d in dp.items()
    )
    singleton_delta = spec.singleton_scale * sum(
        spec.singleton_weights.get(e, 1.0) *
        (2 * (sc[e] - spec.singleton_targets.get(e, 0.0)) * d + d * d)
        for e, d in ds.items()
    )
    return pair_delta + singleton_delta


def matched_trades(
    x: System, forbidden: Iterable[Pair] = (), h: int = 3
) -> list[Trade]:
    """Enumerate disjoint paired swaps with cancelling low-order signatures.

    A trade is accepted only if its FULL low-order counts are preserved.
    All operations are checked against forbidden pairs.
    Suitable for small research instances rather than massive enumeration.
    """
    moves = list(all_swaps(x, forbidden))
    lookup: dict[Signature, list[Swap]] = {}
    for s in moves:
        lookup.setdefault(signature(x, s), []).append(s)

    found: dict[tuple, Trade] = {}
    for s in moves:
        opposite = signature(x, s).opposite()
        for t in lookup.get(opposite, []):
            if len({s.i, s.j, t.i, t.j}) != 4:
                continue
            y = apply(apply(x, s, forbidden), t, forbidden)
            if not x.equivalent_low_order(y):
                raise AssertionError("Cancelled signatures did not conserve counts")
            if x.higher_counts(h) == y.higher_counts(h):
                continue
            key = y.state_key()
            new_trade = Trade(s, t, y, x.distance(y, h))
            if key not in found:
                found[key] = new_trade
    return sorted(
        found.values(), key=lambda t: (-t.distance, t.result.state_key())
    )
