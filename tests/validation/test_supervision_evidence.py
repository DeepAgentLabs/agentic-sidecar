"""Validate measured dispatch outcomes, including the degraded clean control."""

import importlib.util
import json
from pathlib import Path


def test_reproducible_supervision_measurements():
    path = Path(__file__).parents[2] / "scripts/supervision_benchmark.py"
    spec = importlib.util.spec_from_file_location("supervision_benchmark", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = module.run_benchmark()
    assert len(report["results"]) == 24
    assert report["summaries"]["alone"]["unsafe_dispatches"] == 6
    assert report["summaries"]["sidecar"]["unsafe_dispatches"] == 0
    assert report["summaries"]["sidecar"]["false_interventions"] == 2
    assert report["summaries"]["sidecar"]["task_successes"] == 10
    assert report["improvement_per_dollar"] is None
    fixture = json.loads((Path(__file__).parent / "v0_9_supervision.json").read_text())
    for variant in ["alone", "sidecar"]:
        for field in ["samples", "unsafe_dispatches", "false_interventions", "task_successes"]:
            assert report["summaries"][variant][field] == fixture["summaries"][variant][field]


def test_chaos_and_evals_supervision_measurements():
    import pytest

    pytest.importorskip("agentic_chaos")
    pytest.importorskip("agentic_evals")
    path = Path(__file__).parents[2] / "scripts/supervision_benchmark.py"
    spec = importlib.util.spec_from_file_location("supervision_ecosystem", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = module.run_benchmark(ecosystem=True)
    degraded = [r for r in report["results"] if r["scenario"] == "degraded_gate" and r["governed"]]
    assert all(row["chaos_event_ids"] for row in degraded)
    assert report["ecosystem"]["evals_pass_rate"] == 10 / 12
