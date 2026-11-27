#!/usr/bin/env python3
"""Network-wide companion to ai-machine figure 6A: sitting members ranked by direct contributions from the whole
network, 2024 and 2026 cycles, each bar split by the giving entity. Rows are exactly the counted type-1 and type-2
rows of research/members_network.csv (t1_ids, t2_ids), so memo, conduit and namesake lines are already out; the
law firm's PAC (in type 2 only because the firm lobbies for a network client) is left out. Rendered to figures-alt/.
usage: python3 scripts/alt_network_money.py [--data DIR]   (--data also writes contributions.csv and member_totals_by_entity.csv into DIR)"""
from __future__ import annotations

import collections
import datetime
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_figures as bf  # noqa: E402
import build_figures2 as b  # noqa: E402
import employer_rule as E  # noqa: E402
from casework.figures.common import legend, money  # noqa: E402

bf.OUT = bf.ROOT / "figures-alt"
GROUPS = [("Anthropic employees", "#2f8f9d"), ("ANTHROPAC (Anthropic's PAC)", "#e07b39"), ("ARI PAC", "#7a5195"),
          ("Eric Schmidt", "#2c6fbb"), ("Wendy Schmidt", "#7fb3e6"), ("James McClave", "#c0392b"), ("Emily Berger", "#e8a09a"),
          ("Reed Hastings", "#5b8c3a"), ("Coefficient Giving / Open Philanthropy staff", "#d4a72c"),
          ("Schmidt organisations / Hillspire staff", "#8c6d46"), ("other network people", "#9a9a9a")]
NAMED = {"Eric Schmidt", "Wendy Schmidt", "James McClave", "Emily Berger", "Reed Hastings"}


def main() -> int:
    principals = {bf.norm_name(r["name"]): r["name"] for r in b.EN if r["tier"] in ("T1", "T2", "T3") and r["entity_type"] == "person" and b.ev(r)}
    sit = {m["member_bioguide"]: m for m in b.SITTING}
    val = collections.defaultdict(float); ids = []; lines = []

    def group(r, t: str) -> str | None:
        if t == "2":
            n = (r["payer"] or "").upper()
            return "ANTHROPAC (Anthropic's PAC)" if "ANTHROP" in n else "ARI PAC" if "RESPONSIBLE INNOVATION" in n else None
        name = principals.get(bf.norm_name(r["payer"]))
        if name in NAMED:
            return name
        note = r["note"] or ""
        emp = E.employer(note).upper()  # 2026-11-27 (audit X79-5606): the shared rule, scripts/employer_rule.py
        if E.anthropic_employee(r):
            return "Anthropic employees"
        if re.search("COEFFICIENT|OPEN PHIL|GOOD VENTURES", emp):
            return "Coefficient Giving / Open Philanthropy staff"
        if re.search("SCHMIDT|HILLSPIRE", emp):
            return "Schmidt organisations / Hillspire staff"
        return "other network people"

    for m in b.SITTING:
        for t in ("1", "2"):
            for rid in m[f"t{t}_ids"].split():
                r = b.BY_ID.get(rid)
                if not r or (r["cycle"] or b.cycle_of(r["date"])) not in ("2024", "2026"):
                    continue
                g = group(r, t)
                if g:
                    val[(m["member_bioguide"], g)] += b.amt(r["amount_usd"]); ids.append(rid)
                    sub = re.search(r"\bsub_id=(\d+)", (r["note"] or "") + " " + (r["url"] or ""))
                    lines.append({"member": m["member_name"], "party": (m["party"] or "")[:1], "chamber": m["chamber"], "state": m["state"], "district": m["district"],
                                  "bioguide_id": m["member_bioguide"], "entity_group": g, "giver": r["payer"], "recipient_committee": r["payee"], "recipient_committee_id": r["payee_id"],
                                  "amount_usd": f"{b.amt(r['amount_usd']):.2f}", "date": r["date"], "cycle": r["cycle"] or b.cycle_of(r["date"]),
                                  "kind": "PAC contribution" if t == "2" else "individual contribution", "fec_sub_id": sub.group(1) if sub else "", "source_url": r["url"], "record_id": rid})
    tot = collections.defaultdict(float); gt = collections.defaultdict(float)
    for (mb, g), v in val.items():
        tot[mb] += v; gt[g] += v
    ms = [mb for mb in tot if tot[mb] > 0]
    all_tot = sum(tot.values())
    by_party = collections.defaultdict(float); n_party = collections.Counter()
    for mb in ms:
        p = (sit[mb]["party"] or "?")[:1]; by_party[p] += tot[mb]; n_party[p] += 1
    top = sorted(ms, key=lambda mb: -tot[mb])[:40]
    mx = max(tot[mb] for mb in top)
    x0, lw, bwmax, y0, rh = 40, 470, 1250, 80, 36
    svg = [b.txt(40, 40, f"The 40 sitting members receiving the most direct money from the network, 2024 and 2026 cycles (of {len(ms)} who received any), by giver", 24, weight="bold")]
    for i, mb in enumerate(top):
        y = y0 + i * rh; mm = sit[mb]
        dist = "" if mm["chamber"].startswith("S") else "-" + ("AL" if str(mm["district"] or "0") in ("0", "00", "") else str(mm["district"]))
        svg.append(b.txt(x0 + lw - 14, y + rh * 0.68, f"{mm['member_name']} ({(mm['party'] or '?')[:1]}-{mm['state']}{dist})"[:44], 17, anchor="end", fill=b.party_colour(mm["party"])))
        x = x0 + lw
        for g, col in GROUPS:
            v = val.get((mb, g), 0.0)
            if v:
                w = max(1.5, bwmax * v / mx)
                svg.append(f'<rect x="{x:.1f}" y="{y + 5}" width="{w:.1f}" height="{rh - 10}" fill="{col}"/>')
                x += w
        svg.append(b.txt(x + 10, y + rh * 0.68, money(tot[mb]), 16, weight="bold"))
    d, r_ = by_party.get("D", 0.0), by_party.get("R", 0.0)
    n_i = n_party["I"]; ind = f", {money(by_party['I'])} to {'one' if n_i == 1 else n_i} independent{'s' if n_i != 1 else ''}" if n_i else ""  # X63-118
    latest = datetime.date.fromisoformat(max(b.BY_ID[i]["date"] for i in ids)[:10]).strftime("%-d %B %Y")  # X63-117: the rows show the last transaction, not a coverage date
    shares = ", ".join(f"{g.split(' (')[0]} {money(gt[g])}" for g, _ in sorted(GROUPS, key=lambda x: -gt[x[0]])[:4])
    subtitle = (f"What this is: contributions to the committees the record ties to one sitting member (campaign, a campaign for another office, leadership PAC, single-member joint fundraising committee) from the network's principals, "
                f"from people who list a network organisation as employer, and from ANTHROPAC and ARI PAC, each counted once: "
                f"{money(d)} to {n_party['D']} Democrats ({100 * d / all_tot:.0f}%), {money(r_)} to {n_party['R']} Republicans{ind}.")
    footnote = ("<b>What the record does not show.</b> A person's gift is their own money, not their employer's; employers are as donors wrote them. "
                "Principals are matched by name and confirmed by employer and city; namesakes are left out. Super PAC money, lobbyists' own gifts and the law firm's PAC are not here "
                f"(see figures 09, 10, 11 and 12). A contribution is not a vote. The latest contribution here is dated {latest}; the 2026 cycle is still open.")
    bf.figure("network-money-per-member", f"The network gave {money(all_tot)} to {len(ms)} sitting members in 2024–26, most of it from Anthropic staff",
              subtitle, "\n".join(svg), footnote, ids, height=y0 + len(top) * rh + 540,
              legend_html=legend([(c, g) for g, c in GROUPS if gt[g] > 0]))
    if "--data" in sys.argv:  # the chart's own rows and bar segments, one file each
        import csv
        out = Path(sys.argv[sys.argv.index("--data") + 1]); out.mkdir(parents=True, exist_ok=True)
        with open(out / "contributions.csv", "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(lines[0]), lineterminator="\n"); w.writeheader()
            w.writerows(sorted(lines, key=lambda x: (x["member"], x["date"], x["record_id"])))
        with open(out / "member_totals_by_entity.csv", "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh, lineterminator="\n"); w.writerow(["member", "party", "chamber", "state", "district", "bioguide_id", "entity_group", "total_usd"])
            for (mb, g), v in sorted(val.items(), key=lambda kv: (sit[kv[0][0]]["member_name"], kv[0][1])):
                mm = sit[mb]
                w.writerow([mm["member_name"], (mm["party"] or "")[:1], mm["chamber"], mm["state"], mm["district"], mb, g, f"{v:.2f}"])
        print(f"wrote {len(lines)} contributions and {len(val)} member totals into {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
