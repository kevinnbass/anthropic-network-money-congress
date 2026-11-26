#!/usr/bin/env python3
"""Alternative version of figure 10 (lobbyists' own contributions), rendered to figures-alt/ so the pack's registered
figures are untouched. Every gift drawn is a counted type-4b item of research/members_network.csv, so it is dated inside
a window in which the lobbyist's firm was registered for a network client (research/lb_network_windows.csv); gifts
outside a window are context in the join and are not here. Top panel: one row per lobbying firm, one cell per election
cycle, each cell a stacked bar of the firm's lobbyists' gifts to sitting Democrats and Republicans, with the year the
firm's first registration window opens. Middle panel: the same money by cycle. Bottom panel: top recipients.
2026-11-26 (audit X63): the start year came from the firm's earliest lobbying row of any kind, which for five firms was
an LD-203 report naming no client; it now comes from the windows table. The 'before first client' bucket, legend entry
and sentences are gone: no counted gift can fall before its firm's window. The 2026 share is rounded, not floored.
usage: python3 scripts/alt_fig10.py"""
from __future__ import annotations

import collections
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_figures as bf  # noqa: E402
import build_figures2 as b  # noqa: E402
from casework.figures.common import legend, money  # noqa: E402

bf.OUT = bf.ROOT / "figures-alt"
DEM, REP, IND, MUTED, INK, txt = b.DEM, b.REP, b.IND, b.MUTED, b.INK, b.txt


def window_starts() -> tuple[dict[str, str], dict[str, str]]:
    """Year each registrant's first qualifying registration window opens, by LDA registrant id and by registrant name."""
    by_id: dict[str, str] = {}
    by_name: dict[str, str] = {}
    with open(bf.ROOT / "research/lb_network_windows.csv", encoding="utf-8") as fh:
        for w in csv.DictReader(line for line in fh if not line.startswith("#")):
            if w["status"] != "window":
                continue
            y = w["window_start"][:4]
            by_id[w["registrant_id"]] = min(by_id.get(w["registrant_id"], y), y)
            name = w["registrant_name"].upper()
            by_name[name] = min(by_name.get(name, y), y)
    return by_id, by_name


def main() -> int:
    win_id, win_name = window_starts()
    rows = []
    for m in b.SITTING:
        for rid in m["t4b_ids"].split():
            r = b.BY_ID.get(rid)
            if r and (r.get("money_type") or "") == "hard_money":
                rows.append((m, r))
    ids = [r["row_id"] for _, r in rows]
    cell = collections.defaultdict(float); tot = collections.Counter(); by_cycle = collections.defaultdict(float); by_member = collections.Counter()
    reg_ids = collections.defaultdict(set)
    for m, r in rows:
        p = (m["party"] or "?")[:1].upper(); p = p if p in ("D", "R") else "I"
        f = b.registrant_of(r["note"]); c = r["cycle"] or b.cycle_of(r["date"])
        v = b.amt(r["amount_usd"])
        cell[(f, c, p)] += v; tot[f] += v; by_cycle[(c, p)] += v; by_member[m["row_id"]] += v
        i = re.search(r"(?:lda_registrant_id=|registrant=[^;]+ id=)(\d+)", r["note"] or "")  # the join's own reading of the registrant id
        if i:
            reg_ids[f].add(i.group(1))

    def start(f: str) -> str | None:
        c = [win_id[i] for i in reg_ids[f] if i in win_id] or [v for k, v in win_name.items() if k == f.upper()]
        return min(c) if c else None

    cycles = [c for c in sorted({c for (_, c, _) in cell}) if c and c >= "2008"]
    firms = [f for f, _ in tot.most_common(12)]
    cyc_tot = {c: sum(by_cycle[(c, p)] for p in ("D", "R", "I")) for c in cycles}
    total = sum(tot.values()); last = cycles[-1]
    assert all(cyc_tot[x] < cyc_tot[y] for x, y in zip(cycles, cycles[1:])), "the title says the money rose each cycle shown"
    assert abs(sum(cyc_tot.values()) - total) < 0.005, "a counted gift falls in a cycle that is not drawn"
    share_r = 100 * by_cycle[(last, "R")] / cyc_tot[last]
    assert share_r > 50, "the title says the last cycle tilts Republican"
    assert last == "2026", "the footnote says the last cycle shown is still open"

    svg = [txt(40, 40, "Each firm's lobbyists' own gifts to sitting members while the firm was registered for a network client, by election cycle", 22, weight="bold")]
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
            for p, col in (("D", DEM), ("R", REP), ("I", IND)):
                v = cell[(f, c, p)]
                if v:
                    h = (rh - 16) * v / cmax
                    svg.append(f'<rect x="{cx:.1f}" y="{hy - h:.1f}" width="44" height="{max(h, 1.2):.1f}" fill="{col}"/>')
                    hy -= h
            v = cell[(f, c, "D")] + cell[(f, c, "R")] + cell[(f, c, "I")]
            if v >= 20000:
                svg.append(txt(cx + 50, base - 4, money(v), 11, fill=INK))
        svg.append(txt(x0 + lw + len(cycles) * cw + 16, y + 54, money(tot[f]), 17, weight="bold"))

    py = y0 + len(firms) * rh + 90
    svg.append(txt(40, py, "All firms by cycle", 22, weight="bold"))
    mx = max(list(cyc_tot.values()) + [1])
    for j, c in enumerate(cycles):
        x = x0 + lw + j * cw + cw / 2 - 30; base = py + 330; hy = base
        for p, col in (("D", DEM), ("R", REP), ("I", IND)):
            v = by_cycle[(c, p)]
            if v:
                h = 280 * v / mx
                svg.append(f'<rect x="{x:.1f}" y="{hy - h:.1f}" width="60" height="{h:.1f}" fill="{col}"/>')
                hy -= h
        svg.append(txt(x + 30, hy - 10, money(cyc_tot[c]), 13, anchor="middle", weight="bold"))
        svg.append(txt(x + 30, base + 22, c, 15, anchor="middle", fill=MUTED))

    ry = py + 400
    svg.append(txt(40, ry, "Sitting members receiving the most (gifts to committees the FEC record ties to one member; all years)", 22, weight="bold"))
    mb_by = {m["row_id"]: m for m in b.SITTING}
    top = by_member.most_common(16)
    svg.append(b.bar_chart([(b.member_label(mb_by[k]["member_bioguide"]), v, mb_by[k]) for k, v in top], 40, ry + 20, 2000, 520, label_w=520, colour=lambda m: b.party_colour(m["party"])))
    ids += [k for k, _ in top]

    has_ind = any(by_cycle[(c, "I")] for c in cycles)
    subtitle = (f"What this is: gifts that registered lobbyists made from their own money, reported to Congress, for lobbyists at firms that have lobbied for a network client. "
                f"Only gifts dated while the lobbyist's firm was registered for a network client are counted: {money(total)} in all, more in each cycle shown, "
                f"reaching {money(cyc_tot[last])} in {last} so far, {share_r:.0f}% of it to Republicans.")
    footnote = ("<b>What the record does not show.</b> The client did not direct a lobbyist's personal gift, and these lobbyists serve many clients outside the network. "
                "A contribution is not a vote. A firm's start year is the year its first counted registration for a network client begins; "
                "gifts dated outside a firm's registration are not counted and are not drawn. "
                f"{last} is still open.")
    bf.figure("congress-10-lobbyists-own-contributions-alt", f"Lobbyists' counted gifts rose across the displayed cycles; {last} tilts Republican",
              subtitle, "\n".join(svg), footnote, ids, height=ry + 20 + 560 + 470,
              legend_html=legend([(DEM, "to Democrats"), (REP, "to Republicans")] + ([(IND, "to independents")] if has_ind else [])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
