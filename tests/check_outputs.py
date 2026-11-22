"""Read exported JSON rather than trusting example success messages."""
import json
import sys
from pathlib import Path

folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("results")
def read(stem):
    return json.loads((folder / f"{stem}.json").read_text(encoding="utf-8"))

a = read("ex01_cross_stratum")
b = read("ex02_zero_sum")
c = read("ex03_directed_freeze")
d = read("ex04_resource_conflict")
e = read("ex05_reachability")
f = read("ex06_seeded_fitting")

assert [a["initial_loss"], a["final_loss"], a["predicted_local_delta"]] == [4, 0, -4]
assert [b["L1_h3"], b["T3"], b["d3"]] == [8, 4, 1]
assert [c["E_initial"], c["E_provisional"], c["E_committed"]] == [0, 4, 0]
assert [c["targets"]["124"], c["targets"]["456"]] == [1, 1]
assert d["with_required_coverage"]["U_abc"] == 0
assert d["without_required_coverage_EXTRA_CONTROL"]["U_abc"] == 1
assert e["general_switch_endpoint"]["transitions"] == 2
assert not e["every_switch_must_preserve_pair_counts"]["found"]
assert e["one_zero_sum_trade_must_preserve_pair_counts"]["transitions"] == 1
assert f["initial_loss"] == 16
assert f["best_loss"] == 0
assert (folder / "ex06_loss_trajectory.csv").is_file()
print("All paper-linked outputs independently checked.")
