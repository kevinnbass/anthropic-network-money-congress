#!/usr/bin/env python3
"""Registered figures 26-29 (2026-09-29): committee testimony, shared officers, state AI-bill lobbying and the federal AI lobbying
baseline. Each is built by its figures-alt script in FINAL mode, which writes the registered stem into figures/.
usage: python3 scripts/build_figures3.py [stem ...]"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_figures as bf  # noqa: E402

ALL = {"congress-26-committee-testimony": "alt_testimony", "congress-27-shared-officers": "alt_interlocks",
       "congress-28-state-ai-bill-lobbying": "alt_state_ai_bills", "congress-29-federal-ai-lobbying-baseline": "alt_lda_baseline"}


def build(stem: str) -> None:
    mod = importlib.import_module(ALL[stem])
    mod.FINAL = True
    mod.bf.OUT = bf.ROOT / "figures"
    mod.main()


if __name__ == "__main__":
    for stem in sys.argv[1:] or [s for s in ALL if (Path(__file__).resolve().parent / f"{ALL[s]}.py").exists()]:
        build(stem)
