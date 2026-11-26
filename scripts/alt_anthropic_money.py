#!/usr/bin/env python3
"""Anthropic-only companion to ai-machine figure 6A: sitting members ranked by money from Anthropic's employees and its
PAC (ANTHROPAC), 2024 and 2026 cycles, from the congress pack's verified hard-money rows (evidence role; individual
receipts whose filed employer is Anthropic, and ANTHROPAC's contributions; memo, conduit and redesignation lines
excluded). Covers every committee of a member: campaign, a campaign for another office, leadership PAC, joint
fundraising committee. The filed employer is read from the row's note or its quoted FEC record (audit X63).
Rendered to figures-alt/ so the pack's 25 registered figures are untouched.
usage: python3 scripts/alt_anthropic_money.py"""
from __future__ import annotations

import collections
import datetime
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_figures as bf  # noqa: E402
import build_figures2 as b  # noqa: E402
from casework.figures.common import legend, money  # noqa: E402

bf.OUT = bf.ROOT / "figures-alt"
EMP, PAC = "#2f8f9d", "#e07b39"


def main() -> int:
    sit = {m["member_bioguide"]: m for m in b.SITTING}
    emp, pac, donors, ids = collections.defaultdict(float), collections.defaultdict(float), collections.defaultdict(set), []
    for r in b.HM:
        if not b.ev(r) or r["member_bioguide"] not in sit or r["money_type"] not in ("hard_money", "corporate_pac"):
            continue
        note = r["note"] or ""
        e = re.search(r"(?:employer as filed|contributor_employer)=\s*([^;]*)", note)
        q = re.search(r'"contributor_employer":\s*"([^"]*)"', r.get("quote_300") or "")  # X63-269: a variant pull keeps the filed employer in the quoted record and in 'Employer string ...'
        is_emp = r["payer_type"] == "individual" and bool((e and "ANTHROPIC" in e.group(1).upper()) or re.search(r"Employer string ANTHROPIC", note) or (q and "ANTHROPIC" in q.group(1).upper()))
        is_pac = "ANTHROPIC PBC POLITI" in (r["payer"] or "").upper()
        if not (is_emp or is_pac) or (r["cycle"] or b.cycle_of(r["date"])) not in ("2024", "2026"):
            continue
        (pac if is_pac else emp)[r["member_bioguide"]] += b.amt(r["amount_usd"])
        if is_emp:
            # 2026-11-26: one person per surname and first name ('LOFGREN, PETER MR.' is 'LOFGREN, PETER'); spellings were counted as people.
            # X63-267: a hyphen or apostrophe is dropped first, so 'EDWARDS-APPELL' and 'EDWARDSAPPELL' are one surname
            donors[r["member_bioguide"]].add(bf.norm_name(re.sub(r"[-'\u2019]", "", r["payer"] or "")))
        ids.append(r["row_id"])
    ms = sorted(set(emp) | set(pac))  # 2026-11-26: a fixed order, so sums and ties do not depend on the hash seed
    tot = {m: emp[m] + pac[m] for m in ms}
    by_party = collections.defaultdict(float); n_party = collections.Counter()
    for m in ms:
        p = (sit[m]["party"] or "?")[:1]
        by_party[p] += tot[m]; n_party[p] += 1
    all_tot = sum(tot.values()); all_donors = set().union(*donors.values()) if donors else set()
    top = sorted(ms, key=lambda m: (-tot[m], sit[m]["member_name"]))[:40]  # equal totals in name order (two pairs were tied; set order chose)
    mx = max(tot[m] for m in top)
    x0, lw, bwmax, y0, rh = 40, 470, 1150, 80, 36
    svg = [b.txt(40, 40, f"The 40 sitting members receiving the most Anthropic money, 2024 and 2026 cycles (of {len(ms)} who received any)", 24, weight="bold")]
    for i, m in enumerate(top):
        y = y0 + i * rh
        mm = sit[m]
        label = f"{mm['member_name']} ({(mm['party'] or '?')[:1]}-{mm['state']}{'' if mm['chamber'].startswith('S') else '-' + ('AL' if str(mm['district'] or '0') in ('0', '00', '') else str(mm['district']))})"
        svg.append(b.txt(x0 + lw - 14, y + rh * 0.68, label[:44], 17, anchor="end", fill=b.party_colour(mm["party"])))
        x = x0 + lw
        for v, col in ((emp[m], EMP), (pac[m], PAC)):
            if v:
                w = max(2.0, bwmax * v / mx)
                svg.append(f'<rect x="{x:.1f}" y="{y + 5}" width="{w:.1f}" height="{rh - 10}" fill="{col}"/>')
                x += w
        n = len(donors[m])
        svg.append(b.txt(x + 10, y + rh * 0.68, f"{money(tot[m])}", 16, weight="bold"))
        svg.append(b.txt(x + 90, y + rh * 0.68, f"{n} employee{'s' if n != 1 else ''}" + (f" + ANTHROPAC {money(pac[m])}" if pac[m] else ""), 14, fill=b.MUTED))
    d, r_ = by_party.get("D", 0.0), by_party.get("R", 0.0)
    n_i = n_party["I"]; ind = f", {money(by_party['I'])} to {'one' if n_i == 1 else n_i} independent{'s' if n_i != 1 else ''}" if n_i else ""  # X63-172
    latest = datetime.date.fromisoformat(max(b.BY_ID[i]["date"] for i in ids)[:10]).strftime("%-d %B %Y")  # X63-171: the rows show the last transaction, not a coverage date
    subtitle = (f"What this is: campaign contributions to sitting members from people who list Anthropic as their employer, plus Anthropic's company PAC (ANTHROPAC), counted once each, "
                f"to any of the member's committees (campaign, a campaign for another office, leadership PAC, joint fundraising committee). {money(all_tot)} in all from {len(all_donors)} employees and the PAC: "
                f"{money(d)} to {n_party['D']} Democrats ({100 * d / all_tot:.0f}%), {money(r_)} to {n_party['R']} Republicans{ind}.")
    footnote = ("<b>What the record does not show.</b> An employee's gift is their own money, not the company's; the employer is as the donor wrote it on the filing. "
                "ANTHROPAC's money comes from its members and is given by the PAC. A contribution is not a vote. Pass-through and memo entries are counted once or not at all. "
                "Employees are counted by filed surname and first name, so a title, a middle initial or a hyphen does not make a second person; a name filed from more than one city counts once. "
                f"Anthropic's $40M to Public First Action is outside spending and is not here (see figure 02). The latest contribution here is dated {latest}; the 2026 cycle is still open.")
    bf.figure("anthropic-money-per-member", f"Anthropic employees and its PAC gave {money(all_tot)} to {len(ms)} sitting members; {100 * d / all_tot:.0f}% went to Democrats",
              subtitle, "\n".join(svg), footnote, ids, height=y0 + len(top) * rh + 470,
              legend_html=legend([(EMP, "Anthropic employees"), (PAC, "ANTHROPAC (company PAC)"), (b.DEM, "Democrat (name colour)"), (b.REP, "Republican (name colour)")]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
