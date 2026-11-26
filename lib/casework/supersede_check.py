"""Flag rows a review marked superseded that still count beside their replacement (Kevin, 2026-10-11: "flag them only").

`casework promote` writes "superseded by <new>" into the old row's note and leaves the old row's bindings as they were. When
the old and the new row are both bound as evidence on the same element, a join or figure that counts evidence rows counts the
fact twice, unless the two rows are in fact different facts (audit X49 in the congress pack found 12 of 44 such links wrong).
This check only reports; it never changes a row or a binding. A pack records a pair it has settled as two distinct facts in
`research/supersede_reviewed.csv` (columns old_row,new_row,finding_id,basis); a pair settled as one fact is settled by
moving the copy to context, after which it no longer appears here.

usage: python3 -m casework.supersede_check --pack <name> [--strict]   (exit 1 with --strict when any pair is open)
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
from pathlib import Path

REGISTRY = Path(__file__).resolve().parents[1] / "packs.json"
SUPERSEDED = re.compile(r"\bsuperseded by\s+([A-Z]{1,4}\d{2,6})\b")


def _rows(path: Path) -> list[dict[str, str]]:
    csv.field_size_limit(sys.maxsize)
    with path.open(encoding="utf-8-sig", errors="replace", newline="") as stream:
        return list(csv.DictReader(io.StringIO("".join(line for line in stream if not line.startswith("#")))))


def open_pairs(root: Path) -> tuple[list[dict[str, str]], int]:
    config = json.loads((root / "casework.json").read_text(encoding="utf-8"))
    case = json.loads((root / "case.json").read_text(encoding="utf-8"))
    evidence: dict[str, set[str]] = {}
    for claim in case.get("claims", []):
        for element in claim.get("elements", []):
            for binding in element.get("bindings", []):
                if binding.get("role", "evidence") == "evidence":
                    evidence.setdefault(binding["row_id"], set()).add(element["element_id"])
    notes: dict[str, str] = {}
    for table in config.get("tables", {}).values():
        path = root / table.get("file", "")
        if table.get("file") and path.is_file():
            for row in _rows(path):
                notes[row.get("row_id", "")] = row.get("note", "") or ""
    reviewed_path = root / "research" / "supersede_reviewed.csv"
    reviewed = {(r["old_row"], r["new_row"]) for r in _rows(reviewed_path)} if reviewed_path.is_file() else set()
    found, settled = [], 0
    for old, note in notes.items():
        for new in sorted(set(SUPERSEDED.findall(note))):
            shared = sorted(evidence.get(old, set()) & evidence.get(new, set()))
            if not shared:
                continue
            if (old, new) in reviewed:
                settled += 1
                continue
            found.append({"old_row": old, "new_row": new, "elements": ";".join(shared)})
    return found, settled


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="casework.supersede_check", description=__doc__.split("\n\n")[0])
    parser.add_argument("--pack", required=True)
    parser.add_argument("--strict", action="store_true", help="exit 1 when any pair is open")
    args = parser.parse_args(argv)
    packs = json.loads(REGISTRY.read_text(encoding="utf-8"))
    if args.pack not in packs:
        parser.error(f"unknown pack: {args.pack}")
    root = Path(packs[args.pack]["root"])
    found, settled = open_pairs(root)
    for pair in found:
        print(f"SUPERSEDED-STILL-COUNTED {pair['old_row']} -> {pair['new_row']} on {pair['elements']}")
    print(f"supersede-check {args.pack}: open={len(found)} settled_distinct={settled}")
    return 1 if (args.strict and found) else 0


if __name__ == "__main__":
    sys.exit(main())
