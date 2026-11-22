# Higher-Order Combinatorial Structures under Low-Order Statistical Constraints

### Transformations · Directed Constructions · Realizability

**Construct prescribed higher-order patterns while preserving lower-order statistics.**

This repository contains the algorithms, constructive examples, and reproducible experiments accompanying the manuscript *Higher-Order Combinatorial Structures under Low-Order Statistical Constraints: Transformations, Directed Constructions, and Realizability*.

The central goal is **controlled construction**: starting from a feasible combinatorial system, generate specific higher-order configurations while preserving record sizes, element quotas, and prescribed pairwise statistics. The implementation connects target induction, compensating exchanges, record freezing, residual accounting, and exact acceptance checks into a unified construction workflow.

## Construction Highlights

The committed experiment outputs demonstrate the constructive capabilities of the framework on explicit finite systems.

| Capability | Verified result | Experiment |
| --- | --- | --- |
| **Targeted construction** | Both target triples **{1,2,4}** and **{4,5,6}** realized with final low-order loss **E = 0** | [Directed construction](results/ex03_directed_freeze.json) |
| **Constructive search** | **1 induction attempt** and **15 residual states explored** in the automated directed-construction example | [Directed construction](results/ex03_directed_freeze.json) |
| **Higher-order variation** | **9 distinct nontrivial** matched-trade outputs found; maximum demonstrated third-order distance **d₃ = 1** | [Zero-sum trades](results/ex02_zero_sum.json) |
| **Residual compensation** | Low-order loss follows **0 → 4 → 0** across reference, provisional induction, and accepted construction | [Directed construction](results/ex03_directed_freeze.json) |
| **Guided fitting** | Weighted loss reduced from **16 to 0 in 37 iterations** with fixed seed 2026 | [Fitting benchmark](results/ex06_seeded_fitting.json) |
| **Finite realizability** | Resource-constrained integer model certifies **U({a,b,c}) = 0** for a support-graph triangle | [Realizability](results/ex04_resource_conflict.json) |

These figures describe the supplied reproducible instances. Construction quality is measured through target realization, constraint preservation, residual correction, higher-order variation, and the search effort recorded by each experiment.

## The Construction Problem

Let \(\mathcal{B}=(B_1,\ldots,B_M)\) be an indexed multiset of blocks over a finite universe \(V\). For a nonempty subset \(S\subseteq V\), define its occurrence count by

$$
t_S(X)=\sum_{o=1}^{M}\mathbf{1}\{S\subseteq B_o\}.
$$

For fixed block sizes, the total number of order-\(h\) occurrences is

$$
T_h=\sum_{o=1}^{M}\binom{|B_o|}{h}.
$$

The normalized difference between two higher-order frequency vectors is

$$
d_h(X,Y)=\frac{\lVert H_h(X)-H_h(Y)\rVert_1}{2T_h},\qquad T_h>0.
$$

The constructive objective is to realize a prescribed collection of higher-order targets subject to the system's resource and statistical constraints. This leads to three connected tasks:

1. **Generate variation:** transform higher-order patterns while retaining the required low-order counts.
2. **Construct targets:** introduce selected higher-order patterns through directed induction and residual compensation.
3. **Determine feasibility:** evaluate which target patterns are realizable with finite resources and reachable through the available transformations.

## Directed Construction: Induce, Compensate, Commit

The main construction procedure organizes structural control into a sequence of verifiable operations.

```text
Feasible reference system
          |
          v
Select a target higher-order pattern
          |
          v
Induce the target through legal exchanges
          |
          v
Provisionally freeze supporting records
          |
          v
Subtract frozen contributions from residual budgets
          |
          v
Refit the remaining records through compensating exchanges
          |
          v
Verify global low-order constraints and target counts
          |
          v
Commit the construction and continue to the next target
```

This procedure preserves previously accepted structures through complete-record freezing. Residual targets account for the contributions of those records, enabling the remaining system to satisfy the global statistical objective.

### A Reproduced Construction

The four-record reference system is

$$
X_A=
\bigl\{
\{1,2,3\},
\{1,4,5\},
\{2,4,6\},
\{3,5,6\}
\bigr\}.
$$

The target is to realize both \(\{1,2,4\}\) and \(\{4,5,6\}\), while preserving the original pairwise occurrence counts. The construction produces

$$
X_B=
\bigl\{
\{1,2,4\},
\{1,3,5\},
\{2,3,6\},
\{4,5,6\}
\bigr\}.
$$

| Stage | Low-order loss | Construction state |
| --- | ---: | --- |
| Reference | **0** | Original pair-count targets satisfied |
| Target induction | **4** | Target **{1,2,4}** introduced; supporting record provisionally frozen |
| Residual compensation | **0** | Pair-count residuals canceled; **{4,5,6}** realized |
| Acceptance | **0** | Both target triples present and all original low-order counts restored |

The automated constructor independently reaches an accepted configuration in one induction attempt, exploring 15 states during residual refitting. The fixed paper witness and the general constructor provide complementary verification paths.

**Run the construction:**

```bash
python -m examples.ex03_directed_freeze
```

**Use the construction API:**

```python
from hocomb import Goal, System, construct_directed

reference = System.create(
    [(1, 2, 3), (1, 4, 5), (2, 4, 6), (3, 5, 6)],
    universe=range(1, 7),
)

goals = [
    Goal(frozenset({1, 2, 4})),
    Goal(frozenset({4, 5, 6})),
]

result = construct_directed(reference, goals, mode="exact")

assert result.status == "SUCCESS"
assert reference.equivalent_low_order(result.final)
assert all(goal.holds(result.final) for goal in goals)

print("Constructed records:", result.final.readable())
print("Induction attempts:", result.attempted_inductions)
print("Committed goals:", len(result.committed))
```

## Construction Diversity through Zero-Sum Trades

A second constructive mechanism combines two exchanges whose low-order count increments cancel. The resulting operation preserves element quotas, record sizes, pair counts, and singleton counts, while changing the third-order configuration.

For the reference and constructed systems above,

$$
H_2(X_A)=H_2(X_B),\qquad
\lVert H_3(X_A)-H_3(X_B)\rVert_1=8,
$$

with \(T_3=4\), giving

$$
\boxed{d_3(X_A,X_B)=1}.
$$

The matched-trade enumerator identifies **9 distinct nontrivial output states** for this small reference system. This demonstrates constructive diversity within a fixed low-order statistical equivalence class.

```bash
python -m examples.ex02_zero_sum
```

## Realizability and Reachability

Constructive search is paired with finite feasibility analysis:

- **Support-graph screening** identifies candidate higher-order patterns.
- **Integer block-type multiplicity search** evaluates finite-resource realizability and maximum target counts.
- **State-space exploration** compares reachability under individual 2-switches and composite zero-sum trades.

In the resource-constrained example, \(\{a,b,c\}\) forms a triangle in the association support graph, while required edge coverage, quotas, and record-size counts yield \(U(\{a,b,c\})=0\). Relaxing the coverage requirement in a companion experiment gives \(U(\{a,b,c\})=1\).

For the four-record construction, the destination is reached in **two elementary switches** or **one composite zero-sum transition** consisting of the two compensating switches. The composite operation maintains low-order equality between its committed endpoint states.

```bash
python -m examples.ex04_resource_conflict
python -m examples.ex05_reachability
```

## Installation and Reproduction

**Python 3.10+**. The algorithms and tests use the Python standard library.

```bash
git clone https://github.com/antu939/Higher-OrderCombinatorial-Structures-under-Low-Order-StatisticalConstraints.git
cd Higher-OrderCombinatorial-Structures-under-Low-Order-StatisticalConstraints

python -m pip install -e .
python -m unittest discover -s tests -v
python -m examples.run_all --output results-reproduced
```

Run any experiment individually:

```bash
python -m examples.ex01_cross_stratum
python -m examples.ex02_zero_sum
python -m examples.ex03_directed_freeze
python -m examples.ex04_resource_conflict
python -m examples.ex05_reachability
python -m examples.ex06_seeded_fitting
```

The batch runner exports six JSON reports, a results manifest, and `ex06_loss_trajectory.csv`, recording the fitting trajectory. The accompanying suite includes **26 automated tests** covering count invariants, exact local updates, residual identities, realizability, directed construction, and deterministic fitting.

## Repository Layout

```text
├── paper/            # Manuscript and LaTeX sources
├── src/hocomb/       # Core mathematical models and construction algorithms
│   ├── core.py
│   ├── switches.py
│   ├── baseline.py
│   ├── directed.py
│   ├── feasibility.py
│   └── reachability.py
├── examples/         # Six runnable experiments
├── results/          # Reproducible JSON and CSV outputs
├── tests/            # Automated verification
├── docs/             # Mathematical and implementation mapping
├── pyproject.toml    # Python package configuration
├── CITATION.cff      # Citation metadata
└── LICENSE           # Software license
```

## Experiment Map

| Script | Manuscript focus | Main constructive result |
| --- | --- | --- |
| [`ex01_cross_stratum.py`](examples/ex01_cross_stratum.py) | §3: Cross-stratum exchanges | Exact local objective improvement, **4 → 0** |
| [`ex02_zero_sum.py`](examples/ex02_zero_sum.py) | §4: Structural variation | Higher-order separation at fixed pair counts, **d₃ = 1** |
| [`ex03_directed_freeze.py`](examples/ex03_directed_freeze.py) | §5: Directed construction | **Two target triples constructed**, final **E = 0** |
| [`ex04_resource_conflict.py`](examples/ex04_resource_conflict.py) | §6: Realizability | Finite-resource maximum **U({a,b,c}) = 0** |
| [`ex05_reachability.py`](examples/ex05_reachability.py) | §6: Operation reachability | **Two switches / one compound trade** |
| [`ex06_seeded_fitting.py`](examples/ex06_seeded_fitting.py) | §3: Extended fitting benchmark | **E = 16 → 0** in **37 iterations** |

Experiments 01–05 follow the manuscript's constructive examples. Experiment 06 adds a seeded mixed-size fitting benchmark.

## Paper and Citation

- [English manuscript source](paper/main-en.tex)
- [Equation-to-code correspondence](docs/experiment-mapping.md)
- [Algorithm and implementation notes](docs/implementation-notes.md)
- [Citation metadata](CITATION.cff)
- [License](LICENSE)

The paper develops the mathematical framework behind the transformations, directed construction procedure, residual equivalence, and finite realizability model. The repository provides executable construction certificates and numerical outputs for the corresponding examples.
