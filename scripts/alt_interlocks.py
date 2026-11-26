#!/usr/bin/env python3
"""Draft (figures-alt): people holding officer, director or key-employee roles at two or more network organisations,
by the organisations' own IRS returns (lane C161, review R161, audit X27; research/interlocks.csv), and network officers
with documented government careers. An analysis file, not a promoted table, so this stays a draft.
usage: python3 scripts/alt_interlocks.py"""
from __future__ import annotations

import collections
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_figures as bf  # noqa: E402
import build_figures2 as b  # noqa: E402
from casework.figures.common import legend  # noqa: E402

bf.OUT = bf.ROOT / "figures-alt"
FINAL = False  # 2026-09-29: build_figures3.py sets True to render the registered figure into figures/
SRC = bf.ROOT / "research/interlocks.csv"
LANE = bf.ROOT / "research/grok-out/C161-network-interlocks.csv"
CROSS, FAMILY = "#7a5195", "#b0a58f"
ORG_ORDER = [("COEFFICIENT GIVING ACTION", "Coefficient Giving Action Fund"), ("COEFFICIENT", "Coefficient Giving"), ("GOOD VENTURES", "Good Ventures"),
             ("OPERATING", "Schmidt Operating Foundation"), ("SCHMIDT", "Schmidt Fund"), ("BEMC 4", "BEMC 4 Association"), ("BEMC", "BEMC Foundation"),
             ("ARC", "ARC"), ("ALIGNMENT RESEARCH", "ARC"), ("METR", "METR"), ("MODEL EVALUATION", "METR"), ("REDWOOD", "Redwood Research"), ("FAR", "FAR AI"),
             ("GOVAI", "GovAI"), ("GOVERNANCE OF AI", "GovAI"), ("HORIZON", "Horizon Institute"), ("FAS", "FAS"), ("FEDERATION OF AMERICAN", "FAS"),
             ("IFP", "IFP"), ("INSTITUTE FOR PROGRESS", "IFP"), ("FAI", "FAI"), ("AMERICAN INNOVATION", "FAI")]
FAMILIES = [{"Coefficient Giving Action Fund", "Coefficient Giving", "Good Ventures"}, {"Schmidt Operating Foundation", "Schmidt Fund"},
            {"BEMC 4 Association", "BEMC Foundation"}]


def org_label(s: str) -> str:
    u = (s or "").upper()
    for k, v in ORG_ORDER:
        if k in u:
            return v
    return s.strip()[:28]


def person_case(n: str) -> str:
    """Title case that keeps Mc and Mac names (X40-2989: James McClave, not Mcclave)."""
    return re.sub(r"\b(Ma?c)([a-z])", lambda m: m.group(1) + m.group(2).upper(), (n or "").title())


def main() -> int:
    stem = "congress-27-shared-officers"
    if not FINAL:
        stem = "network-interlocks-draft"
    rows = [r for r in csv.DictReader(l for l in open(SRC, encoding="utf-8") if not l.startswith("#"))]
    lane = list(csv.DictReader(l for l in open(LANE, encoding="utf-8") if not l.startswith("#")))
    roles = collections.defaultdict(lambda: collections.defaultdict(set))
    ids_cited = sorted({r["entity_id"] for r in rows if (r.get("entity_id") or "").startswith("EN")})
    for r in rows:
        if r["task"] == "S1" and r["tax_year"][:4].isdigit():
            roles[person_case(r["person"])][org_label(r["organisation"])].add(int(r["tax_year"][:4]))
    def cross(p):
        orgs = set(roles[p])
        return not any(orgs <= f for f in FAMILIES)
    people = sorted(roles, key=lambda p: (not cross(p), -len(roles[p]), p))
    yrs = sorted({y for p in people for o in roles[p] for y in roles[p][o]}) or [0]  # X40-2990: the subtitle states the years drawn
    seen = []
    for _, v in ORG_ORDER:
        if v not in seen and any(v in roles[p] for p in people):
            seen.append(v)
    orgs = seen
    x0, lw, cw, y0, rh = 40, 300, 100, 230, 40
    svg = [b.txt(40, 40, f"People holding officer, director or key-employee roles at two or more network organisations ({len(people)}), with the tax years of each role", 24, weight="bold")]
    for j, o in enumerate(orgs):
        cx = x0 + lw + j * cw + cw / 2
        svg.append(f'<text x="{cx:.1f}" y="{y0 - 14}" font-size="15" font-family="Arial" fill="{b.INK}" text-anchor="start" transform="rotate(-35 {cx:.1f} {y0 - 14})">{b.esc(o) if hasattr(b, "esc") else o}</text>')
    for i, p in enumerate(people):
        yy = y0 + i * rh
        if i % 2 == 0:
            svg.append(f'<rect x="{x0}" y="{yy}" width="{lw + len(orgs) * cw}" height="{rh}" fill="#efece4"/>')
        col = CROSS if cross(p) else FAMILY
        svg.append(b.txt(x0 + lw - 14, yy + rh * 0.66, p, 17, anchor="end", weight="bold" if cross(p) else None, fill=b.INK if cross(p) else b.MUTED))
        for j, o in enumerate(orgs):
            ys = roles[p].get(o)
            if ys:
                cx = x0 + lw + j * cw + cw / 2
                svg.append(f'<circle cx="{cx:.1f}" cy="{yy + rh / 2:.1f}" r="7" fill="{col}"/>')
                span = f"{min(ys)}" if min(ys) == max(ys) else f"{min(ys)}–{str(max(ys))[2:]}"
                svg.append(b.txt(cx + 12, yy + rh * 0.66, span, 13, fill=b.MUTED))
    gy = y0 + len(people) * rh + 80
    svg.append(b.txt(40, gy, "Officers of network organisations with documented government careers", 22, weight="bold"))
    gov = []
    for r in rows:
        if r["task"] == "S2a":
            n = lane[int(r["lane_row"]) - 1]["note"]
            m = re.search(r"government_role=([^;]*)", n)
            gov.append((person_case(r["person"]), org_label(r["organisation"]), (m.group(1) if m else "").strip()))
    seen_g = set(); k = 0
    for person, org, role in sorted(gov):
        if (person, role) in seen_g or not role:
            continue
        seen_g.add((person, role))
        yy = gy + 40 + k * 32; k += 1
        svg.append(b.txt(60, yy, person, 17, weight="bold"))
        svg.append(b.txt(380, yy, org, 17))
        svg.append(b.txt(760, yy, role[:110], 16, fill=b.MUTED))
    height = gy + 40 + k * 32 + 460
    subtitle = ("What this is: every person the organisations' own tax returns (Form 990 Part VII, 990-PF Part VIII) list as an officer, director, trustee or "
                f"key employee at two or more network organisations in {min(yrs)}–{max(yrs)} (tax years), matched as the same person on the returns' own details or the organisations' "
                "own statements. Purple rows link organisations in different families; grey rows are shared officers within one family's vehicles.")
    footnote = ("<b>What the record does not show.</b> A shared officer is a shared role, not coordination, and a board seat is not control. Four network "
                "organisations have no officer returns in the data (IAPS, Tarbell, Coefficient Giving's policy fund, Apollo Research), so their people are "
                "missing, not absent. Government careers are from official biographies and lobbying filings. " + ("" if FINAL else "Draft figure.") + "")
    bf.figure(stem, f"{sum(1 for p in people if cross(p))} people sit across separate network organisations; "
              "funder staff sit on grantees' boards", subtitle, "\n".join(svg), footnote, ids_cited,
              height=height, legend_html=legend([(CROSS, "roles in organisations of different families"), (FAMILY, "roles within one family's vehicles")]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
