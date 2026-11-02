"""Characterisation tests: numeric outputs must match those captured from the
original (pre-refactor) code. Golden files live in tests/golden/ and were
generated from commit ce98f7a."""
from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path

import pytest

from ethanol_design import ddgs as DG
from ethanol_design import dehydration as DH
from ethanol_design import distillation as D
from ethanol_design import feedstock as F
from ethanol_design import fermentation as FM
from ethanol_design import properties as P
from ethanol_design import starch_hydrolysis as SH
from ethanol_design import stillage as ST

ROOT = Path(__file__).resolve().parent.parent
GOLDEN = ROOT / "tests" / "golden"


def _d(x):
    return asdict(x) if is_dataclass(x) else x


def _assert_same(actual, expected, path=""):
    if isinstance(expected, dict):
        assert set(actual) == set(expected), path
        for k in expected:
            _assert_same(actual[k], expected[k], f"{path}/{k}")
    elif isinstance(expected, list):
        assert len(actual) == len(expected), path
        for i, (a, e) in enumerate(zip(actual, expected)):
            _assert_same(a, e, f"{path}[{i}]")
    elif isinstance(expected, float):
        assert actual == pytest.approx(expected, rel=1e-6), path
    else:
        assert actual == expected, path


def _current_outputs():
    out = {}
    az = P.find_azeotrope()
    out["azeotrope"] = _d(az)
    out["bubble"] = _d(P.bubble_point(0.5))
    out["conv"] = [P.mole_frac_to_mass_frac_ethanol(0.3), P.mass_frac_to_mole_frac_ethanol(0.3)]
    feeds = {"cane": F.cane_juice_feedstock(11.57), "b": F.b_heavy_molasses_feedstock(11.57),
             "c": F.c_heavy_molasses_feedstock(11.57), "rice": SH.milled_rice(5.79),
             "broken": SH.broken_rice(5.79), "maize": SH.maize(5.79)}
    for k, f in feeds.items():
        out["feed_" + k] = _d(f)
        out["ferm_" + k] = _d(FM.ferment(f, f.mass_flow_kg_s * 3.0))
    out["fsize"] = _d(FM.fermenter_sizing(feeds["b"], 30.0, 36.0))
    out["col"] = _d(D.design_column(0.08, 0.93, 0.0005))
    out["bed"] = _d(DH.size_dehydration_bed(1.0, 0.07))
    out["ddgs"] = _d(DG.characterize_ddgs(5.79, 0.75, 0.95, 2.0))
    out["still"] = _d(ST.characterize_stillage(10.0, 80.0))
    out["fsize_f"] = out["fsize"]
    return json.loads(json.dumps(out, default=repr))


def test_module_outputs_match_original_golden():
    expected = json.loads((GOLDEN / "module_outputs.json").read_text())
    _assert_same(_current_outputs(), expected)


@pytest.mark.parametrize("name", ["full_chain_worked_example", "grain_worked_example"])
def test_worked_example_stdout_is_identical(name):
    proc = subprocess.run([sys.executable, str(ROOT / "examples" / f"{name}.py")],
                          capture_output=True, text=True, check=True, cwd=ROOT)
    assert proc.stdout == (GOLDEN / f"{name}.txt").read_text()
