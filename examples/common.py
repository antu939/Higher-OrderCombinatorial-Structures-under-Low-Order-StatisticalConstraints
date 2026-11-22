"""Shared, JSON-safe formatting for the experiments."""
from __future__ import annotations

import json
from . import __doc__ as _package_doc  # Keep examples a proper package.


def format_pair_counts(x) -> dict[str, int]:
    return {",".join(map(str, p)): x.pair_counts()[p]
            for p in sorted(x.pair_counts(), key=lambda p: tuple(map(str, p)))}


def format_singletons(x) -> dict[str, int]:
    return {str(e): x.singleton_counts()[e] for e in x.universe}


def print_result(data: dict) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))
