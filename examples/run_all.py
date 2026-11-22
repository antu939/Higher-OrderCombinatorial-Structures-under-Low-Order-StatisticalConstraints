"""Batch reproduction with per-case JSON and seeded fit CSV artifact."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from . import (
    ex01_cross_stratum, ex02_zero_sum, ex03_directed_freeze,
    ex04_resource_conflict, ex05_reachability, ex06_seeded_fitting,
)


def main() -> None:
    p = argparse.ArgumentParser(description="Reproduce paper-linked experiments")
    p.add_argument("--output", default="results", help="Directory for JSON and CSV")
    args = p.parse_args()
    folder = Path(args.output)
    folder.mkdir(parents=True, exist_ok=True)
    cases = [
        ex01_cross_stratum, ex02_zero_sum, ex03_directed_freeze,
        ex04_resource_conflict, ex05_reachability, ex06_seeded_fitting,
    ]
    manifest = []
    for case in cases:
        result = case.run()
        output = folder / (case.__name__.split(".")[-1] + ".json")
        output.write_text(
            json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        manifest.append({"experiment": case.__name__.split(".")[-1],
                         "artifact": output.name, "paper": result["paper"]})
        print(f"[PASS] {output.name}")
    fit_report, rows = ex06_seeded_fitting.run_with_trace()
    csv_path = folder / "ex06_loss_trajectory.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "iteration", "accepted", "proposal", "delta",
            "current_loss", "best_loss",
        ])
        writer.writeheader()
        writer.writerows(rows)
    (folder / "manifest.json").write_text(
        json.dumps({"experiments": manifest, "fitting_seed": 2026},
                   ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"[PASS] {csv_path.name}")
    print(f"Reproduced {len(cases)} experiments in {folder.resolve()}")


if __name__ == "__main__":
    main()
