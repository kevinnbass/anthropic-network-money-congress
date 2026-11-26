#!/usr/bin/env python3
"""Alternative version of figure 10 (lobbyists' own contributions), rendered to figures-alt/ so the pack's 25 registered
figures are untouched. Top panel: one row per lobbying firm, one cell per election cycle, each cell a stacked bar of
the firm's lobbyists' gifts to sitting Democrats and Republicans; cells before the firm first lobbied for a network
client (its earliest evidence LD-1/LD-2 in research/lobbying.csv) are faded. Middle panel: the same money by cycle,
split into before and after the firm's engagement. Bottom panel: top recipients, as in the original.
usage: python3 scripts/alt_fig10.py"""
from __future__ import annotations

import collections
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_figures as bf  # noqa: E402
import build_figures2 as b  # noqa: E402
from casework.figures.common import legend, money  # noqa: E402

bf.OUT = bf.ROOT / "figures-alt"
DEM, REP, IND, MUTED, INK, txt = b.DEM, b.REP, b.IND, b.MUTED, b.INK, b.txt
FADE = 0.28


def first_engagement() -> dict[str, str]:
    first: dict[str, str] = {}
    for r in b.LB:
        if not b.ev(r):
            continue
        reg, y = (r.get("registrant") or "").upper(), (r.get("date") or "")[:4]
        if reg and y.isdigit():
            first[reg] = min(first.get(reg, "9999"), y)
    return first


def main() -> int:
    first = first_engagement()

    def start(f: str) -> str | None:
        c = [v for k, v in first.items() if f[:18].upper() in k or k[:18] in f.upper()]
        return min(c) if c else None

    rows = []
    for m in b.SITTING:
        for rid in m["t4b_ids"].split():
            r = b.BY_ID.get(rid)
            if r and (r.get("money_type") or "") == "hard_money":
                rows.append((m, r))
    ids = [r["row_id"] for _, r in rows]
    cell = collections.defaultdict(float); tot = collections.Counter(); by_cycle = collections.defaultdict(float); by_member = collections.Counter()
    for m, r in rows:
        p = (m["party"] or "?")[:1].upper(); p = p if p in ("D", "R") else "I"
        f = b.registrant_of(r["note"]); c = r["cycle"] or b.cycle_of(r["date"]); y = (r["date"] or c)[:4]
        s = start(f); phase = "after" if (s and y >= s) else "before"
        v = b.amt(r["amount_usd"])
        cell[(f, c, p)] += v; tot[f] += v; by_cycle[(c, phase, p)] += v; by_member[m["row_id"]] += v
    cycles = [c for c in sorted({c for (_, c, _) in cell}) if c and c >= "2008"]
    firms = [f for f, _ in tot.most_common(12)]
    early = sum(v for (c, ph, p), v in by_cycle.items() if ph == "before"); late = sum(v for (c, ph, p), v in by_cycle.items() if ph == "after")
    late26 = sum(v for (c, ph, p), v in by_cycle.items() if ph == "after" and c == "2026")
    late26r = by_cycle.get(("2026", "after", "R"), 0.0)

    svg = [txt(40, 40, "Each firm's lobbyists' own gifts to sitting members, by election cycle (blue to Democrats, red to Republicans; faded = before the firm lobbied for a network client)", 22, weight="bold")]
    x0, y0, lw, cw, rh = 40, 110, 560, 128, 96
    cmax = max([cell[(f, c, "D")] + cell[(f, c, "R")] + cell[(f, c, "I")] for f in firms for c in cycles] + [1])
    for j, c in enumerate(cycles):
        svg.append(txt(x0 + lw + j * cw + cw / 2, y0 - 14, c, 15, anchor="middle", fill=MUTED))
    svg.append(txt(x0 + lw + len(cycles) * cw + 16, y0 - 14, "all years", 15, fill=MUTED))
    for i, f in enumerate(firms):
        y = y0 + i * rh
        if i % 2 == 0:
            svg.append(f'<rect x="{x0}" y="{y}" width="{lw + len(cycles) * cw + 180}" height="{rh}" fill="#efece4"/>')
        s = start(f)
        name = re.sub(r"\s*\(FORMERLY[^)]*\)?", "", f.upper())
        name = re.sub(r",?\s*(LLC|LLP|INC\.?)\s*$", "", name).strip(" ,").title().replace("Llp", "LLP")
        svg.append(txt(x0 + 8, y + 40, name[:42], 17, weight="bold"))
        svg.append(txt(x0 + 8, y + 64, f"network client from {s}" if s else "network client year not found", 14, fill=MUTED))
        for j, c in enumerate(cycles):
            cx = x0 + lw + j * cw + cw / 2 - 22; base = y + rh - 8; hy = base
            op = 1.0 if (s and int(c) >= int(s)) else FADE  # a cycle is solid once it ends at or after the firm's first network-client year
            for p, col in (("D", DEM), ("R", REP), ("I", IND)):
                v = cell[(f, c, p)]
                if v:
                    h = (rh - 16) * v / cmax
                    svg.append(f'<rect x="{cx:.1f}" y="{hy - h:.1f}" width="44" height="{max(h, 1.2):.1f}" fill="{col}" opacity="{op}"/>')
                    hy -= h
            v = cell[(f, c, "D")] + cell[(f, c, "R")] + cell[(f, c, "I")]
            if v >= 20000:
                svg.append(txt(cx + 50, base - 4, money(v), 11, fill=MUTED if op < 1 else INK))
        svg.append(txt(x0 + lw + len(cycles) * cw + 16, y + 54, money(tot[f]), 17, weight="bold"))

    py = y0 + len(firms) * rh + 90
    svg.append(txt(40, py, "All firms by cycle: gifts after each firm took on a network client (solid) and before (faded)", 22, weight="bold"))
    mx = max([sum(by_cycle[(c, ph, p)] for ph in ("before", "after") for p in ("D", "R", "I")) for c in cycles] + [1])
    for j, c in enumerate(cycles):
        x = x0 + lw + j * cw + cw / 2 - 30; base = py + 330; hy = base
        for ph, op in (("after", 1.0), ("before", FADE)):
            for p, col in (("D", DEM), ("R", REP), ("I", IND)):
                v = by_cycle[(c, ph, p)]
                if v:
                    h = 280 * v / mx
                    svg.append(f'<rect x="{x:.1f}" y="{hy - h:.1f}" width="60" height="{h:.1f}" fill="{col}" opacity="{op}"/>')
                    hy -= h
        t = sum(by_cycle[(c, ph, p)] for ph in ("before", "after") for p in ("D", "R", "I"))
        a = sum(by_cycle[(c, "after", p)] for p in ("D", "R", "I"))
        svg.append(txt(x + 30, hy - 26, money(t), 13, anchor="middle", weight="bold"))
        svg.append(txt(x + 30, hy - 10, f"{money(a)} after", 11, anchor="middle", fill=MUTED))
        svg.append(txt(x + 30, base + 22, c, 15, anchor="middle", fill=MUTED))

    ry = py + 400
    svg.append(txt(40, ry, "Sitting members receiving the most (their own committees, and committees a filing names as honouring them; all years)", 22, weight="bold"))
    mb_by = {m["row_id"]: m for m in b.SITTING}
    top = by_member.most_common(16)
    svg.append(b.bar_chart([(b.member_label(mb_by[k]["member_bioguide"]), v, mb_by[k]) for k, v in top], 40, ry + 20, 2000, 520, label_w=520, colour=lambda m: b.party_colour(m["party"])))
    ids += [k for k, _ in top]

    subtitle = (f"What this is: gifts that registered lobbyists made from their own money, reported to Congress, for lobbyists at firms that have lobbied for a network client. "
                f"{money(early)} of the {money(early + late)} was given before the lobbyist's firm took on its first network client; since then the money has risen each cycle, "
                f"to {money(late26)} in 2026 so far, {100 * late26r // max(1, late26):.0f}% of it to Republicans.")
    footnote = ("<b>What the record does not show.</b> The client did not direct a lobbyist's personal gift, and these lobbyists serve many clients outside the network. "
                "A contribution is not a vote. A firm's start year is its earliest lobbying report for a network client in this study; gifts before it are shown faded, not removed. "
                "2026 is still open.")
    bf.figure("congress-10-lobbyists-own-contributions-alt", "Lobbyists' gifts climbed as more firms took on network clients; 2026 tilts Republican",
              subtitle, "\n".join(svg), footnote, ids, height=ry + 20 + 560 + 470,
              legend_html=legend([(DEM, "to Democrats"), (REP, "to Republicans"), ("#c9c4b8", "faded: before the firm's first network client")]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
