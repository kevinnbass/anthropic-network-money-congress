#!/usr/bin/env python3
"""Unpack the tables stored gzipped (GitHub refuses files over 100 MB). Run once after cloning: python3 scripts/setup_data.py"""
import gzip, shutil
from pathlib import Path

for gz in sorted((Path(__file__).resolve().parents[1] / "research").glob("*.csv.gz")):
    dst = gz.with_suffix("")
    if not dst.exists():
        with gzip.open(gz, "rb") as src, open(dst, "wb") as out:
            shutil.copyfileobj(src, out)
        print("unpacked", dst.name)
    else:
        print("already there", dst.name)
