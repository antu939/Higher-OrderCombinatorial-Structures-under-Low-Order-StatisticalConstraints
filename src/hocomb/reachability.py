"""Finite labelled-state reachability, paper Section 6.

Distinguishes (a) endpoints with hard constraints and (b) paths where
every committed intermediate state must also preserve exact low-order counts.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Literal

from .core import HardConstraints, System
from .switches import all_swaps, apply, matched_trades


@dataclass(frozen=True)
class PathResult:
    found: bool
    path: tuple[System, ...]
    transitions: int | None
    visited_states: int
    truncated: bool


def find_path(
    start: System,
    goal: System,
    operation: Literal["switch", "zero_sum_trade"] = "switch",
    strict_intermediate: bool = False,
    max_depth: int = 3,
    max_states: int = 10000,
    forbidden: tuple[tuple, ...] = (),
) -> PathResult:
    hard = HardConstraints.from_system(start, forbidden)
    hard.require(start)
    if not hard.check(goal):
        raise ValueError("Target must satisfy identical hard constraints")
    if operation not in {"switch", "zero_sum_trade"}:
        raise ValueError("Invalid operation")
    queue = deque([(start, (start,))])
    seen = {start.state_key()}
    truncated = False
    while queue:
        current, path = queue.popleft()
        if current.state_key() == goal.state_key():
            return PathResult(True, path, len(path) - 1, len(seen), truncated)
        if len(path) - 1 >= max_depth:
            continue
        if operation == "switch":
            neighbors = (
                apply(current, s, hard.forbidden)
                for s in all_swaps(current, hard.forbidden)
            )
        else:
            neighbors = (
                t.result for t in matched_trades(
                    current, forbidden=hard.forbidden, h=3
                )
            )
        for nxt in neighbors:
            if strict_intermediate and not nxt.equivalent_low_order(start):
                continue
            key = nxt.state_key()
            if key in seen:
                continue
            if len(seen) >= max_states:
                truncated = True
                return PathResult(False, (), None, len(seen), truncated)
            seen.add(key)
            queue.append((nxt, path + (nxt,)))
    return PathResult(False, (), None, len(seen), truncated)
