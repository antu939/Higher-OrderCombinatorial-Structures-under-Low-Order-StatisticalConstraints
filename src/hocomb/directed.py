"""Directed induction, provisional freezing, residual refitting, commit checks.

A proposed frozen block is NEVER a committed frozen block until the entire
candidate has passed exact/tolerance acceptance. Section 5 distinction.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from math import comb
from typing import Iterable

from .core import Element, HardConstraints, LossSpec, ResidualBudget, System, verify_residual_equivalence
from .switches import Swap, all_swaps, apply, local_loss_delta


@dataclass(frozen=True)
class Goal:
    elements: frozenset[Element]
    multiplicity: int = 1
    relation: str = ">="

    def __post_init__(self) -> None:
        if len(self.elements) < 3 or self.multiplicity < 0 or self.relation not in (">=", "="):
            raise ValueError("A goal needs >=3 elements, nonnegative count, relation >= or =")

    def holds(self, x: System) -> bool:
        actual = x.count(self.elements)
        return actual >= self.multiplicity if self.relation == ">=" else actual == self.multiplicity

    def deficit(self, x: System) -> int:
        actual = x.count(self.elements)
        if self.relation == ">=":
            return max(0, self.multiplicity - actual)
        return abs(self.multiplicity - actual)


@dataclass(frozen=True)
class ConstructionResult:
    status: str
    final: System
    frozen_ids: frozenset[int]
    committed: tuple[Goal, ...]
    attempted_inductions: int
    accepted_steps: tuple[dict, ...]


def is_acceptable(
    x: System,
    initial: System,
    hard: HardConstraints,
    targets: LossSpec,
    mode: str,
    epsilon: float,
    goals: Iterable[Goal],
    previously_frozen: Iterable[int],
    frozen_reference: System | None = None,
) -> bool:
    if not hard.check(x):
        return False
    reference = initial if frozen_reference is None else frozen_reference
    if any(x.blocks[i] != reference.blocks[i] for i in previously_frozen):
        return False
    if not all(g.holds(x) for g in goals):
        return False
    if mode == "exact":
        return x.equivalent_low_order(initial)
    if mode == "tolerance":
        return targets.loss(x) <= epsilon + 1e-9
    raise ValueError("Mode must be exact or tolerance")


def residual_refit_bfs(
    provisional: System,
    initial: System,
    targets: LossSpec,
    hard: HardConstraints,
    frozen_ids: frozenset[int],
    commitments: Iterable[Goal],
    mode: str = "exact",
    epsilon: float = 0.0,
    max_depth: int = 3,
    max_states: int = 3000,
) -> tuple[System | None, int]:
    """Small-instance compensator: shortest legal free-swap path via BFS.

    Intermediate candidates need only satisfy hard constraints and freeze rules;
    exact/tolerance acceptance is required at the END of the branch.
    """
    if mode not in {"exact", "tolerance"}:
        raise ValueError("Invalid validation mode")
    if not hard.check(provisional):
        raise ValueError("Provisional candidate violates hard constraints")
    free_ids = set(range(len(provisional.blocks))) - frozen_ids
    if not verify_residual_equivalence(provisional, frozen_ids, targets):
        raise AssertionError("Residual identity failed before refit")

    queue = deque([(provisional, 0)])
    seen = {provisional.state_key()}
    while queue:
        current, depth = queue.popleft()
        if is_acceptable(
            current, initial, hard, targets, mode, epsilon, commitments,
            frozen_ids, frozen_reference=provisional
        ):
            assert verify_residual_equivalence(current, frozen_ids, targets)
            return current, len(seen)
        if depth >= max_depth:
            continue
        moves = list(all_swaps(current, hard.forbidden, free_ids))
        # Lower loss first accelerates search but BFS still searches all
        # depth-limited states, rather than asserting a local optimum is global.
        moves.sort(key=lambda s: local_loss_delta(current, s, targets))
        for move in moves:
            nxt = apply(current, move, hard.forbidden)
            key = nxt.state_key()
            if key in seen:
                continue
            if len(seen) >= max_states:
                return None, len(seen)
            seen.add(key)
            queue.append((nxt, depth + 1))
    return None, len(seen)


def construct_directed(
    initial: System,
    goals: Iterable[Goal],
    targets: LossSpec | None = None,
    forbidden: Iterable[tuple[Element, Element]] = (),
    mode: str = "exact",
    epsilon: float = 0.0,
    induction_budget: int = 250,
    refit_depth: int = 3,
    refit_states: int = 3000,
) -> ConstructionResult:
    """Finite-budget implementation of the Section 5 induction/commit logic.

    This is an exhaustive one-switch induction + depth-bounded BFS refit
    HEURISTIC, not a completeness proof for the general algorithm.
    """
    if mode not in {"exact", "tolerance"}:
        raise ValueError("Invalid validation mode")
    if induction_budget < 0:
        raise ValueError("Negative induction budget")
    target = targets or LossSpec.from_reference(initial)
    hard = HardConstraints.from_system(initial, forbidden)
    hard.require(initial)
    if mode == "tolerance" and target.loss(initial) > epsilon:
        raise ValueError("Initial state fails tolerance")
    all_goals = tuple(goals)
    x = initial
    frozen: frozenset[int] = frozenset()
    committed = tuple(g for g in all_goals if g.holds(x))
    attempts = 0
    events: list[dict] = []

    while len(committed) != len(all_goals) and attempts < induction_budget:
        goal = next(g for g in all_goals if g not in committed)
        free_ids = set(range(len(x.blocks))) - frozen
        proposals = []
        for move in all_swaps(x, hard.forbidden, free_ids):
            new = apply(x, move, hard.forbidden)
            improvement = goal.deficit(x) - goal.deficit(new)
            if improvement > 0:
                proposals.append((improvement, local_loss_delta(x, move, target),
                                  move, new))
        proposals.sort(key=lambda t: (-t[0], t[1], t[2].i, t[2].j))
        accepted = False
        for improvement, delta, move, induced in proposals:
            if attempts >= induction_budget:
                break
            attempts += 1
            # Only choose records ACTUALLY containing U; duplicate types have
            # separate record indices. >= goals can be secured by these anchors.
            anchors = set(frozen)
            if goal.multiplicity:
                current_cover = sum(goal.elements <= induced.blocks[i] for i in anchors)
                need = max(0, goal.multiplicity - current_cover)
                extra = [
                    i for i in range(len(induced.blocks))
                    if i not in anchors and goal.elements <= induced.blocks[i]
                ]
                if len(extra) < need:
                    continue
                anchors.update(extra[:need])
            temporary_frozen = frozenset(anchors)
            if not verify_residual_equivalence(induced, temporary_frozen, target):
                raise AssertionError("Incorrect residual subtraction")
            candidate, visited = residual_refit_bfs(
                induced, initial, target, hard, temporary_frozen,
                (*committed, goal), mode=mode, epsilon=epsilon,
                max_depth=refit_depth, max_states=refit_states,
            )
            if candidate is None:
                continue
            # Check OLD committed frozen records and all promises before
            # extending the permanent frozen set (transactional commit).
            if not is_acceptable(
                candidate, initial, hard, target, mode, epsilon,
                (*committed, goal), frozen, frozen_reference=x
            ):
                raise AssertionError("Proposed acceptance violated old commitments")
            new_commitments = tuple(g for g in all_goals if g.holds(candidate))
            events.append({
                "goal": sorted(goal.elements, key=str),
                "induction": {"i": move.i, "j": move.j,
                              "a": move.a, "b": move.b},
                "induction_delta_loss": delta,
                "provisional_loss": target.loss(induced),
                "final_loss": target.loss(candidate),
                "provisionally_frozen": sorted(temporary_frozen),
                "refit_states_seen": visited,
                "newly_committed_goal_count": len(new_commitments),
            })
            x, frozen, committed = candidate, temporary_frozen, new_commitments
            accepted = True
            break
        if not accepted:
            break

    status = (
        "SUCCESS" if len(committed) == len(all_goals)
        else "PARTIAL" if committed else "FAILURE"
    )
    assert all(g.holds(x) for g in committed)
    assert is_acceptable(x, initial, hard, target, mode, epsilon, committed,
                         frozen, frozen_reference=x)
    return ConstructionResult(status, x, frozen, committed, attempts, tuple(events))


def paper_directed_trace() -> dict:
    """Exact Section 5 four-stage witness, including AFTER-commit second freeze."""
    original = System.create([
        (1, 2, 3), (1, 4, 5), (2, 4, 6), (3, 5, 6)
    ], universe=range(1, 7))
    target = LossSpec.from_reference(original)
    hard = HardConstraints.from_system(original)
    induced = apply(original, Swap(0, 1, 3, 4))
    frozen1 = frozenset({0})  # New real record {1,2,4}
    r1 = ResidualBudget.compute(induced, frozen1, target)
    assert abs(target.loss(induced) - 4.0) < 1e-9
    assert verify_residual_equivalence(induced, frozen1, target)
    accepted = apply(induced, Swap(2, 3, 4, 3))
    goals = (Goal(frozenset({1, 2, 4})), Goal(frozenset({4, 5, 6})))
    assert is_acceptable(
        accepted, original, hard, target, "exact", 0.0, goals, frozen1,
        frozen_reference=induced
    )
    assert accepted.equivalent_low_order(original)
    assert verify_residual_equivalence(accepted, frozen1, target)
    frozen2 = frozenset({0, 3})  # Add {4,5,6}, only AFTER acceptance
    r2 = ResidualBudget.compute(accepted, frozen2, target)
    T3 = accepted.total_h(3)
    def free_h_budget(system: System, frozen: frozenset[int]) -> int:
        return sum(
            comb(len(system.blocks[i]), 3)
            for i in range(len(system.blocks))
            if i not in frozen and len(system.blocks[i]) >= 3
        )
    return {
        "reference": original,
        "induced": induced,
        "accepted": accepted,
        "goals": goals,
        "initial_loss": target.loss(original),
        "induction_loss": target.loss(induced),
        "commit_loss": target.loss(accepted),
        "frozen_first": frozen1,
        "frozen_second": frozen2,
        "residual_first": r1,
        "residual_second": r2,
        "residual_identity_holds": (
            verify_residual_equivalence(induced, frozen1, target)
            and verify_residual_equivalence(accepted, frozen2, target)
        ),
        "frozen_distance_bound_first": free_h_budget(accepted, frozen1) / T3,
        "frozen_distance_bound_second": free_h_budget(accepted, frozen2) / T3,
    }
