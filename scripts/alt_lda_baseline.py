#!/usr/bin/env python3
"""Federal AI lobbying: the network against the frontier labs and every client that reported an AI issue, 2019-2025, from
research/lda_baseline.csv (lane C160 corrected by census audit X29) plus research/lda_baseline_additions.csv when present
(the filings that name only "AI", lane C160b, audited by X31). Amounts are each filing's whole reported income or
expenses for all its issues, never an estimate of AI spending.
usage: python3 scripts/alt_lda_baseline.py"""
from __future__ import annotations

import collections
import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_figures as bf  # noqa: E402
import build_figures2 as b  # noqa: E402
from casework.figures.common import legend, money  # noqa: E402

bf.OUT = bf.ROOT / "figures-alt"
FINAL = False
LDA_THRESHOLD_USD = 5000  # the LDA reporting threshold below which a report states no amount (2 U.S.C. 1604(c)(1))
NET, LAB, ALL_ = "#7a5195", "#e07b39", "#9a9a9a"
BASE = bf.ROOT / "research/lda_baseline.csv"
ADD = bf.ROOT / "research/lda_baseline_additions.csv"


def load(p: Path) -> list[dict]:
    return list(csv.DictReader(l for l in open(p, encoding="utf-8") if not l.startswith("#"))) if p.exists() else []


def label(client: str) -> str:
    c = re.sub(r"\s+", " ", client or "").strip().upper()
    for k, v in (("META PLATFORMS", "Meta"), ("AMAZON", "Amazon"), ("GOOGLE", "Google"), ("ALPHABET", "Google"), ("WING", "Google"), ("MICROSOFT", "Microsoft"),
                 ("NVIDIA", "Nvidia"), ("OPENAI", "OpenAI"), ("X.AI", "xAI"), ("XAI", "xAI"), ("ANTHROPIC", "Anthropic"),
                 ("RESPONSIBLE INNOVATION", "Americans for Responsible Innovation"), ("CENTER FOR AI SAFETY", "Center for AI Safety Action Fund"),
                 ("FUTURE OF LIFE", "Future of Life Institute"), ("ENCODE", "Encode"), ("FEDERATION OF AMERICAN SCIENTISTS", "Federation of American Scientists"), ("APOLLO RESEARCH", "Apollo Research"), ("OPEN PHILANTHROPY ACTION", "Open Philanthropy Action Fund")):
        if k in c:
            return v
    return client.title()[:40]


INHOUSE = {r["filing_uuid"]: r["reports_expenses"] for r in load(bf.ROOT / "research/lda_filing_expenses.csv")}


def _nz(s: str) -> str:
    return " ".join(re.sub(r"\b(INC|LLC|PBC|CORP|CORPORATION|CO|COMPANY|THE)\b", "", re.sub(r"[^A-Z0-9 ]", " ", (s or "").upper())).split())


def inhouse_precedence(rows: list[dict]) -> tuple[list[dict], collections.Counter]:
    """X39-1035 (Kevin, 2026-10-11, E5): an in-house filer's reported expenses already include what it paid outside firms,
    so for a client and quarter with an in-house report, outside firms' income for that client and quarter is not added.
    In-house is read from the saved filing itself (a self-filer reports expenses, a firm reports income), not from names."""
    # X51 (2026-10-11): a filing below the $5,000 threshold has both API amounts null; its printed checkbox gives the branch
    censored = {r["uuid"]: r["branch"] for r in load(bf.ROOT / "research/lda_branch_censored.csv")}
    # X51: outside filings whose client X51 documented as the in-house filer under another name (FKA, DBA, acronym, issuer alias)
    pairs = {r["outside_uuid"] for r in load(bf.ROOT / "research/lda_precedence_pairs.csv")}
    for r in rows:
        r["_inhouse"] = INHOUSE[r["filing_uuid"]] == "1" or censored.get(r["filing_uuid"]) == "expenses"  # public copy: the saved filings' expenses field, read once into research/lda_filing_expenses.csv
        r["_ckey"] = label(r["client"]) if r["group"] in ("network", "frontier_labs") else _nz(r["client"])
    inq = {(r["_ckey"], r["year"], r["quarter"]) for r in rows if r["_inhouse"]}
    kept, dropped = [], collections.Counter()
    for r in rows:
        if not r["_inhouse"] and ((r["_ckey"], r["year"], r["quarter"]) in inq or r["filing_uuid"] in pairs):
            dropped[(r["group"], "filings")] += 1; dropped[(r["group"], "usd")] += float(r["all_issues_usd"] or 0)
            continue
        kept.append(r)
    return kept, dropped


def main() -> int:
    stem = "congress-29-federal-ai-lobbying-baseline"
    if not FINAL:
        stem = "lda-baseline-draft"
    rows, dropped = inhouse_precedence(load(BASE) + load(ADD))
    for g in ("network", "frontier_labs", "other_ai_issue"):
        print(f"in-house precedence: {g} outside-firm filings not added {dropped[(g, 'filings')]} (${dropped[(g, 'usd')]:,.0f})")
    years = [str(y) for y in range(2019, 2026)]
    tot = collections.defaultdict(float)
    for r in rows:
        if r["year"] in years:
            tot[(r["group"], r["year"])] += float(r["all_issues_usd"] or 0)
    x0, y0, pw, ph = 40, 90, 1900, 360
    svg = [b.txt(40, 44, "Lobbying reported on filings with an AI issue: the network's clients and the frontier labs, by year (same scale)", 24, weight="bold")]
    mx = max([tot[(g, y)] for g in ("network", "frontier_labs") for y in years] + [1])
    bw = pw / len(years)
    for j, y in enumerate(years):
        for k, (g, col) in enumerate((("network", NET), ("frontier_labs", LAB))):
            v = tot[(g, y)]; h = ph * v / mx; x = x0 + 60 + j * bw + k * 64
            svg.append(f'<rect x="{x:.1f}" y="{y0 + ph - h:.1f}" width="56" height="{max(h, 1):.1f}" fill="{col}"/>')
            svg.append(b.txt(x + 28, y0 + ph - h - 8, money(v), 14, anchor="middle"))
        svg.append(b.txt(x0 + 60 + j * bw + 60, y0 + ph + 26, y, 16, anchor="middle", fill=b.MUTED))
    sy = y0 + ph + 110
    svg.append(b.txt(40, sy, "The network's share of all lobbying reported on filings with an AI issue", 22, weight="bold"))
    for j, y in enumerate(years):
        allv = tot[("network", y)] + tot[("frontier_labs", y)] + tot[("other_ai_issue", y)]
        share = 100 * tot[("network", y)] / allv if allv else 0
        x = x0 + 60 + j * bw; h = 180 * share / 1.0 if share < 1.0 else 180
        svg.append(f'<rect x="{x:.1f}" y="{sy + 200 - h:.1f}" width="120" height="{max(h, 1):.1f}" fill="{NET}"/>')
        svg.append(b.txt(x + 60, sy + 200 - h - 8, f"{share:.2f}%", 15, anchor="middle"))
        svg.append(b.txt(x + 60, sy + 226, f"{y}: all clients {money(allv)}", 13, anchor="middle", fill=b.MUTED))
    cy = sy + 290
    svg.append(b.txt(40, cy, "Largest clients in 2024–2025, network and frontier labs", 22, weight="bold"))
    cl = collections.defaultdict(float); grp = {}
    for r in rows:
        if r["year"] in ("2024", "2025") and r["group"] in ("network", "frontier_labs"):
            k = label(r["client"]); cl[k] += float(r["all_issues_usd"] or 0); grp[k] = r["group"]
    top = sorted(cl.items(), key=lambda kv: -kv[1])[:14]
    tm = max([v for _, v in top] + [1])
    for i, (k, v) in enumerate(top):
        yy = cy + 30 + i * 34; w = 1300 * v / tm
        svg.append(b.txt(x0 + 380, yy + 22, k, 16, anchor="end", weight="bold" if grp[k] == "network" else None))
        svg.append(f'<rect x="{x0 + 396}" y="{yy + 6}" width="{max(w, 1.5):.1f}" height="22" fill="{NET if grp[k] == "network" else LAB}"/>')
        svg.append(b.txt(x0 + 404 + w, yy + 22, money(v), 14))
    height = cy + 30 + len(top) * 34 + 470
    ids = []
    uu = {r["filing_uuid"] for r in rows if r["group"] == "network"}
    for r in b.LB:
        m = re.search(r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", (r.get("url") or "") + " " + (r.get("note") or ""))
        if m and m.group(1) in uu and b.ev(r):
            ids.append(r["row_id"])
    net25 = tot[("network", "2025")]; lab25 = tot[("frontier_labs", "2025")]
    all25 = net25 + lab25 + tot[("other_ai_issue", "2025")]
    subtitle = ("What this is: every federal lobbying report (LD-2) from 2019 to 2025 whose specific-issue text names artificial intelligence or an AI bill "
                "by its AI title, from the Senate's lobbying records. Network: Anthropic and the network organisations that lobby. Frontier labs: Meta, "
                "Amazon, Google, Microsoft, Nvidia, OpenAI and xAI. Each amount is what the report states for all of its issues.")
    footnote = ("<b>What the record does not show.</b> A lobbying report's amount covers every issue on it, so these are upper bounds on AI lobbying, "
                f"not estimates of it. A client's own in-house report already includes what it paid outside firms, so in a quarter with an in-house report for a documented common client the firms' fees are not added; amounts below the ${LDA_THRESHOLD_USD:,} reporting threshold are not counted, and expense methods may cover different activities. Some client identities and expense coverage remain unresolved, so these totals are provisional. Filings are matched to AI by their own issue text; a bill number alone was not enough, because many AI bills "
                "share numbers with unrelated bills in other sessions. Thirty filings the census held as adjacent algorithmic policy (other clients, none in the network) are left out. Lobbying is not a vote. Records through 2025.")
    title = f"The network reported {100 * net25 / all25:.1f}% of 2025's AI-issue lobbying; the frontier labs {100 * lab25 / all25:.0f}%"
    bf.figure(stem, title, subtitle, "\n".join(svg), footnote, ids,
              height=height, legend_html=legend([(NET, "network clients"), (LAB, "frontier labs")]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
