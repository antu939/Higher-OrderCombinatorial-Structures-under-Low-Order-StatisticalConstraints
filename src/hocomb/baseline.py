"""Initialization and residual-guided fitting (paper Section 3)."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from math import exp
from random import Random
from typing import Iterable, Mapping

from .core import Element, HardConstraints, LossSpec, System, order_key, pair, pairs
from .switches import Swap, all_swaps, apply, count_delta, local_loss_delta


@dataclass(frozen=True)
class FitResult:
    initial: System
    best: System
    final: System
    initial_loss: float
    best_loss: float
    trajectory: tuple[dict, ...]


def feasible_initialization(
    universe: Iterable[Element],
    sizes: Iterable[int],
    quotas: Mapping[Element, int],
    forbidden: Iterable[tuple[Element, Element]] = (),
) -> System:
    """Integral maximum flow without forbidden pairs.

    With forbidden pairs, fall back to the exact block-type integer solver,
    intended for small research instances. No optimization dependency.
    """
    elements = tuple(sorted(universe, key=order_key))
    row_sizes = tuple(sizes)
    forbidden_pairs = frozenset(pair(*p) for p in forbidden)
    if sum(row_sizes) != sum(quotas.get(e, 0) for e in elements):
        raise ValueError("Quota total differs from total record capacity")
    if any(k < 1 or k > len(elements) for k in row_sizes):
        raise ValueError("Record size outside [1,n]")
    if any(quotas.get(e, 0) < 0 for e in elements):
        raise ValueError("Negative quota")

    if forbidden_pairs:
        from .feasibility import maximize_occurrences
        from collections import Counter
        result = maximize_occurrences(
            elements, quotas, Counter(row_sizes), forbidden=forbidden_pairs
        )
        if not result.feasible or result.witness is None:
            raise ValueError("No feasible initialization for supplied constraints")
        # Assign records to the requested row-size sequence.
        waiting: dict[int, list] = {}
        for block in result.witness.blocks:
            waiting.setdefault(len(block), []).append(block)
        arranged = [waiting[k].pop() for k in row_sizes]
        output = System(elements, tuple(arranged))
        HardConstraints(
            elements, row_sizes, {e: quotas.get(e, 0) for e in elements},
            forbidden_pairs
        ).require(output)
        return output

    # Residual network with reverse edges for Dinic maximum flow.
    M, n = len(row_sizes), len(elements)
    source, sink = 0, M + n + 1
    adjacency: list[list[list[int]]] = [[] for _ in range(sink + 1)]

    def edge(u: int, v: int, cap: int) -> None:
        adjacency[u].append([v, len(adjacency[v]), cap])
        adjacency[v].append([u, len(adjacency[u]) - 1, 0])

    for i, k in enumerate(row_sizes):
        edge(source, 1 + i, k)
        for j in range(n):
            edge(1 + i, 1 + M + j, 1)
    for j, e in enumerate(elements):
        edge(1 + M + j, sink, quotas.get(e, 0))

    total = 0
    while True:
        level = [-1] * (sink + 1)
        level[source] = 0
        queue = deque([source])
        while queue:
            u = queue.popleft()
            for v, _, cap in adjacency[u]:
                if cap and level[v] < 0:
                    level[v] = level[u] + 1
                    queue.append(v)
        if level[sink] < 0:
            break
        ptr = [0] * (sink + 1)

        def send(u: int, amount: int) -> int:
            if u == sink:
                return amount
            while ptr[u] < len(adjacency[u]):
                e = adjacency[u][ptr[u]]
                v, rev, cap = e
                if cap and level[v] == level[u] + 1:
                    moved = send(v, min(amount, cap))
                    if moved:
                        e[2] -= moved
                        adjacency[v][rev][2] += moved
                        return moved
                ptr[u] += 1
            return 0

        while moved := send(source, 10**9):
            total += moved
    if total != sum(row_sizes):
        raise ValueError("No feasible integer max-flow assignment")

    records = []
    for i in range(M):
        record = []
        for v, _, remaining in adjacency[1 + i]:
            if 1 + M <= v < 1 + M + n and remaining == 0:
                record.append(elements[v - 1 - M])
        records.append(record)
    output = System.create(records, universe=elements)
    HardConstraints(
        elements, row_sizes, {e: quotas.get(e, 0) for e in elements}
    ).require(output)
    return output


def fit_residuals(
    initial: System,
    targets: LossSpec,
    iterations: int = 500,
    seed: int = 2026,
    residual_proposal_probability: float = 0.70,
    start_temperature: float = 0.6,
    end_temperature: float = 0.01,
    forbidden: Iterable[tuple[Element, Element]] = (),
) -> FitResult:
    """Random+residual-guided proposals with Metropolis acceptance.

    Every proposal is a legal 2-switch. Exact local delta is checked against
    the complete objective at each accepted move. Track the best-seen state,
    as in the paper, rather than returning the last annealing state.
    """
    if iterations < 0 or not (0 <= residual_proposal_probability <= 1):
        raise ValueError("Invalid search budget or proposal probability")
    if start_temperature < 0 or end_temperature < 0:
        raise ValueError("Temperatures must be nonnegative")
    rng = Random(seed)
    constraints = HardConstraints.from_system(initial, forbidden)
    constraints.require(initial)
    x = initial
    best = initial
    current_e = best_e = targets.loss(x)
    trace = [{
        "iteration": 0, "accepted": True, "proposal": "initial",
        "delta": 0.0, "current_loss": current_e, "best_loss": best_e,
    }]
    for step in range(1, iterations + 1):
        swaps = list(all_swaps(x, constraints.forbidden))
        if not swaps:
            break
        mode = "random"
        candidate = None
        if rng.random() < residual_proposal_probability:
            pc = x.pair_counts()
            active = [
                p for p in pairs(x.universe)
                if abs(pc[p] - targets.pair_targets.get(p, 0.0)) > 1e-12
                and targets.pair_weights.get(p, 1.0) > 0
            ]
            if active:
                weights = [
                    abs(pc[p] - targets.pair_targets.get(p, 0.0))
                    * targets.pair_weights.get(p, 1.0)
                    for p in active
                ]
                chosen = rng.choices(active, weights=weights, k=1)[0]
                residual = pc[chosen] - targets.pair_targets.get(chosen, 0.0)
                helpful = [
                    s for s in swaps
                    if count_delta(x, s)[0].get(chosen, 0) * residual < 0
                ]
                if helpful:
                    candidate = min(
                        helpful, key=lambda s: local_loss_delta(x, s, targets)
                    )
                    mode = "residual"
        if candidate is None:
            candidate = rng.choice(swaps)
        delta = local_loss_delta(x, candidate, targets)
        temperature = (
            start_temperature * (end_temperature / start_temperature)
            ** ((step - 1) / max(1, iterations - 1))
            if start_temperature > 0 and end_temperature > 0
            else 0.0
        )
        accept = delta <= 0 or (
            temperature > 0 and rng.random() < exp(-delta / temperature)
        )
        if accept:
            next_x = apply(x, candidate, constraints.forbidden)
            exact_e = targets.loss(next_x)
            if abs((exact_e - current_e) - delta) > 1e-8:
                raise AssertionError("Local delta disagrees with full loss")
            constraints.require(next_x)
            x, current_e = next_x, exact_e
            if current_e < best_e - 1e-12:
                best, best_e = x, current_e
        trace.append({
            "iteration": step, "accepted": bool(accept), "proposal": mode,
            "delta": delta, "current_loss": current_e, "best_loss": best_e,
        })
        if best_e < 1e-12:
            break
    return FitResult(initial, best, x, trace[0]["current_loss"],
                     best_e, tuple(trace))
