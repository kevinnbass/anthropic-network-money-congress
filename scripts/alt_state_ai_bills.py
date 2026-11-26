#!/usr/bin/env python3
"""Draft (figures-alt): who lobbied the states' AI-safety bills, and the network's share. Clients per bill come from
research/primary/C159-state-ai-lobbying/ai_bill_lobbying.csv (lane C159, reviewed in R159; every client that reported
lobbying on CA SB 1047, CA SB 53 or NY's RAISE Act, marked network or other; not yet promoted rows, so this stays a draft
until that list is audited); the network's payments are the SG evidence rows promoted from C159 and checked by X25.
usage: python3 scripts/alt_state_ai_bills.py"""
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
FINAL = False  # 2026-09-29: build_figures3.py sets True to render the registered figure into figures/
NET, OTH = "#7a5195", "#c9c4b8"
SRC = bf.ROOT / "research/state_ai_bill_clients.csv"  # 2026-09-29: the client list verified by census audit X32 (one row per client and bill family)


def bill_of(s: str) -> str:
    if "1047" in s:
        return "California SB 1047 (2024)"
    if "SB 53" in s:
        return "California SB 53 (2025)"
    return "New York RAISE Act (2025)"


def key(s: str) -> str:
    return re.sub(r"(INC|LLC|CORP|CORPORATION|PBC|THE)", "", re.sub(r"[^A-Z0-9]", "", (s or "").upper()))


def main() -> int:
    stem = "congress-28-state-ai-bill-lobbying"
    if not FINAL:
        stem = "state-ai-bills-draft"
    rows = list(csv.DictReader(l for l in open(SRC, encoding="utf-8") if not l.startswith("#")))
    clients = collections.defaultdict(dict)
    for r in rows:  # names are already joined by X32's documented rule (client_key)
        clients[r["bill_family"]].setdefault(r["client_key"], (r["client"].strip(), r["class"]))
    bills = ["California SB 1047 (2024)", "California SB 53 (2025–26)", "New York RAISE Act (2025–26)"]
    width = 1250  # bar area width
    x0, lw, bw, y0, rh = 40, 420, width, 100, 70
    mx = max(len(clients[bl]) for bl in bills)
    svg = [b.txt(40, 44, "Clients that reported lobbying on each bill (each client once per bill), network clients first", 24, weight="bold")]
    for i, bl in enumerate(bills):
        yy = y0 + i * rh
        c = clients[bl]; n_net = sum(1 for _, cl in c.values() if cl == "network")
        svg.append(b.txt(x0 + lw - 16, yy + 38, bl, 19, anchor="end", weight="bold"))
        wn = bw * n_net / mx; wo = bw * (len(c) - n_net) / mx
        svg.append(f'<rect x="{x0 + lw}" y="{yy + 14}" width="{wn:.1f}" height="36" fill="{NET}"/>')
        svg.append(f'<rect x="{x0 + lw + wn:.1f}" y="{yy + 14}" width="{wo:.1f}" height="36" fill="{OTH}"/>')
        svg.append(b.txt(x0 + lw + wn + wo + 12, yy + 38, f"{len(c)} clients, {n_net} in the network", 17))
    ly = y0 + len(bills) * rh + 60
    svg.append(b.txt(40, ly, "The network's clients on each bill, and what they reported paying for state lobbying", 22, weight="bold"))
    # 2026-09-29 (X33-026): every evidence state lobbying payment in 2024–2026 by a network client of these bills, not only lane C159's
    # rows (Anthropic's own California F635 reports were missing); the firms' F625 copies of those payments are context (X33-021)
    netkeys = {key(nm) for bl in bills for nm, cl in clients[bl].values() if cl == "network"}
    def yr(r):
        return (r.get("period") or "")[:4] if re.match(r"\d{4}", r.get("period") or "") else (r["date"] or "")[:4]
    sg = [r for r in b.SG if b.ev(r) and r["money_type"] == "lobbying_spend" and r["state"] in ("CA", "NY") and key(r["payer"]) in netkeys and "2024" <= yr(r) <= "2026"]
    ids = [r["row_id"] for r in sg]
    pay = collections.defaultdict(float)
    for r in sg:
        pay[(r["state"], key(r["payer"]))] += b.amt(r["amount_usd"])
    for i, bl in enumerate(bills):
        yy = ly + 44 + i * 40
        st = "CA" if bl.startswith("California") else "NY"
        names = sorted({nm for nm, cl in clients[bl].values() if cl == "network"})
        svg.append(b.txt(60, yy, bl, 18, weight="bold"))
        svg.append(b.txt(480, yy, "; ".join(f"{nm} ({money(pay[(st, key(nm))])} in {st})" if pay.get((st, key(nm))) else nm for nm in names), 17))
    subtitle = ("What this is: every organisation that told California or New York it lobbied on the three main state AI-safety bills, from the states' own "
                "lobbying records, with the network's organisations picked out. Payments are what each reported paying for state lobbying in 2024–2026, on all "
                "its issues, not only these bills.")
    footnote = ("<b>What the record does not show.</b> State filings list the bills a client lobbied on but not the side it took, so this chart shows who "
                "lobbied, not who supported or opposed. Names that differ only in case or punctuation, or that a filer id or address shows to be one client, are counted once. Lobbying is not a vote. "
                + ("" if FINAL else "Draft figure: the list of other clients has been reviewed but not yet independently audited."))
    bf.figure(stem, "The network lobbied all three state AI-safety bills, as a handful of clients among many", subtitle, "\n".join(svg),
              footnote, ids, height=ly + 44 + len(bills) * 40 + 470, legend_html=legend([(NET, "network organisations"), (OTH, "every other reported client")]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
