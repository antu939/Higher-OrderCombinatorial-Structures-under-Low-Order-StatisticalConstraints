"""Mathematical model and invariant checks from paper Sections 2--5.

Records are indexed: repeated blocks remain distinct records.
A higher-order count t_S counts *containing* blocks, not exact block types.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from itertools import combinations
from math import comb
from typing import Iterable, Mapping

Element = int | str
Pair = tuple[Element, Element]


def order_key(x: Element) -> tuple:
    """A stable order supporting both numerical and letter-labelled examples."""
    return (0, x) if isinstance(x, int) else (1, str(x))


def ordered(items: Iterable[Element]) -> tuple[Element, ...]:
    return tuple(sorted(items, key=order_key))


def pair(a: Element, b: Element) -> Pair:
    if a == b:
        raise ValueError("A pair must contain two distinct elements")
    x, y = ordered((a, b))
    return (x, y)


def pairs(elements: Iterable[Element]) -> tuple[Pair, ...]:
    return tuple(combinations(ordered(elements), 2))


@dataclass(frozen=True)
class System:
    universe: tuple[Element, ...]
    blocks: tuple[frozenset[Element], ...]

    @classmethod
    def create(
        cls, records: Iterable[Iterable[Element]],
        universe: Iterable[Element] | None = None,
    ) -> "System":
        seqs = [tuple(record) for record in records]
        for record in seqs:
            if not record:
                raise ValueError("The paper excludes empty records")
            if len(set(record)) != len(record):
                raise ValueError(f"Duplicate element within record: {record}")
        blocks = tuple(frozenset(r) for r in seqs)
        all_elements = set().union(*blocks) if blocks else set()
        u = ordered(all_elements if universe is None else universe)
        return cls(u, blocks)

    def __post_init__(self) -> None:
        if len(set(self.universe)) != len(self.universe):
            raise ValueError("Duplicate elements in the universe")
        if ordered(self.universe) != self.universe:
            raise ValueError("Universe must be in canonical order")
        allowed = set(self.universe)
        for block in self.blocks:
            if not block or not block <= allowed:
                raise ValueError("Empty block or element outside the universe")

    def replace(self, i: int, j: int, a: Element, b: Element) -> "System":
        blocks = list(self.blocks)
        blocks[i] = (blocks[i] - {a}) | {b}
        blocks[j] = (blocks[j] - {b}) | {a}
        return System(self.universe, tuple(blocks))

    def readable(self) -> list[list[Element]]:
        return [list(ordered(block)) for block in self.blocks]

    def quotas(self) -> Counter:
        return Counter(x for block in self.blocks for x in block)

    def sizes(self) -> tuple[int, ...]:
        return tuple(len(b) for b in self.blocks)

    def size_distribution(self) -> Counter:
        return Counter(self.sizes())

    def pair_counts(self) -> Counter:
        return Counter(
            p for block in self.blocks
            for p in combinations(ordered(block), 2)
        )

    def singleton_counts(self) -> Counter:
        return Counter(next(iter(b)) for b in self.blocks if len(b) == 1)

    def higher_counts(self, h: int) -> Counter:
        if h < 1:
            raise ValueError("h must be positive")
        return Counter(
            sub for block in self.blocks if len(block) >= h
            for sub in combinations(ordered(block), h)
        )

    def count(self, elements: Iterable[Element]) -> int:
        subset = frozenset(elements)
        if not subset:
            raise ValueError("Containment count requires nonempty subset")
        return sum(subset <= block for block in self.blocks)

    def total_h(self, h: int) -> int:
        return sum(comb(len(b), h) for b in self.blocks if len(b) >= h)

    def distance(self, other: "System", h: int) -> float:
        if self.universe != other.universe or self.total_h(h) != other.total_h(h):
            raise ValueError("Distance requires equal universe and total h-count")
        total = self.total_h(h)
        if total == 0:
            raise ValueError("Distance undefined for T_h=0")
        x, y = self.higher_counts(h), other.higher_counts(h)
        return sum(abs(x[s] - y[s]) for s in x.keys() | y.keys()) / (2 * total)

    def equivalent_low_order(self, other: "System") -> bool:
        return (
            self.universe == other.universe
            and self.sizes() == other.sizes()
            and self.quotas() == other.quotas()
            and self.pair_counts() == other.pair_counts()
            and self.singleton_counts() == other.singleton_counts()
        )

    def state_key(self) -> tuple[tuple[Element, ...], ...]:
        """Record-labelled state; important for freeze/reachability tests."""
        return tuple(ordered(b) for b in self.blocks)


@dataclass(frozen=True)
class HardConstraints:
    universe: tuple[Element, ...]
    sizes: tuple[int, ...]
    quotas: Mapping[Element, int]
    forbidden: frozenset[Pair] = frozenset()

    @classmethod
    def from_system(
        cls, system: System, forbidden: Iterable[tuple[Element, Element]] = ()
    ) -> "HardConstraints":
        return cls(
            system.universe, system.sizes(),
            {e: system.quotas()[e] for e in system.universe},
            frozenset(pair(a, b) for a, b in forbidden),
        )

    def check(self, system: System) -> bool:
        if system.universe != self.universe or system.sizes() != self.sizes:
            return False
        if any(system.quotas()[e] != self.quotas[e] for e in self.universe):
            return False
        return all(
            p not in self.forbidden
            for block in system.blocks for p in combinations(ordered(block), 2)
        )

    def require(self, system: System) -> None:
        if not self.check(system):
            raise AssertionError("Hard constraints (sizes, quotas, forbidden) violated")


@dataclass(frozen=True)
class LossSpec:
    """Equation (2): pair and singleton squared-count targets."""
    pair_targets: Mapping[Pair, float]
    singleton_targets: Mapping[Element, float] = field(default_factory=dict)
    pair_weights: Mapping[Pair, float] = field(default_factory=dict)
    singleton_weights: Mapping[Element, float] = field(default_factory=dict)
    singleton_scale: float = 1.0

    @classmethod
    def from_reference(cls, x: System) -> "LossSpec":
        pc, sc = x.pair_counts(), x.singleton_counts()
        return cls(
            {p: float(pc[p]) for p in pairs(x.universe)},
            {e: float(sc[e]) for e in x.universe},
        )

    def loss(self, x: System) -> float:
        pc, sc = x.pair_counts(), x.singleton_counts()
        return (
            sum(
                self.pair_weights.get(p, 1.0) *
                (pc[p] - self.pair_targets.get(p, 0.0)) ** 2
                for p in pairs(x.universe)
            )
            + self.singleton_scale * sum(
                self.singleton_weights.get(e, 1.0) *
                (sc[e] - self.singleton_targets.get(e, 0.0)) ** 2
                for e in x.universe
            )
        )

    def subtract_frozen(self, frozen: System) -> "LossSpec":
        """Equation (5): residual TARGETS, which may become negative."""
        pc, sc = frozen.pair_counts(), frozen.singleton_counts()
        return LossSpec(
            {p: self.pair_targets.get(p, 0.0) - pc[p]
             for p in pairs(frozen.universe)},
            {e: self.singleton_targets.get(e, 0.0) - sc[e]
             for e in frozen.universe},
            self.pair_weights,
            self.singleton_weights,
            self.singleton_scale,
        )


@dataclass(frozen=True)
class ResidualBudget:
    remaining_quotas: dict[Element, int]
    remaining_size_counts: dict[int, int]
    remaining_loss_targets: LossSpec

    @classmethod
    def compute(
        cls, complete: System, frozen_ids: Iterable[int], target: LossSpec
    ) -> "ResidualBudget":
        ids = frozenset(frozen_ids)
        if any(i < 0 or i >= len(complete.blocks) for i in ids):
            raise IndexError("Unknown frozen record")
        frozen = System(complete.universe, tuple(
            complete.blocks[i] for i in sorted(ids)
        ))
        total_q, frozen_q = complete.quotas(), frozen.quotas()
        total_sizes, frozen_sizes = complete.size_distribution(), frozen.size_distribution()
        return cls(
            {e: total_q[e] - frozen_q[e] for e in complete.universe},
            {k: total_sizes[k] - frozen_sizes[k] for k in total_sizes},
            target.subtract_frozen(frozen),
        )


def sub_system(complete: System, ids: Iterable[int]) -> System:
    return System(complete.universe, tuple(complete.blocks[i] for i in sorted(ids)))


def verify_residual_equivalence(
    complete: System, frozen_ids: Iterable[int], target: LossSpec
) -> bool:
    ids = frozenset(frozen_ids)
    if not ids.issubset(set(range(len(complete.blocks)))):
        raise IndexError("Invalid frozen record")
    free = sub_system(complete, set(range(len(complete.blocks))) - ids)
    residual = ResidualBudget.compute(complete, ids, target)
    return abs(target.loss(complete) - residual.remaining_loss_targets.loss(free)) < 1e-9
