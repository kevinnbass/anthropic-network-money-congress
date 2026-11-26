#!/usr/bin/env python3
"""Second figure set (PLAN.md §4, exhaustive pass 2026-09-17): the connection types and tables the first seven figures
left undrawn. Same rules as build_figures.py: one type per figure or per column, never summed across types; hop 2
labelled; only rows bound as evidence; people named only in public roles (organisations and PLAN §1.1 principals);
no motive; a footnote on what the record does not show; row ids cited in the hidden comment.

Usage: python3 scripts/build_figures2.py [stem ...]   (no args = all)
"""
from __future__ import annotations
import collections, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_figures import (load, ROLE, ev, amt, party_colour, txt, bar_chart, figure, norm_name, client_label,  # noqa: E402
                           MB, HM, SP, LB, RD, FG, EN, TL, SITTING, PAL, DEM, REP, IND, GREY, INK, MUTED, NOW, TYPE_LABEL)
from casework.figures.common import money, legend, flow, esc  # noqa: E402

LC = load("lobbyist_contributions"); VN = load("vendors"); TV = load("travel"); MS = load("member_statements")
SG = load("state_government"); GR = load("grants"); PD = load("member_disclosures")
SIT = {m["member_bioguide"]: m for m in SITTING}
PARTY = {m["member_bioguide"]: (m["party"] or "?").upper()[:1] for m in MB if m["member_bioguide"].strip()}
NAME = {m["member_bioguide"]: m["member_name"] for m in MB}
BY_ID = {}
for _t in (HM, SP, LC, VN, TV, MS, SG, GR, PD, LB, RD, FG, EN, TL):
    for _r in _t:
        BY_ID[_r["row_id"]] = _r
PRINCIPALS = {norm_name(r["name"]): (r["name"], r["tier"]) for r in EN if r["tier"] in ("T1", "T2", "T3") and r["entity_type"] == "person" and ev(r)}
# 2026-09-27 (Kevin: figures 21 and 14 split network grants by cause): one cause class per evidence grant, from
# research/grant_causes.csv (lane C158, reviewed and audited); a grant without one is "unclassified"
import csv as _csv  # noqa: E402
_GC = Path(__file__).resolve().parents[1] / "research/grant_causes.csv"
CAUSE = {r["row_id"]: r["cause_class"] for r in _csv.DictReader(l for l in open(_GC, encoding="utf-8") if not l.startswith("#"))} if _GC.exists() else {}
NEUTRAL = "#7f8a8e"  # X39-1020..1024 (2026-10-11): single-series bars use a colour no legend uses
HELD = "#d6d9d3"  # rows held as context, drawn beside a NEUTRAL counted bar
CAUSE_LABEL = {"ai_tech_biosecurity_gcr": "AI, technology, biosecurity and catastrophic risk", "ea_community_research": "effective-altruism community and research",
               "economic_housing_labour_justice_policy": "housing, labour, economic and criminal-justice policy", "animal_welfare": "animal welfare",
               "global_development_migration": "global development and migration", "global_health": "global health",
               "climate_energy_science": "climate, energy and general science", "civic_electoral_foreign_policy": "civic, electoral and foreign policy",
               "broad_or_unallocated": "general support or broad purposes", "unclassified": "not yet classified"}


def cause_of(r) -> str:
    return CAUSE.get(r["row_id"], "unclassified")
ORG_WORDS = ("PAC", "INC", "LLC", "LLP", "FUND", "COMMITTEE", "ACTION", "FOUNDATION", "PBC", "CORP", "GROUP", "ASSOCIATION", "PARTNERS", "ALLIANCE", "PROJECT", "FIRST", "VENTURES")



def bind_no(note: str) -> bool:
    """The latest explicit binding decision in an append-only note: bind=yes(was no) overrides an earlier bind=no (Codex X8d, 2026-09-24)."""
    n = note or ""  # a bind=no with no later bind=yes; a correction writes bind=yes(was no) and may quote the old value
    return bool(re.search(r"\bbind=no\b", n)) and not re.search(r"\bbind=yes\b", n)

def cycle_of(date: str) -> str:
    y = (date or "")[:4]
    if not y.isdigit():
        return ""
    y = int(y)
    return str(y + (y % 2))


def is_org(name: str, payer_type: str = "") -> bool:
    n = (name or "").upper()
    if (payer_type or "").strip() == "individual":
        # 2026-11-26: for a payer the table types as an individual, only a whole word counts (PAC, INC), so a person whose name merely holds those
        # letters (Pacheco, Vincent) can never be drawn as an organisation under their own name. No row was affected on the day.
        return bool(set(re.findall(r"[A-Z]+", n.replace(".", ""))) & set(ORG_WORDS)) and "," not in n or n.endswith((" INC", " INC.", " LLC", " PBC"))
    return any(w in n.split() or w in n for w in ORG_WORDS) and "," not in n or n.endswith((" INC", " INC.", " LLC", " PBC"))


def public_name(name: str, payer_type: str = "") -> str:
    """Organisations and PLAN §1.1 principals by name; other individuals folded."""
    if is_org(name, payer_type):
        return re.sub(r"\s+", " ", name.strip())[:56]
    key = norm_name(name)
    if key in PRINCIPALS:
        return PRINCIPALS[key][0]
    return "other individuals (not named)"


def member_label(b: str) -> str:
    m = MB and next((x for x in MB if x["member_bioguide"] == b), None)
    if not m:
        return b
    return f"{m['member_name'][:34]} ({(m['party'] or '?')[:1]}-{m['state']})"


def stacked_bars(cells, xs, ys, x0, y0, w, h, colours, label_w=520, fmt=money, val_label=True, cap=None):
    """cells[(x_key, y_key)] -> value; one horizontal stacked bar per y in ys, segments per x in xs."""
    out = []
    tot = {y: sum(cells.get((x, y), 0.0) for x in xs) for y in ys}
    mx = max(list(tot.values()) + [1])
    bh = min(36, (h - 10) / max(1, len(ys)))
    for i, y in enumerate(ys):
        yy = y0 + i * bh
        out.append(txt(x0 + label_w - 14, yy + bh * 0.7, str(y)[:60], 16, anchor="end"))
        xx = x0 + label_w
        for j, x in enumerate(xs):
            v = cells.get((x, y), 0.0)
            if not v:
                continue
            bw = (w - label_w - 220) * v / mx
            out.append(f'<rect x="{xx:.1f}" y="{yy+3}" width="{max(1,bw):.1f}" height="{bh-7:.1f}" fill="{colours[j % len(colours)]}"/>')
            xx += bw
        if val_label:
            out.append(txt(xx + 8, yy + bh * 0.7, fmt(tot[y]), 15, fill=MUTED))
    return "\n".join(out)


KEY_X = 1500  # layout: left edge of a party key drawn beside a panel heading


def party_key(x, y):
    """X39-0505/0719: a party-colour key drawn beside each panel that colours bars by party."""
    out = []
    for k, (c, lab) in enumerate([(DEM, "Democrat"), (REP, "Republican"), (IND, "independent")]):
        out.append(f'<rect x="{x + k*190}" y="{y-14}" width="16" height="16" fill="{c}"/>'); out.append(txt(x + k*190 + 24, y, lab, 15, fill=MUTED))
    return "\n".join(out)


# ---------------------------------------------------------------- 08 member × type heatmap
def fig08():
    stem = "congress-08-member-type-heatmap"
    cols = ["1", "2", "10", "12", "9", "11", "5", "7", "6", "4a", "4b", "3b"]
    hop2 = {"4b", "3b"}
    short = {"1": "direct\ngifts", "2": "network\nPACs", "10": "bought AI\nsoftware", "12": "state\nmoney", "9": "travel,\nevents", "11": "public\nstatements", "5": "staff,\nfellows", "7": "federal\nmoney", "6": "grants", "4a": "lobbying on\ntheir bills", "4b": "lobbyists'\ngifts", "3b": "super PAC\nspending"}
    def score(m):
        h1 = sum(1 for t in cols if t not in hop2 and int(m[f"t{t}_n"]) > 0)
        allt = sum(1 for t in cols if int(m[f"t{t}_n"]) > 0)
        rows = sum(int(m[f"t{t}_n"]) for t in cols if t not in hop2)
        return (h1, allt, rows)
    members = sorted(SITTING, key=score, reverse=True)[:60]
    ids = [m["row_id"] for m in members]
    x0, y0, cw, rh = 40, 120, 112, 21
    svg = [txt(x0, 40, "The 60 sitting members with the most kinds of connection to the network (direct connections counted first; ties broken by all kinds, then records)", 24, weight="bold"),
           txt(x0, 70, "Each cell is the number of confirmed records of that kind for the member. Grey columns are money the network did not give directly: a lobbyist's own gift, or a super PAC's spending.", 17, fill=MUTED)]
    for j, t in enumerate(cols):
        x = x0 + 520 + j * cw
        for k, line in enumerate(short[t].split("\n")):
            svg.append(txt(x + cw / 2, y0 - 26 + k * 17, line, 14, anchor="middle", fill=MUTED, weight="bold"))
    svg.append(txt(x0 + 520 + len(cols) * cw + 20, y0 - 9, "kinds (direct / all)", 14, fill=MUTED, weight="bold"))
    for i, m in enumerate(members):
        y = y0 + i * rh
        if i % 2 == 0:
            svg.append(f'<rect x="{x0}" y="{y}" width="{520 + len(cols)*cw + 200}" height="{rh}" fill="#efece4"/>')
        svg.append(f'<rect x="{x0}" y="{y+4}" width="8" height="{rh-8}" fill="{party_colour(m["party"])}"/>')
        svg.append(txt(x0 + 16, y + 15, f"{m['member_name'][:30]} ({(m['party'] or '?')[:1]}-{m['state']}, {m['chamber'][:1]})", 15))
        for j, t in enumerate(cols):
            n = int(m[f"t{t}_n"])
            x = x0 + 520 + j * cw
            if n:
                import math
                a = min(1.0, 0.25 + 0.2 * math.log10(n + 1) * 1.5)
                col = GREY if t in hop2 else party_colour(m["party"])
                svg.append(f'<rect x="{x+2}" y="{y+2}" width="{cw-4}" height="{rh-4}" fill="{col}" opacity="{a:.2f}" rx="2"/>')
                svg.append(txt(x + cw / 2, y + 15, f"{n:,}", 13, anchor="middle", fill=INK if a < 0.7 else "#ffffff"))
        h1, allt, rows = score(m)
        svg.append(txt(x0 + 520 + len(cols) * cw + 20, y + 15, f"{h1} / {allt}", 14, fill=MUTED))
    subtitle = ('Sources: every confirmed record in this study linked to a sitting member. Money into super PACs and financial-disclosure links are left out: the first goes to committees rather than members, and the second touches only two members (household income from the Carnegie Endowment, a network grantee).')
    footnote = ('<b>What the record does not show.</b> Breadth is not weight: a member with five kinds may have one small record in each. A contribution is not a vote; outside spending is not coordination. Travel is mostly Aspen Institute conferences; a network-funded group is named as a sponsor of the 2025 conference, and network organisations supplied speakers at the others. Statements can be critical as well as friendly. A blank cell means none found, not none.')
    figure(stem, "Which members the most kinds of connection touch", subtitle, "\n".join(svg), footnote, ids, height=y0 + len(members) * rh + 560)


# ---------------------------------------------------------------- 09 IE committees and their network receipts
NAME2ID: dict[str, str] = {}
for _r in SP + HM:
    for _side in ("payer", "payee"):
        _cid = (_r.get(f"{_side}_id") or "").strip().upper(); _nm = re.sub(r"[^A-Z0-9]", "", (_r.get(_side) or "").upper())
        if _cid.startswith("C") and _nm:
            NAME2ID.setdefault(_nm, _cid)


def committee_key(r, side):
    cid = (r[f"{side}_id"] or "").strip().upper()
    nm = re.sub(r"[^A-Z0-9]", "", (r[side] or "").upper())
    return cid or NAME2ID.get(nm, nm)


def unique_ab(rows):
    """One contribution per (payer, payee, date, amount) across a Schedule A copy and a Schedule B copy; two lines on one schedule stay (Codex X1b #5)."""
    seen = {}; out = []
    for r in sorted(rows, key=lambda r: (len(r["row_id"]), r["row_id"])):
        k = (re.sub(r"[^A-Z0-9]", "", (r["payer"] or "").upper()), committee_key(r, "payee"), (r["date"] or "").strip(), round(amt(r["amount_usd"]), 2))
        sched = "B" if "schedule_b" in (r["url"] or "") else "A"
        if k in seen and seen[k] != sched:
            continue
        seen[k] = sched; out.append(r)
    return out


def unique_lines(rows):
    """One line per (payer, payee, date, amount): the A1/A6 rule for Schedule A lines pulled more than once or itemised on several lines."""
    seen = set(); out = []
    for r in rows:
        k = (re.sub(r"[^A-Z0-9]", "", (r["payer"] or "").upper()), committee_key(r, "payee"), (r["date"] or "").strip(), round(amt(r["amount_usd"]), 2))
        if k not in seen:
            seen.add(k); out.append(r)
    return out


def fig09():
    stem = "congress-09-ie-committees-and-network-receipts"
    ie = [r for r in SP if ev(r) and r["money_type"] in ("independent_expenditure", "electioneering_communication") and r["member_bioguide"] in SIT]
    per = collections.defaultdict(lambda: {"support": 0.0, "oppose": 0.0, "members": set(), "ids": [], "name": ""})
    for r in ie:
        d = per[committee_key(r, "payer")]
        so = (r["support_oppose"] or "").lower()
        if so in ("support", "oppose"):
            d[so] += amt(r["amount_usd"])
        else:
            d["undesignated"] = d.get("undesignated", 0.0) + amt(r["amount_usd"])  # 2026-09-23 (Codex X1b #3): a blank designation is not support
        d["members"].add(r["member_bioguide"]); d["ids"].append(r["row_id"]); d["name"] = d["name"] or r["payer"]
    # network itemised receipts into those committees: SP receipts (payee) + HM rows whose payee is the committee
    rec = collections.defaultdict(lambda: {"usd": 0.0, "ids": [], "seen": set()})
    for r in SP:
        if ev(r) and r["money_type"] in ("outside_receipt", "transfer"):
            k = committee_key(r, "payee")
            if k in per:
                u = (re.sub(r"[^A-Z0-9]", "", (r["payer"] or "").upper()), (r["date"] or "").strip(), round(amt(r["amount_usd"]), 2))
                if u not in rec[k]["seen"]:
                    rec[k]["seen"].add(u); rec[k]["usd"] += amt(r["amount_usd"]); rec[k]["ids"].append(r["row_id"])
    for r in HM:
        if ev(r) and r["money_type"] in ("hard_money", "transfer") and r["hop"] == "1":
            k = committee_key(r, "payee")
            if k in per:  # 2026-09-23 (Codex X1b #3): hard-money lines were classified line by line (A7); no key collapse
                rec[k]["usd"] += amt(r["amount_usd"]); rec[k]["ids"].append(r["row_id"])
    top = sorted(per.items(), key=lambda kv: -(kv[1]["support"] + kv[1]["oppose"]))[:22]
    ids = []
    svg = [txt(40, 40, f"Super PAC and party spending naming sitting members, by committee (the {len(top)} largest of {len(per)}), beside the money the network gave that committee", 23, weight="bold")]  # X40-0888: cut-off stated
    hdr = 84
    svg.append(txt(560, hdr, "spent for / against sitting members", 15, fill=MUTED, weight="bold")); svg.append(txt(1560, hdr, "members named", 15, fill=MUTED, weight="bold", anchor="end"))
    svg.append(txt(1600, hdr, "network money into the committee (own scale)", 15, fill=MUTED, weight="bold"))
    mx = max([d["support"] + d["oppose"] for _, d in top] + [1]); mxr = max([rec[k]["usd"] for k, _ in top] + [1])
    for i, (k, d) in enumerate(top):
        y = hdr + 20 + i * 42
        svg.append(txt(540, y + 24, (d["name"] or "?")[:44], 16, anchor="end"))
        ws = 720 * d["support"] / mx; wo = 720 * d["oppose"] / mx
        svg.append(f'<rect x="560" y="{y+4}" width="{ws:.1f}" height="30" fill="{DEM}" rx="3"/>')
        svg.append(f'<rect x="{560+ws:.1f}" y="{y+4}" width="{wo:.1f}" height="30" fill="{REP}" rx="3"/>')
        svg.append(txt(566 + ws + wo, y + 25, f"{money(d['support'])} for · {money(d['oppose'])} against" + (f" · {money(d['undesignated'])} undesignated" if d.get("undesignated") else "") + ("" if rec[k]["usd"] else "  (no network money found in this committee)"), 13, fill=MUTED))
        svg.append(txt(1560, y + 25, str(len(d["members"])), 15, anchor="end"))
        rv = rec[k]["usd"]
        wr = 380 * rv / mxr
        svg.append(f'<rect x="1600" y="{y+4}" width="{max(1,wr):.1f}" height="30" fill="{IND}" rx="3"/>')
        svg.append(txt(1606 + max(1, wr), y + 25, money(rv) if rv else "none found", 13, fill=MUTED))
        ids += d["ids"] + rec[k]["ids"]
    subtitle = ('Sources: FEC outside-spending reports naming a sitting member, grouped by the committee that spent; and FEC contribution records showing network people, staff or committees giving to that committee, each counted once. Left and right are on different scales and are never divided.')
    footnote = ("<b>What the record does not show.</b> The left bars are all of the committee's spending on sitting members; the right bar is only the network money found going in. Most of the left is not network money. A contribution does not direct spending, and outside spending is not coordination with any candidate. Party committees appear because a principal gave to them. Gifts to groups that do not disclose donors are not here, so both sides are floors.")
    figure(stem, "Who spends on members, and how much of that money came from the network", subtitle, "\n".join(svg), footnote, ids, height=hdr + 20 + len(top) * 42 + 480,
           legend_html=legend([(DEM, "spent in support of the member"), (REP, "spent against the member"), (IND, "network money into the committee")]))


# ---------------------------------------------------------------- 10 lobbyists' own contributions
def registrant_of(note: str) -> str:
    m = re.search(r"registrant=([^;]+?)(?: id=| registrant_id=|;|$)", note or "")
    return (m.group(1).strip() if m else "").upper()[:46] or "(firm not recorded)"


def fig10():
    stem = "congress-10-lobbyists-own-contributions"
    rows = []
    for m in SITTING:
        for rid in m["t4b_ids"].split():
            r = BY_ID.get(rid)
            if r and (r.get("money_type") or "") == "hard_money":
                rows.append((m, r))
    ids = [r["row_id"] for _, r in rows]
    by_reg = collections.defaultdict(float); by_cycle = collections.defaultdict(float); by_member = collections.Counter(); regs_n = collections.Counter()
    for m, r in rows:
        p = (m["party"] or "?")[:1].upper(); reg = registrant_of(r["note"])
        by_reg[(p, reg)] += amt(r["amount_usd"]); regs_n[reg] += amt(r["amount_usd"])
        by_cycle[(p, r["cycle"] or cycle_of(r["date"]))] += amt(r["amount_usd"]); by_member[m["row_id"]] += amt(r["amount_usd"])
    regs = [k for k, _ in regs_n.most_common(14)]
    # 2026-09-29 (Kevin: "do both for lobbyist gifts. give both alternatives"): measure A = firm registered for a network client (drawn by
    # party below); measure B = the lobbyist is also named for that client on its LD-1 or LD-2 (research/lb_4b_measures.csv)
    from build_figures import MEAS4B
    rowsB = [(m, r) for m, r in rows if MEAS4B.get(r["row_id"]) == "named"]
    totA = sum(amt(r["amount_usd"]) for _, r in rows); totB = sum(amt(r["amount_usd"]) for _, r in rowsB)
    svg = [txt(40, 40, f"Lobbyists' own contributions to sitting members, by the LD-203 registrant named on the filing ({len(regs)} of {len(regs_n)} firms) and the recipient's party (the lobbyist gave, not the client)", 24, weight="bold"),  # X40-1008
           txt(40, 70, f"Two counts. A, drawn in the bars: the lobbyist's firm was registered for a network client on the gift's date: {money(totA)}, {len(rows):,} gifts, {len({m['row_id'] for m, _ in rows})} members. "
                       f"B, stricter: the lobbyist is also named for that client on its registration or quarterly reports: {money(totB)}, {len(rowsB):,} gifts, {len({m['row_id'] for m, _ in rowsB})} members.", 16, fill=MUTED)]
    svg.append(stacked_bars(by_reg, ["D", "R", "I"], regs, 40, 90, 2000, 530, [DEM, REP, IND], label_w=620))
    OFF = 470
    regB = collections.Counter(); cycA = collections.Counter(); cycB = collections.Counter()
    for m, r in rows:
        cycA[r["cycle"] or cycle_of(r["date"])] += amt(r["amount_usd"])
    for m, r in rowsB:
        regB[registrant_of(r["note"])] += amt(r["amount_usd"]); cycB[r["cycle"] or cycle_of(r["date"])] += amt(r["amount_usd"])
    svg.append(txt(40, 660, "The two counts side by side, by firm and by cycle (A: firm registered for a network client · B: lobbyist also named for that client)", 22, weight="bold"))
    for i, reg in enumerate(regs):
        yy = 700 + i * 28
        svg.append(txt(40 + 600, yy, reg[:60], 15, anchor="end"))
        wA = 700 * regs_n[reg] / max(regs_n.values()); wB = 700 * regB.get(reg, 0) / max(regs_n.values())
        svg.append(f'<rect x="660" y="{yy - 14}" width="{max(wA, 1):.1f}" height="16" fill="#c9c3b6"/>')
        svg.append(f'<rect x="660" y="{yy - 14}" width="{max(wB, 0):.1f}" height="16" fill="#5a5146"/>')
        svg.append(txt(670 + wA, yy, f"A {money(regs_n[reg])} · B {money(regB.get(reg, 0))}", 13, fill=MUTED))
    cyc_sorted = sorted(c for c in cycA if c)
    svg.append(txt(1600, 700, "By cycle", 17, weight="bold"))
    for j, c in enumerate(cyc_sorted):
        svg.append(txt(1600, 730 + j * 26, f"{c}: A {money(cycA[c])} · B {money(cycB.get(c, 0))}", 15))
    cycles = sorted({c for (_, c) in by_cycle if c})
    svg.append(txt(40, 660 + OFF, "By election cycle and recipient party (count A)", 22, weight="bold"))
    mx = max(list(by_cycle.values()) + [1])
    for i, c in enumerate(cycles):
        x = 120 + i * 150
        for j, p in enumerate(["D", "R", "I"]):
            v = by_cycle.get((p, c), 0.0); h = 240 * v / mx
            svg.append(f'<rect x="{x + j*44}" y="{940 + OFF - h:.1f}" width="40" height="{h:.1f}" fill="{party_colour(p)}" rx="2"/>')
            if v:
                svg.append(txt(x + j * 44 + 20, 934 + OFF - h, money(v), 11, anchor="middle"))
        svg.append(txt(x + 66, 962 + OFF, c, 15, anchor="middle", fill=MUTED))
    mb_by = {m["row_id"]: m for m in SITTING}
    top = by_member.most_common(22)
    svg.append(txt(40, 1010 + OFF, f"The {len(top)} sitting members receiving the most of {len(by_member)}, count A (their campaign, leadership PAC and joint fundraising committees, and committees a filing names as honouring them)", 22, weight="bold"))  # X40-1008
    svg.append(bar_chart([(member_label(mb_by[k]["member_bioguide"]), v, mb_by[k]) for k, v in top], 40, 1030 + OFF, 2000, 700, label_w=520, colour=lambda m: party_colour(m["party"])))
    ids += [k for k, _ in top]
    subtitle = ("Sources: lobbyists' semi-annual contribution reports to Congress, for lobbyists whose firm was registered for a network client, counting only gifts dated while that registration ran (count A); count B also requires the lobbyist to be named for the network client on its registration or quarterly reports. The firm is as printed on the report; the money is the lobbyist's own.")
    footnote = ("<b>What the record does not show.</b> The client did not direct the lobbyist's personal gift, and most of these lobbyists also serve clients outside the network. A contribution is not a vote. A lobbyist who left the firm still appears under it for the period reported. Gifts dated before the firm took a network client, or after it stopped, are held but not drawn. Count B follows the filings, not each person's work: a registration lists lobbyists from its effective date, a quarterly report names who lobbied that quarter, and B runs to 90 days after the last quarter that names the lobbyist; the filings do not date when a person started or stopped working for the client. Some re-checks could not be completed and are left out.")
    figure(stem, "Lobbyists' own money, by firm, cycle and recipient", subtitle, "\n".join(svg), footnote, ids, height=2100 + OFF,
           legend_html=legend([(DEM, "to Democrats"), (REP, "to Republicans"), (IND, "to independents")]))


# ---------------------------------------------------------------- 11 corporate PACs
def fig11():
    stem = "congress-11-corporate-pacs"
    rows = unique_ab([r for r in HM if ev(r) and r["money_type"] == "corporate_pac"])  # a Schedule A copy and a Schedule B copy of one contribution count once
    ids = [r["row_id"] for r in rows]
    def pac(r):
        n = r["payer"].upper()
        return "ANTHROPAC (Anthropic PBC PAC)" if "ANTHROP" in n else "ARI PAC (Americans for Responsible Innovation)" if "RESPONSIBLE INNOVATION" in n else "ARNOLD & PORTER PARTNERS PAC (lobbying firm's PAC)" if "ARNOLD" in n else n[:40]
    def party_of(r):
        p = (r["party"] or "").upper()[:1]
        if p in ("D", "R", "I"):
            return p
        b = r["member_bioguide"]
        if b in PARTY:
            return PARTY[b]
        n = r["payee"].upper()
        if any(w in n for w in ("DCCC", "DSCC", "DEMOCRATIC", "DEMOCRATS")):
            return "D"
        if any(w in n for w in ("NRCC", "NRSC", "REPUBLICAN")):
            return "R"
        return "?"
    cells = collections.defaultdict(float); cnt = collections.Counter()
    for r in rows:
        cells[(party_of(r), pac(r))] += amt(r["amount_usd"]); cnt[pac(r)] += 1
    pacs = [k for k, _ in cnt.most_common()]
    svg = [txt(40, 40, "PACs of network organisations and of a network client's lobbying firm, by recipient party (all recipients; each contribution counted once)", 24, weight="bold")]
    svg.append(stacked_bars(cells, ["D", "R", "I", "?"], pacs, 40, 60, 2000, 200, [DEM, REP, IND, GREY], label_w=620))
    svg.append(txt(40, 280, "Every sitting member who received money from these PACs (amount is that PAC's money only)", 22, weight="bold"))
    per = collections.defaultdict(lambda: {"usd": 0.0, "pacs": set(), "ids": []})
    for r in rows:
        if r["member_bioguide"] in SIT:
            d = per[r["member_bioguide"]]; d["usd"] += amt(r["amount_usd"]); d["pacs"].add(pac(r).split(" (")[0]); d["ids"].append(r["row_id"])
    items = sorted(per.items(), key=lambda kv: -kv[1]["usd"])
    colw = 2 if len(items) > 30 else 1
    per_col = (len(items) + colw - 1) // colw
    for i, (b, d) in enumerate(items):
        c, rr = divmod(i, per_col)
        x = 40 + c * 1000; y = 310 + rr * 26
        svg.append(f'<rect x="{x}" y="{y-14}" width="8" height="18" fill="{party_colour(PARTY.get(b, "?"))}"/>')
        svg.append(txt(x + 16, y, f"{member_label(b)}", 15))
        svg.append(txt(x + 560, y, money(d["usd"]), 15, anchor="end"))
        svg.append(txt(x + 580, y, ", ".join(sorted(d["pacs"])), 13, fill=MUTED))
    subtitle = ("Sources: FEC spending and contribution records of ANTHROPAC (Anthropic's PAC), ARI PAC (a membership group's PAC) and the Arnold & Porter partners' PAC (the law firm lobbies for a network client), plus the PACs' reports to Congress. Each line is one contribution as filed.")
    footnote = ("<b>What the record does not show.</b> A PAC contribution is not a vote. ANTHROPAC's and ARI PAC's money comes from their employees and members; the law firm's PAC is its partners' money and appears only because the firm lobbies for a network client. 2026 is still open, so totals are floors.")
    figure(stem, "The network's PACs and where they give", subtitle, "\n".join(svg), footnote, ids, height=310 + per_col * 26 + 520,
           legend_html=legend([(DEM, "to Democrats"), (REP, "to Republicans"), (IND, "to independents"), (GREY, "party not recorded")]))


# ---------------------------------------------------------------- 12 outside-money flows
def fig12():
    stem = "congress-12-outside-money-flows"
    rec = [r for r in SP if ev(r) and r["money_type"] in ("outside_receipt", "transfer")]
    uniq = {}
    for r in rec:
        key = (re.sub(r"[^A-Z0-9]", "", (r["payer"] or "").upper()), committee_key(r, "payee"), (r["date"] or "").strip(), round(amt(r["amount_usd"]), 2))
        uniq.setdefault(key, r)
    def payer_label(r):
        n = (r["payer"] or "").upper()
        if "ANTHROPIC" in n:
            return "Anthropic PBC"
        if "PUBLIC FIRST" in n:
            return "Public First family (internal transfers)"
        if (r["payer_type"] or "").strip() and r["payer_type"] != "individual":  # X39-0406: a committee by its filed type (STRONGER TOGETHER PA), not by a name keyword
            return re.sub(r"\s+", " ", (r["payer"] or "").strip())[:56]
        return public_name(r["payer"], r.get("payer_type", ""))
    def payee_label(r):
        return re.sub(r"[.,]", "", (r["payee"] or "?").upper())[:40]
    flows = collections.defaultdict(float); ids = []
    for r in uniq.values():
        flows[(payer_label(r), payee_label(r))] += amt(r["amount_usd"]); ids.append(r["row_id"])
    payers = collections.Counter(); payees = collections.Counter()
    for (a, b), v in flows.items():
        payers[a] += v; payees[b] += v
    L = [k for k, _ in payers.most_common(11)]; Rr = [k for k, _ in payees.most_common(16)]
    other_l = sum(v for k, v in payers.items() if k not in L); other_r = sum(v for k, v in payees.items() if k not in Rr)
    svg = [txt(40, 40, "Money into the network's super PACs and political nonprofits, 2016–2026", 23, weight="bold"),  # X39-0407/1018: two lines
           txt(40, 70, "By giver and recipient (each contribution counted once; other itemised donors included)", 19, fill=MUTED)]
    lx, rx, top, bottom = 560, 1500, 120, 1210
    def pos(keys, totals, extra):
        tot = sum(totals[k] for k in keys) + extra
        avail = (bottom - top) - 28 * (len(keys) + 1)
        ys = {}; y = top
        for k in keys:
            h = 28 + avail * totals[k] / tot
            ys[k] = (y, h); y += h
        return ys, y
    ly, ly_end = pos(L, payers, other_l); ry, ry_end = pos(Rr, payees, other_r)
    for (a, b), v in sorted(flows.items(), key=lambda kv: -kv[1]):
        if a not in ly or b not in ry:
            continue
        y1 = ly[a][0] + ly[a][1] / 2; y2 = ry[b][0] + ry[b][1] / 2
        w = max(1.5, 60 * v / max(payers.values()))
        col = IND if "Public First" in a else DEM if a in ("Anthropic PBC",) else PAL[L.index(a) % len(PAL)]
        mid = (lx + rx) / 2
        svg.append(f'<path d="M{lx+8},{y1:.1f} C{mid},{y1:.1f} {mid},{y2:.1f} {rx-8},{y2:.1f}" fill="none" stroke="{col}" stroke-width="{w:.1f}" opacity="0.45"/>')
    for k, (y, h) in ly.items():
        svg.append(f'<rect x="{lx}" y="{y:.1f}" width="10" height="{max(2,h-2):.1f}" fill="{INK}"/>')
        svg.append(txt(lx - 14, y + h / 2 + 5, f"{k[:52]}  {money(payers[k])}", 15, anchor="end"))
    svg.append(txt(lx - 14, ly_end + 16, f"all other payers  {money(other_l)}", 14, anchor="end", fill=MUTED))
    for k, (y, h) in ry.items():
        svg.append(f'<rect x="{rx}" y="{y:.1f}" width="10" height="{max(2,h-2):.1f}" fill="{INK}"/>')
        svg.append(txt(rx + 20, y + h / 2 + 5, f"{money(payees[k])}  {k}", 15))
    svg.append(txt(rx + 20, ry_end + 16, f"{money(other_r)}  all other committees", 14, fill=MUTED))
    ANTH_PFA = sum(amt(r["amount_usd"]) for r in SP if r["row_id"] in ("SP053", "SP054"))  # Anthropic's issuer-disclosed gifts to Public First Action
    MOSK_TRUST = sum(amt(r["amount_usd"]) for r in SP if ev(r) and "MOSKOVITZ TRUST" in ((r["quote_300"] or "") + (r["note"] or "")).upper())  # receipts filed under the trust
    subtitle = (f"Sources: FEC contribution records filed by the receiving committees; BEMC 4 Association's 2022 IRS filing listing grants to four political nonprofits; and Anthropic's own announcements of its {money(ANTH_PFA)} to Public First Action, which does not disclose donors. Other individual givers are grouped into one line.")
    footnote = (f"<b>What the record does not show.</b> A contribution is not an instruction: the committee spends as it chooses. Gifts to nonprofits that do not disclose donors do not appear, so Public First Action's funding beyond Anthropic's gift is a floor. FF PAC, SMP, LCV Victory Fund and MoveOn have many donors; the ribbon is the network's share, not their size. Gifts filed under Dustin Moskovitz's trust ({money(MOSK_TRUST)}) are drawn under his name. Refunds are not netted.")
    figure(stem, "Where the principals' outside money went", subtitle, "\n".join(svg), footnote, ids, height=1700)


# ---------------------------------------------------------------- 13 hard money by recipient vehicle + top recipients
def fig13():
    stem = "congress-13-hard-money-by-vehicle-and-recipient"
    # 2026-09-23 (Codex X3 #8): same-key hard-money lines were classified line by line (A7), so no key collapse here
    rows = [r for r in HM if ev(r) and r["money_type"] == "hard_money" and r["hop"] == "1" and r["payer_type"] == "individual"]
    VEH = {"candidate_committee": "candidate committee", "presidential_committee": "presidential committee", "party_committee": "party committee", "jfc": "joint fundraising committee", "leadership_pac": "leadership PAC",
           "hybrid_pac": "hybrid PAC / super PAC", "super_pac": "hybrid PAC / super PAC", "nonconnected_pac": "nonconnected PAC", "corporate_pac": "connected or registrant PAC", "": "not stated on the row"}  # 2026-09-23 (Codex X4b #3): classes follow the FEC committee master file
    cells = collections.defaultdict(float); ids = []
    for r in rows:
        c = r["cycle"] or cycle_of(r["date"])
        if "2016" <= c <= "2026":
            cells[(c, VEH.get(r["payee_type"], r["payee_type"]))] += amt(r["amount_usd"]); ids.append(r["row_id"])
    cycles = sorted({c for (c, _) in cells}); vehs = [v for v, _ in collections.Counter({v: sum(x for (c, vv), x in cells.items() if vv == v) for v in {v for (_, v) in cells}}).most_common()]
    svg = [txt(40, 40, "Direct contributions from network people (principals and employees), by the kind of committee receiving them and election cycle (all recipients, not only sitting members)", 24, weight="bold")]
    CPAL = PAL[3:]  # cycle colours stay off the party colours the lower panel uses
    svg.append(stacked_bars(cells, cycles, vehs, 40, 60, 2000, 380, CPAL, label_w=520))
    top = sorted(SITTING, key=lambda m: -float(m["t1_usd"] or 0))[:26]
    n_any = sum(1 for m in SITTING if float(m["t1_usd"] or 0) > 0)
    svg.append(txt(40, 470, f"The {min(len(top), n_any)} sitting members receiving the most, of {n_any} with any (their own campaign and leadership committees)", 22, weight="bold")); svg.append(party_key(KEY_X, 470))  # X40-1480
    svg.append(bar_chart([(member_label(m["member_bioguide"]), float(m["t1_usd"] or 0), m) for m in top if float(m["t1_usd"] or 0) > 0], 40, 490, 2000, 900, label_w=520, colour=lambda m: party_colour(m["party"])))
    ids += [m["row_id"] for m in top]
    subtitle = ("Sources: FEC contribution records where the giver is a network principal or lists Anthropic, Coefficient Giving (formerly Open Philanthropy), Schmidt or Hillspire as employer. The lower panel adds up each member's own committees.")
    footnote = ("<b>What the record does not show.</b> A contribution is not a vote. An employee's giving is their own, not the employer's; the employer is as the giver wrote it. Gifts made through ActBlue or WinRed are counted once, from the recipient's report; where that report is not yet filed or does not itemise the gift, it is not counted. Gifts a committee reports twice are counted once. Gifts to super PACs also appear in the outside-money figures; here they only show the split by kind of committee. 2026 is still open, so every bar is a floor.")
    figure(stem, "Where network individuals' contributions land", subtitle, "\n".join(svg), footnote, ids, height=1850,
           legend_html=legend([(CPAL[i], c) for i, c in enumerate(cycles)]))


# ---------------------------------------------------------------- 14 dollars by cycle, per type
def fig14():
    stem = "congress-14-dollars-by-cycle-and-type"
    panels = []
    def sp_unique(rows):
        seen = set(); out = []
        for r in rows:
            k = (re.sub(r"[^A-Z0-9]", "", (r["payer"] or "").upper()), committee_key(r, "payee"), (r["date"] or "").strip(), round(amt(r["amount_usd"]), 2))
            if k not in seen:
                seen.add(k); out.append(r)
        return out
    panels.append(("Direct contributions from network people (all recipients)", [r for r in HM if ev(r) and r["money_type"] == "hard_money" and r["hop"] == "1" and r["payer_type"] == "individual"], DEM))
    panels.append(("Network PAC contributions (each counted once)", unique_ab([r for r in HM if ev(r) and r["money_type"] == "corporate_pac"]), PAL[3]))
    panels.append(("Network money into super PACs and political nonprofits", sp_unique([r for r in SP if ev(r) and r["money_type"] in ("outside_receipt", "transfer")]), IND))
    panels.append(("Spending by every super PAC in the study, all races (indirect)", [r for r in SP if ev(r) and r["money_type"] in ("independent_expenditure", "electioneering_communication")], GREY))
    panels.append(("Lobbyists' own contributions (indirect)", [r for r in LC if ev(r) and r["money_type"] == "hard_money"], GREY))
    paid = [r for r in GR if ev(r) and amt(r["amount_usd"]) > 0 and "990_group=approved_future" not in (r["note"] or "")]  # 2026-09-23 (Codex X5b #5)
    _unp = {r["row_id"] for r in load("grant_payment_unproven")}  # X53 (2026-10-11): as in figure 21, a payment that may restate a drawn award is not added
    paid = [r for r in paid if r["row_id"] not in _unp]
    # 2026-09-27 (Kevin): grants split by cause, as in figure 21
    panels.append(("Network grants for AI, technology, biosecurity and catastrophic-risk work (indirect)", [r for r in paid if cause_of(r) == "ai_tech_biosecurity_gcr"], PAL[4]))
    panels.append(("Network grants to other causes (indirect; see figure 21)", [r for r in paid if cause_of(r) != "ai_tech_biosecurity_gcr"], GREY))
    panels.append(("Campaigns and offices paying Anthropic / Claude (the OpenAI comparison is in figure 19)", [r for r in VN if ev(r) and r["money_type"] == "vendor" and re.search(r"ANTHROPIC|CLAUDE", r["payee"].upper())], PAL[5]))
    panels.append(("State-level contributions and lobbying spend", [r for r in SG if ev(r) and r["money_type"] in ("state_contribution", "lobbying_spend")], PAL[6]))
    cycles = [str(y) for y in range(2016, 2027, 2)]
    ids = []
    svg = [txt(40, 40, "Dollars by two-year election cycle, one panel per kind of connection, each on its own scale (panels are never added together)", 24, weight="bold")]
    pw, ph = 1000, 300
    for i, (title, rows, col) in enumerate(panels):
        rr, c = divmod(i, 2)
        x0 = 40 + c * (pw + 80); y0 = 90 + rr * (ph + 40)
        cells = collections.defaultdict(float); n = 0
        for r in rows:
            cy = r.get("cycle") or cycle_of(r.get("date") or r.get("fiscal_year") or "")
            if cy in cycles:
                cells[cy] += amt(r["amount_usd"]); ids.append(r["row_id"]); n += 1
        is4b = title.startswith("Lobbyists' own contributions")
        cellsB = collections.defaultdict(float)
        if is4b:  # 2026-09-29 (Kevin: both counts): dark inner bar = lobbyist also named for the network client (research/lb_4b_measures.csv)
            from build_figures import MEAS4B
            for r in rows:
                cy = r.get("cycle") or cycle_of(r.get("date") or "")
                if cy in cycles and MEAS4B.get(r["row_id"]) == "named":
                    cellsB[cy] += amt(r["amount_usd"])
            title = "Lobbyists' own contributions (indirect; grey: firm registered for a network client; dark: lobbyist also named for it)"
        svg.append(txt(x0, y0, f"{title} · {n:,} records", 17 if not is4b else 15, weight="bold"))
        mx = max(list(cells.values()) + [1])
        bw = (pw - 60) / len(cycles)
        for j, cy in enumerate(cycles):
            v = cells.get(cy, 0.0); h = (ph - 80) * v / mx
            svg.append(f'<rect x="{x0 + 40 + j*bw:.1f}" y="{y0 + ph - 50 - h:.1f}" width="{bw-14:.1f}" height="{h:.1f}" fill="{col}" rx="3"/>')
            svg.append(txt(x0 + 40 + j * bw + (bw - 14) / 2, y0 + ph - 30, cy, 14, anchor="middle", fill=MUTED))
            if is4b and cellsB.get(cy):
                hB = (ph - 80) * cellsB[cy] / mx
                svg.append(f'<rect x="{x0 + 40 + j*bw + 12:.1f}" y="{y0 + ph - 50 - hB:.1f}" width="{bw-38:.1f}" height="{hB:.1f}" fill="#5a5146" rx="2"/>')
            if v:
                svg.append(txt(x0 + 40 + j * bw + (bw - 14) / 2, y0 + ph - 56 - h, money(v) + (f" ({money(cellsB.get(cy, 0))} named)" if is4b else ""), 12, anchor="middle"))
    subtitle = ("Sources: every confirmed record with a dollar amount: FEC contribution and spending records, lobbyists' contribution reports, grant filings, campaign payments to AI labs and state filings, grouped by two-year election cycle. Panels marked indirect are second-hop money.")
    footnote = ('<b>What the record does not show.</b> Panels are separate and never added. The super PAC panel is all spending by the committees in the study, not only network money. Grants go to research and policy groups, and state money goes to state races. Totals follow search depth: 2024–2026 were searched most thoroughly and 2026 is still open, so every bar is a floor. A contribution is not a vote; outside spending is not coordination.')
    figure(stem, "Money by election cycle, one kind at a time", subtitle, "\n".join(svg), footnote, ids, height=90 + -(-len(panels) // 2) * (ph + 40) + 420)


# ---------------------------------------------------------------- 15 travel and events
def fig15():
    stem = "congress-15-travel-and-events"
    # look-alike sponsors the vision lanes recorded with bind=no are on the record but are not network travel
    rows = [r for r in TV if ev(r) and not bind_no(r.get("note") or "") and not (r["event"] or "").lower().startswith("hearing testimony")]  # X33-015: testimony is figure 26
    ids = [r["row_id"] for r in rows]
    NET = ("GOOD VENTURES", "COEFFICIENT", "OPEN PHILANTHROPY", "FEDERATION OF AMERICAN SCIENTISTS", "SCHMIDT", "INSTITUTE FOR PROGRESS", "ANTHROPIC", "RAND", "CSET", "FUTURE OF LIFE", "AMERICANS FOR RESPONSIBLE", "SEEDAI", "CNAS", "CENTER FOR A NEW AMERICAN SECURITY")
    def klass(r):  # 2026-09-23 (Codex X1b #11): the sponsor string decides; a bound participant is not a sponsor
        s = (r["sponsor"] or "").upper(); n = (r["note"] or "")
        if "ASPEN" in s:  # 2026-10-11 (audit X44; Kevin: keep the data, organised consistently): only these count
            return "Aspen conference with network people in a network role (Spain 2025, Bellagio 2026)"
        if any(w in s for w in NET):  # 2026-09-23 (Codex X4c #2): a network sponsor string decides before the Hill-event test
            return "sponsor line names a network organisation"
        if re.search(r"COMMITTEE|SUBCOMMITTEE|HOUSE |SENATE ", s) or "hill_briefing" in n or "roundtable" in (r["event"] or "").lower():
            return "Hill briefing, roundtable or demo (network organisation present)"
        return "other sponsor"
    by_k = collections.Counter(klass(r) for r in rows)
    # Aspen records kept on the record but not counted, by the class audit X44 found in the saved agendas (research/aspen_classes.json)
    try:
        aspen = json.load(open(Path(__file__).resolve().parents[1] / "research/aspen_classes.json"))
    except FileNotFoundError:
        aspen = {}
    TVI = {r["row_id"]: r for r in TV}
    copies = {r["row_id"] for r in load("travel_copies")}  # X40-3097 (2026-10-11): a copy of a trip another row carries is not counted again in grey
    held = collections.Counter()
    for rid, c in aspen.items():
        r = TVI.get(rid)
        if r and rid not in copies and ROLE.get(rid) == "context" and not c.startswith("counted") and not (r["event"] or "").lower().startswith("hearing testimony"):
            held[c.split(":")[0]] += 1
    bars = [(k, v, "counted") for k, v in by_k.most_common()] + [(f"{k} (on record, not counted)", v, "held") for k, v in held.most_common()]
    svg = [txt(40, 40, "Travel and events involving the network, by how the network appears on the filing (grey: Aspen records kept but not counted)", 24, weight="bold")]
    svg.append(bar_chart(bars, 40, 60, 2000, 200, label_w=1180, colour=lambda r: NEUTRAL if r == "counted" else HELD, fmt=lambda v: f"{int(v)} records", label_max=120))
    cells = collections.defaultdict(float)
    for r in rows:
        y = (r["date"] or r["start"] or "")[:4]
        if y.isdigit():
            cells[(PARTY.get(r["member_bioguide"], "?"), y)] += 1
    years = sorted({y for (_, y) in cells})
    svg.append(txt(40, 290, "Trips by year and the traveller's party (member and staff trips both count)", 22, weight="bold"))
    mx = max([sum(cells.get((p, y), 0) for p in "DRI?") for y in years] + [1])
    for i, y in enumerate(years):
        x = 120 + i * 150; yy = 560
        for p in ["D", "R", "I", "?"]:
            v = cells.get((p, y), 0); h = 220 * v / mx
            svg.append(f'<rect x="{x}" y="{yy-h:.1f}" width="90" height="{h:.1f}" fill="{party_colour(p)}"/>'); yy -= h
        svg.append(txt(x + 45, 585, y, 15, anchor="middle", fill=MUTED)); svg.append(txt(x + 45, yy - 6, str(int(sum(cells.get((p, y), 0) for p in "DRI?"))), 13, anchor="middle"))
    svg.append(txt(40, 640, "Co-sponsors named on the same filing lines (Aspen Institute conferences list the foundations that fund each programme)", 22, weight="bold"))
    # 2026-10-11 (audit X39 E16): organisations are matched by name, not split on "and" (which cut "Cooperative for Assistance and
    # Relief Everywhere" in two); a part matching no listed name falls back to a semicolon split only, since committee names
    # carry commas ("House Science, Space, and Technology Committee" is one sponsor)
    CANON = [("Gates Foundation (Bill & Melinda Gates Foundation)", r"Gates Foundation"), ("Rockefeller Brothers Fund", r"Rockefe(?:ll|11)er Brothers Fund"),
             ("Rockefeller Foundation", r"Rockefe(?:ll|11)er Foundation"), ("Democracy Fund", r"Democracy Fund"), ("Carnegie Corporation of New York", r"Carnegie Corporation"),
             ("Center for Responsible Innovation", r"Center for Responsible Innovation"), ("Breakthrough Energy Foundation", r"Breakthrough Energy"),
             ("Climate Imperative Foundation", r"Climate Imper"), ("Henry Luce Foundation", r"Henry Luce"), ("Cooperative for Assistance and Relief Everywhere (CARE)", r"Cooperative for Assistance|\bCARE\b"),
             ("Commonwealth Fund", r"Commonwealth Fund"), ("Eleanor Crook Foundation", r"Eleanor Crook"), ("William and Flora Hewlett Foundation", r"Hewlett"), ("Stanford University", r"Stanford"),
             ("Good Ventures Foundation", r"Good Ventures"), ("Institute for Progress", r"In(?:s)?titute for Progress"), ("Federation of American Scientists", r"Federation of American Scientists")]
    cof = collections.Counter()
    for r in rows:
        s = re.sub(r"\s+", " ", r["sponsor"] or "")
        hit = False
        for name, pat in CANON:
            if re.search(pat, s, re.I):
                cof[name] += 1; hit = True; s = re.sub(pat, "", s, flags=re.I)
        for part in s.split(";"):
            part = part.strip(" .,")
            if part and "aspen" not in part.lower() and len(part) > 3 and part.lower() not in ("inc", "the", "and") and not hit:
                cof[part] += 1
    svg.append(bar_chart([(k, v, None) for k, v in cof.most_common(10)], 40, 660, 2000, 380, label_w=900, colour=lambda r: NEUTRAL, fmt=lambda v: f"{int(v)} record{'s' if v != 1 else ''}", label_max=100))
    bym = collections.Counter(r["member_bioguide"] for r in rows if r["member_bioguide"] in SIT)
    MIN_TRIPS = 2  # 2026-10-11: the cutoff is a count, so no tie is cut; members below it are counted in the heading
    mt = [(b, v) for b, v in bym.most_common() if v >= MIN_TRIPS]
    n_below = sum(1 for v in bym.values() if v < MIN_TRIPS)
    svg.append(txt(40, 1060, f"Members with {MIN_TRIPS} or more trips ({n_below} more sitting members have one)", 22, weight="bold"))
    svg.append(bar_chart([(member_label(b), v, SIT[b]) for b, v in mt], 40, 1080, 2000, 34 * len(mt) + 40, label_w=520, colour=lambda m: party_colour(m["party"]), fmt=lambda v: f"{int(v)} trip{'s' if v != 1 else ''}"))
    ids += [SIT[b]["row_id"] for b in bym]
    subtitle = ('Sources: House and Senate gift-travel filings, event pages and conference reports. Sponsors are as printed on the filing; Hill briefings are recognised from the event description.')
    footnote = ("<b>What the record does not show.</b> Most trips are Aspen Institute Congressional Program conferences paid for by the foundations on the sponsor line; the programme takes no corporate money, and Anthropic, RAND and Coefficient Giving appear as speakers, not payers. Attending a briefing is not a transaction. Dollar values are not drawn because most filings give none. Staff trips are the office's, not the member's. Senate forms are scanned images, read by machine and then re-checked by hand.")
    figure(stem, "Travel and events: how the network appears", subtitle, "\n".join(svg), footnote, ids, height=1080 + 34 * len(mt) + 160 + 420,
           legend_html=legend([(DEM, "Democratic traveller"), (REP, "Republican traveller"), (IND, "independent"), (GREY, "party not recorded")]))


# ---------------------------------------------------------------- 16 member statements
def fig16():
    stem = "congress-16-member-statements"
    # 2026-09-23 (Codex X4c #3, X5a #1): a statement must name a network entity; a bill, a federal body or a concept on the entity cell is not one
    NET16 = re.compile(r"ANTHROPIC|AMODEI|\bRAND\b|CSET|SECURITY AND EMERGING|RESPONSIBLE INNOVATION|\bARI\b|OPEN PHILANTHROPY|COEFFICIENT|GOOD VENTURES|\bMETR\b|FATHOM|AMERICAN INNOVATION|FUTURE OF LIFE|\bFLI\b|PUBLIC FIRST|SCHMIDT|INSTITUTE FOR PROGRESS|FEDERATION OF AMERICAN SCIENTISTS|\bFAS\b|CENTER FOR AI SAFETY|\bCAIS\b|ENCODE|HORIZON INSTITUTE|TECHCONGRESS|GOVAI|GOVERNANCE OF AI|\bEPOCH\b|REDWOOD|\bMATS\b|PALISADE|SEEDAI|\bCNAS\b|NEW AMERICAN SECURITY|JACK CLARK|KAPLAN|MOSKOVITZ|TUNA|HASTINGS|TALLINN|MATHENY|CHRISTIANO|CARNEGIE ENDOWMENT|^S\d\d$", re.I)
    rows = [r for r in MS if ev(r) and r["member_bioguide"] in PARTY and any(NET16.search(e.strip()) for e in (r["entity_named"] or "").split(";"))]
    ids = [r["row_id"] for r in rows]
    def ent(r):
        e = (r["entity_named"] or "").strip()
        if not e:
            return "(organisation not recorded)"
        e = e.split(";")[0].strip()
        if e.upper().startswith("ANTHROPIC") or e in ("Amodei", "Dario Amodei"):
            return "Anthropic / Dario Amodei"
        if "RAND" in e:
            return "RAND Corporation"
        if re.match(r"^S\d\d$", e):
            return "other network organisation"
        return e[:40]
    def st(r):
        s = (r["stance"] or "").strip()
        return {"names": "names the entity", "warns": "warns", "calls_for_action": "calls for action", "mention_only_in_quoted_text": "mention only, in quoted text", "citation_or_appearance": "cites or hosts it", "": "stance not coded"}.get(s, s[:30])
    stances = [s for s, n in collections.Counter(st(r) for r in rows).most_common(6) if n >= 5]  # X39 E25: rarer stances fold into 'other coded stance'
    if any(st(r) not in stances for r in rows):
        stances.append("other coded stance")  # 2026-09-23 (Codex X5a #2): the bars sum to the whole row universe
    cells = collections.defaultdict(float)
    for r in rows:
        y = r["date"][:4]
        if y >= "2016":
            cells[(st(r) if st(r) in stances else "other coded stance", y)] += 1
    years = sorted({y for (_, y) in cells})
    SPAL = PAL[3:]  # stance colours stay off the party colours (blue, red, green) this figure also uses
    svg = [txt(40, 40, "Members naming a network organisation in public, by year and what the statement does (counts of statements, not dollars)", 24, weight="bold")]
    mx = max([sum(cells.get((s, y), 0) for s in stances) for y in years] + [1])
    for i, y in enumerate(years):
        x = 120 + i * 160; yy = 380
        for j, s in enumerate(stances):
            v = cells.get((s, y), 0); h = 280 * v / mx
            svg.append(f'<rect x="{x}" y="{yy-h:.1f}" width="100" height="{h:.1f}" fill="{SPAL[j % len(SPAL)]}"/>'); yy -= h
        svg.append(txt(x + 50, 404, y, 15, anchor="middle", fill=MUTED)); svg.append(txt(x + 50, yy - 6, str(int(sum(cells.get((s, y), 0) for s in stances))), 13, anchor="middle"))
    svg.append(txt(40, 460, "By the entity named, split by the speaker's party", 22, weight="bold")); svg.append(party_key(KEY_X, 460))
    ce = collections.defaultdict(float)
    for r in rows:
        ce[(PARTY.get(r["member_bioguide"], "?"), ent(r))] += 1
    ents = [e for e, _ in collections.Counter(ent(r) for r in rows).most_common()]  # X39-0671: every entity named at least once
    eh = 36 * len(ents) + 10
    svg.append(stacked_bars(ce, ["D", "R", "I", "?"], ents, 40, 480, 2000, eh, [DEM, REP, IND, GREY], label_w=620, fmt=lambda v: f"{int(v)}"))
    yv = 480 + eh + 30
    svg.append(txt(40, yv, "By venue", 22, weight="bold"))
    def venue(v):  # X33-083 (2026-09-29): raw venue strings mapped to a closed set before counting
        v = (v or "").lower()
        if "hearing" in v:
            return "hearing"
        if v in ("x", "twitter", "x.com") or v.startswith("x "):
            return "X"
        if "congressional" in v and "record" in v:
            return "Congressional Record"
        if re.search(r"press|site|\.gov|newsletter|statement", v):
            return "press release or member site"
        if "bill" in v or "report" in v:
            return "bill text or committee report"
        return "other"
    cv = collections.Counter(venue(r["venue"]) for r in rows)
    vrows = [(k, v, None) for k, v in cv.most_common()]
    svg.append(bar_chart(vrows, 40, yv + 20, 2000, 34 * len(vrows) + 40, label_w=620, colour=lambda r: NEUTRAL, fmt=lambda v: f"{int(v)}"))
    MIN_ST = 5  # X39-0713: the member panel ends at five statements; every member at the threshold is drawn
    bym = collections.Counter(r["member_bioguide"] for r in rows if r["member_bioguide"] in SIT)
    mrows = [(b, v) for b, v in bym.most_common() if v >= MIN_ST]
    ym = yv + 34 * len(vrows) + 110
    svg.append(txt(40, ym, f"Members with {MIN_ST} or more statements", 22, weight="bold")); svg.append(party_key(KEY_X, ym))
    svg.append(bar_chart([(member_label(b), v, SIT[b]) for b, v in mrows], 40, ym + 20, 2000, 34 * len(mrows) + 40, label_w=520, colour=lambda m: party_colour(m["party"]), fmt=lambda v: f"{int(v)}"))
    ids += [SIT[b]["row_id"] for b, _ in mrows]
    height = ym + 34 * len(mrows) + 120 + 420
    subtitle = ("Sources: hearing transcripts, committee reports, the Congressional Record, bill text, members' press releases and posts on X. Each statement is coded by what it does (names it, warns, calls for action and so on), not by whether it helps the company.")
    footnote = ('<b>What the record does not show.</b> Naming a company is not a connection to it: warnings, subpoenas and praise all count once. Transcripts were searched by name, so a member who never uses the names is absent, not silent. Posts on X were collected for some accounts only, and 2026 is over-represented. Reports and bill text are counted under the venue where they are hosted. Statements naming private individuals are left out.')
    figure(stem, "What members say about the network, in public", subtitle, "\n".join(svg), footnote, ids, height=height,
           legend_html=legend([(SPAL[j], s) for j, s in enumerate(stances)]))


# ---------------------------------------------------------------- 17 AI bills, 4a, fellows
def fig17():
    stem = "congress-17-ai-bills-fellows-and-lobbying-on-members-bills"
    cells = collections.defaultdict(float); ids = []
    for m in SITTING:
        p = (m["party"] or "?")[:1].upper()
        for col, lab in (("bills_restrict_n", "restrict or regulate AI"), ("bills_promote_n", "promote or fund AI"), ("bills_other_n", "other AI-related")):
            v = float(m[col] or 0)
            if v:
                cells[(p, lab)] += v; ids.append(m["row_id"])
    svg = [txt(40, 40, "AI bills sponsored by sitting members, by the bill's direction and the sponsor's party (counts of bills)", 24, weight="bold")]
    svg.append(stacked_bars(cells, ["D", "R", "I"], ["restrict or regulate AI", "promote or fund AI", "other AI-related"], 40, 60, 2000, 150, [DEM, REP, IND], label_w=520, fmt=lambda v: f"{int(v)} bills"))
    co = collections.Counter()
    for m in SITTING:
        n = int(float(m["bills_cosponsored_n"] or 0)); co[min(n, 6)] += 1
    svg.append(txt(40, 250, "How many AI bills each sitting member cosponsored", 22, weight="bold"))
    mx = max(co.values() or [1])
    for k in range(0, 7):
        x = 120 + k * 150; h = 160 * co.get(k, 0) / mx
        svg.append(f'<rect x="{x}" y="{440-h:.1f}" width="110" height="{h:.1f}" fill="{NEUTRAL if k else HELD}" rx="3"/>')  # X39-1022: one series, not a party
        svg.append(txt(x + 55, 464, f"{k}{'+' if k == 6 else ''}", 15, anchor="middle", fill=MUTED)); svg.append(txt(x + 55, 434 - h, str(co.get(k, 0)), 14, anchor="middle"))
    svg.append(txt(40, 520, "Network lobbying reports that name a bill the member sponsored (no money is attributed to the member)", 22, weight="bold"))
    y = 550
    for m in sorted(SITTING, key=lambda m: -int(float(m["lda_filings_naming_sponsored_bills_n"] or 0))):
        n = int(float(m["lda_filings_naming_sponsored_bills_n"] or 0))
        if not n:
            break
        lbs = m["lda_filings_naming_sponsored_bills_ids"].split()
        clients = collections.Counter(client_label(BY_ID[i]["client"]) for i in lbs if i in BY_ID)
        # only the sponsored bills that the matched filings name (Codex X1: the full sponsored list was shown before)
        sponsored = {bill_norm(b) for b in m["bills_sponsored"].split(";") if bill_norm(b)}
        named = set()
        for i in lbs:
            for tok in re.split(r"[;|,]", BY_ID.get(i, {}).get("bills_named") or ""):
                bn = bill_norm(tok)
                if bn and bn in sponsored:
                    named.add(bn)
        svg.append(f'<rect x="40" y="{y-14}" width="8" height="18" fill="{party_colour(m["party"])}"/>')
        bills = "; ".join(sorted(named)) or "(bill named on the filing not matched to the sponsored list)"
        svg.append(txt(56, y, f"{member_label(m['member_bioguide'])}: {n} filing{'s' if n != 1 else ''} naming {bills[:70]}{'…' if len(bills) > 70 else ''}", 15))
        svg.append(txt(760, y, "; ".join(f"{c} ({v})" for c, v in clients.most_common(4)), 14, fill=MUTED))
        ids += lbs; y += 26
    y += 30
    svg.append(txt(40, y, "Horizon Institute fellows placed in a sitting member's office (the fellows are paid by the Horizon programme, which network grants fund)", 22, weight="bold"))
    y += 30
    # X39-0807 (2026-10-11): from this pack's evidence placement rows, canonicalised as in figure 24, not the companion file
    hz = collections.defaultdict(list)
    for p in horizon_placements()[0]:
        if p["member_bioguide"] in SIT:
            hz[p["member_bioguide"]].append(p)
    for b, ps in sorted(hz.items(), key=lambda kv: (-len({p["person"] for p in kv[1]}), member_label(kv[0]))):
        m = SIT[b]; n = len({p["person"] for p in ps})
        svg.append(f'<rect x="40" y="{y-14}" width="8" height="18" fill="{party_colour(m["party"])}"/>')
        yrs = sorted({int(p["start"]) for p in ps if p["start"].isdigit()})  # X33-018/084: no fellow names or row ids drawn
        span = (f"placed {yrs[0]}" if yrs[0] == yrs[-1] else f"placed {yrs[0]}–{yrs[-1]}") if yrs else "start year not stated"
        svg.append(txt(56, y, f"{member_label(b)}: {n} fellow{'s' if n > 1 else ''}, {span}", 15)); y += 26
        ids += [i for p in ps for i in p["row_ids"]] + [m["row_id"]]
    subtitle = ("Sources: this project's companion study of AI bills (each bill's direction coded), Horizon Institute's own placement pages, and quarterly lobbying reports by network clients that name a bill the member sponsored.")
    footnote = ("<b>What the record does not show.</b> A bill's direction is a code for the bill, not a score of the sponsor. A lobbying report naming a bill says the client lobbied on it, not which way or whether the sponsor's office was contacted. A fellow is paid by the programme; the fellow and the office choose each other. A report that names a bill only by its title is not counted. Cosponsor counts cover AI bills in the companion study only.")
    figure(stem, "Members' bills, the lobbying that named them, and the fellows in their offices", subtitle, "\n".join(svg), footnote, ids, height=y + 420,
           legend_html=legend([(DEM, "Democratic sponsor"), (REP, "Republican sponsor"), (IND, "independent")]))


# ---------------------------------------------------------------- 18 lobbying bills and issues
FIRST_CONGRESS_YEAR = 1789  # the 1st Congress convened in 1789; Congress n spans years 1789+2(n-1) and the next


def bill_norm(s: str) -> str:
    if re.match(r"^\s*[HS]\.?\s?Amdt", s.strip(), re.I):
        return ""  # an amendment number is not a bill
    m = re.match(r"^\s*([HS])\.?\s?(R\.?|J\.?\s?RES\.?|CON\.?\s?RES\.?|RES\.?)?\s?(\d{1,5})\b", s.strip().upper())
    if not m:
        return ""
    ch, kind, num = m.group(1), (m.group(2) or "").replace(".", "").replace(" ", ""), m.group(3)
    kind = {"R": "R.", "JRES": "J.Res.", "CONRES": "Con.Res.", "RES": "Res."}.get(kind, "")
    return f"{ch}.{kind} {num}" if kind else f"{ch}. {num}"


def fig18():
    stem = "congress-18-lobbying-bills-and-issues"
    ld2 = [r for r in LB if ev(r) and r["filing_type"] == "LD-2" and "2016" <= (r["period"] or r["date"] or "")[:4] <= "2026"]
    # 2026-09-23 (Codex X3 #2): one filing counts once; rows restating a filing's bills under the same UUID collapse
    seen_u = set(); ld2u = []
    for r in sorted(ld2, key=lambda r: (len(r["row_id"]), r["row_id"])):
        u = re.search(r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", (r["url"] or "") + " " + (r["note"] or ""))  # 2026-09-23 (Codex X4d #1): UUID may sit in the note
        if not u:  # 2026-09-23 (Codex X4c #5): a row with no filing UUID (a client-name search summary) is not a filing
            continue
        if u.group(1) in seen_u:
            continue
        seen_u.add(u.group(1))
        ld2u.append(r)
    ld2 = ld2u
    ids = [r["row_id"] for r in ld2]  # X39-0912: every drawn filing is cited, so G1 measures all of them
    bills = collections.defaultdict(collections.Counter)
    def congress_of(r):  # X39 E27: a bill is a number in one Congress
        y = (r["period"] or r["date"] or "")[:4]
        return (int(y) - FIRST_CONGRESS_YEAR) // 2 + 1 if y.isdigit() else None
    for r in ld2:
        seen = set(); cg = congress_of(r)
        for tok in re.split(r"[;|,]", r["bills_named"] or ""):
            b = bill_norm(tok)
            if b and cg:
                b = f"{b} ({cg}th)"
            if b and b not in seen:
                seen.add(b); bills[b][client_label(r["client"])] += 1
    MIN_FILINGS = 3  # X39-0871: every bill named on three or more filings is drawn, ties included
    top = sorted(((b, c) for b, c in bills.items() if sum(c.values()) >= MIN_FILINGS), key=lambda kv: (-sum(kv[1].values()), kv[0]))
    svg = [txt(40, 40, "Bills most often named in network clients' lobbying reports, 2016–2026 (one count per report naming the bill)", 24, weight="bold")]
    clients_all = collections.Counter()
    for _, c in top:
        clients_all.update(c)
    cl = [c for c, _ in clients_all.most_common(8)]
    cells = {(c, b): float(cnt.get(c, 0)) for b, cnt in top for c in cl}
    th = 36 * len(top) + 10
    svg.append(stacked_bars(cells, cl, [b for b, _ in top], 40, 60, 2000, th, PAL, label_w=300, fmt=lambda v: f"{int(v)} filings"))
    yi = 60 + th + 40
    svg.append(txt(40, yi, f"Issue areas for the clients in the top panel (the issue codes the lobbying firms selected on {MIN_FILINGS} or more reports)", 22, weight="bold"))
    ic = collections.defaultdict(float)
    for r in ld2:
        for code in sorted(set(re.findall(r"\b([A-Z]{3})\s*:", r["issues"] or ""))):
            ic[(client_label(r["client"]), code)] += 1
    # 2026-11-26: the panel drew the twelve most frequent codes and five codes tied for the twelfth place, so which one was drawn changed from run to
    # run (set order). It now draws every code on MIN_FILINGS or more reports, ties included, as the bills panel does, most frequent first, then by code.
    code_n = {c: sum(v for (cc, c2), v in ic.items() if c2 == c and cc in cl) for (_, c) in ic}  # X33-085
    codes = [c for c, n in sorted(code_n.items(), key=lambda kv: (-kv[1], kv[0])) if n >= MIN_FILINGS]
    ih = 36 * len(codes) + 10
    svg.append(stacked_bars(ic, cl, codes, 40, yi + 20, 2000, ih, PAL, label_w=300, fmt=lambda v: f"{int(v)} filings"))
    y = yi + 20 + ih + 40
    svg.append(txt(40, y, "Who files for each network client: the client itself and its lobbying firms (number of quarterly reports)", 22, weight="bold"))
    rc = collections.Counter((client_label(r["client"]), re.sub(r"\s+", " ", (r["registrant"] or "?").strip())) for r in ld2)
    y += 30
    by_client = collections.defaultdict(list)
    for (c, reg), v in rc.most_common():
        by_client[c].append((reg, v))
    SHOW_FIRMS = 4  # X39-0888/0890/0898: full registrant names, never cut; the rest are counted, not dropped
    for c in cl:
        regs = by_client.get(c, [])
        parts = [f"{reg} ({v})" for reg, v in regs[:SHOW_FIRMS]]
        if len(regs) > SHOW_FIRMS:
            parts.append(f"and {len(regs) - SHOW_FIRMS} other{'s' if len(regs) - SHOW_FIRMS != 1 else ''}")
        lines, cur = [], ""
        for part in parts:  # wrap between firms, so no name is split
            nxt = f"{cur}; {part}" if cur else part
            if len(nxt) > 120 and cur:
                lines.append(cur + ";"); cur = part
            else:
                cur = nxt
        lines.append(cur)
        svg.append(txt(40, y, c, 15, weight="bold"))
        for ln in lines:
            svg.append(txt(640, y, ln, 14, fill=MUTED)); y += 22
        y += 6
    subtitle = ('Sources: quarterly Senate lobbying reports for network clients. Bill names are standardised from the report text; issue areas are the codes the lobbying firm chose.')
    footnote = ("<b>What the record does not show.</b> Naming a bill does not say whether the client supported or opposed it, only that it lobbied on it. Firms list every bill touched in a quarter, so spending and defense bills recur for reasons unrelated to AI. Client spellings are merged; reports before 2016 (RAND's and FAS's) are left out. Amended reports appear once.")
    figure(stem, "What the network lobbies on", subtitle, "\n".join(svg), footnote, ids, height=y + 420, legend_html=legend([(PAL[i], c) for i, c in enumerate(cl)]))


# ---------------------------------------------------------------- 19 AI vendors
def fig19():
    stem = "congress-19-ai-lab-vendors"
    def lab(p):
        p = p.upper()
        if "ANTHROPIC" in p or "CLAUDE" in p:
            return "Anthropic / Claude"
        if "OPENAI" in p or "CHATGPT" in p:
            return "OpenAI / ChatGPT"
        return ""
    rows = [r for r in VN if ev(r) and lab(r["payee"])]
    ids = [r["row_id"] for r in rows]
    def ptype(r):
        if "CHIEF ADMIN" in r["payer"].upper() or r["payer_type"] == "agency":
            return "House offices (Statement of Disbursements)"
        return {"candidate_committee": "candidate committees", "hybrid_pac": "hybrid PACs", "super_pac": "super PACs", "party_committee": "party committees", "leadership_pac": "leadership PACs", "nonconnected_pac": "nonconnected PACs", "corporate_pac": "corporate PACs", "": "committee type not recorded"}.get(r["payer_type"], r["payer_type"])
    cells = collections.defaultdict(float); cnt = collections.defaultdict(float)
    for r in rows:
        cells[(lab(r["payee"]), ptype(r))] += amt(r["amount_usd"]); cnt[(lab(r["payee"]), ptype(r))] += 1
    pts = [p for p, _ in collections.Counter({p: sum(v for (_, pp), v in cnt.items() if pp == p) for (_, p) in cnt}).most_common()]
    svg = [txt(40, 40, "Payments to AI labs by political committees and House offices, by kind of payer: dollars, then number of payments", 24, weight="bold")]
    svg.append(stacked_bars(cells, ["Anthropic / Claude", "OpenAI / ChatGPT"], pts, 40, 60, 1000, 300, [PAL[4], PAL[3]], label_w=420))
    svg.append(stacked_bars(cnt, ["Anthropic / Claude", "OpenAI / ChatGPT"], pts, 1080, 60, 1000, 300, [PAL[4], PAL[3]], label_w=420, fmt=lambda v: f"{int(v)} lines"))
    cy = collections.defaultdict(float)
    for r in rows:
        y = (r["date"] or "")[:4]
        if y.isdigit():
            cy[(lab(r["payee"]), y)] += amt(r["amount_usd"])
    years = sorted({y for (_, y) in cy})
    svg.append(txt(40, 400, "By year (dollars)", 22, weight="bold"))
    svg.append(stacked_bars(cy, ["Anthropic / Claude", "OpenAI / ChatGPT"], years, 40, 420, 2000, 200, [PAL[4], PAL[3]], label_w=300))
    pa = collections.Counter(); po = collections.Counter()
    for r in rows:
        (pa if lab(r["payee"]).startswith("Anthropic") else po)[(r["payer"] or "?")[:44]] += amt(r["amount_usd"])
    svg.append(txt(40, 660, f"Payers paying Anthropic the most (the {min(10, len(pa))} largest of {len(pa)})", 22, weight="bold"))  # X40-2975
    svg.append(bar_chart([(k, v, None) for k, v in pa.most_common(10)], 40, 680, 1000, 380, label_w=520, colour=lambda r: PAL[4]))
    svg.append(txt(1080, 660, f"Payers paying OpenAI the most (the {min(10, len(po))} largest of {len(po)})", 22, weight="bold"))
    svg.append(bar_chart([(k, v, None) for k, v in po.most_common(10)], 1080, 680, 1000, 380, label_w=520, colour=lambda r: PAL[3]))
    svg.append(txt(40, 1100, "Sitting members whose campaign committee or House office paid Anthropic", 22, weight="bold"))
    top = sorted([m for m in SITTING if float(m["t10_usd"] or 0) > 0], key=lambda m: -float(m["t10_usd"] or 0))  # X40-2974: every member with a counted payment
    mh = 34 * len(top) + 40
    svg.append(bar_chart([(member_label(m["member_bioguide"]), float(m["t10_usd"]), m) for m in top], 40, 1120, 2000, mh, label_w=520, colour=lambda m: party_colour(m["party"])))
    ids += [m["row_id"] for m in top]
    subtitle = ('Sources: FEC committee spending reports and House office spending reports where the payee is Anthropic, Claude, OpenAI or ChatGPT. OpenAI is shown for comparison; it is not network money.')
    footnote = ("<b>What the record does not show.</b> A subscription is a purchase, not a contribution, and the money flows from the committee to the lab. Card-processor descriptions are as printed and may bundle other charges. House office spending is the office's, not the member's. Committees that pay through a consultant do not appear. 2026 is still open and not every committee was searched, so counts are floors.")
    height = 2130
    ym = 1120  # top of the member panel
    if ym + mh + 540 > height:
        height = ym + mh + 540
    figure(stem, "Committees and offices buying from the AI labs", subtitle, "\n".join(svg), footnote, ids, height=height, legend_html=legend([(PAL[4], "Anthropic / Claude"), (PAL[3], "OpenAI / ChatGPT (comparison)")]))


# ---------------------------------------------------------------- 20 state money
def fig20():
    stem = "congress-20-state-money"
    rows = [r for r in SG if ev(r) and r["money_type"] in ("state_contribution", "lobbying_spend") and amt(r["amount_usd"]) > 0]
    # 2026-09-23 (Codex X4c #7): amendment versions of one California bulk-export transaction were set to context row by row against the
    # export's transaction ids (receipt codex-x4c-record-figures-2026-09-23.json); a same-day same-amount pair in one filing can be two
    # contributions (primary and general election), so no key collapse is applied here
    ids = [r["row_id"] for r in rows]
    def payer(r):
        n = (r["payer"] or "").upper()
        if "ANTHROPIC" in n:
            return "Anthropic PBC (lobbying and contributions)"
        if "HASTINGS" in n:
            return "Reed Hastings"
        if "TUNA" in n:
            return "Cari Tuna"
        if "MOSKOVITZ" in n:
            return "Dustin Moskovitz"
        if "FUTURE OF LIFE" in n:  # X33-022: an organisation, not an employee
            return "Future of Life Institute"
        if "ENCODE" in n:  # X33-023: one client under two spellings
            return "Encode AI Corporation"
        return public_name(r["payer"], r.get("payer_type", "")).replace("other individuals (not named)", "other network individuals (employees; not named)")
    def office(r):
        o = (r["office"] or "").strip()
        o = {"Member of Assembly": "State Assembly", "State Senate": "State Senate", "State Senator": "State Senate"}.get(o, o)
        return o or ("ballot measure / party / PAC" if re.search(r"PAC|FUND|COMMITTEE|PARTY|YES ON|NO ON|ACTBLUE", (r["payee"] or "").upper()) else "office not recorded")
    cells = collections.defaultdict(float)
    for r in rows:
        cells[(office(r), payer(r))] += amt(r["amount_usd"])
    payers = [p for p, _ in collections.Counter({p: sum(v for (_, pp), v in cells.items() if pp == p) for (_, p) in cells}).most_common(9)]
    offices = [o for o, _ in collections.Counter({o: sum(v for (oo, _), v in cells.items() if oo == o) for (o, _) in cells}).most_common(8)]
    # X40-1930/1931 (2026-10-11): the smaller kinds of office are one "other offices" segment, so each giver's label is its whole total
    if any(o not in offices for (o, _) in cells):
        folded = collections.defaultdict(float)
        for (o, p_), v in cells.items():
            folded[(o if o in offices else "other offices", p_)] += v
        cells = folded; offices = offices + ["other offices"]
    n_givers = len({p_ for (_, p_) in cells})
    svg = [txt(40, 40, f"State contributions and lobbying spend by network principals, Anthropic and its employees, by giver ({len(payers)} of {n_givers}) and the kind of office (the eight largest, then the rest together)", 24, weight="bold")]  # X40-1932
    svg.append(stacked_bars(cells, offices, payers, 40, 60, 2000, 360, PAL, label_w=620))
    cy = collections.defaultdict(float)
    for r in rows:
        # 2026-09-27 (Codex X25-038): a lobbying report's year is the period it covers, not the date it was filed
        yr = r["period"][:4] if r["money_type"] == "lobbying_spend" and re.match(r"\d{4}", r.get("period") or "") else (r["date"] or "")[:4]
        cy[(r["state"] or "?", yr)] += amt(r["amount_usd"])
    years = sorted({y for (_, y) in cy if y}); states = [s for s, _ in collections.Counter({s: sum(v for (ss, _), v in cy.items() if ss == s) for (s, _) in cy}).most_common(5)]
    if any(s_ not in states for (s_, _) in cy):  # X40-1933 (2026-10-11): the smaller states are one segment, so each year bar is the whole year
        _f = collections.defaultdict(float)
        for (s_, y_), v in cy.items():
            _f[(s_ if s_ in states else "other states", y_)] += v
        cy = _f; states = states + ["other states"]
    svg.append(txt(40, 450, "By year and state", 22, weight="bold"))
    svg.append(stacked_bars({(s, y): cy.get((s, y), 0.0) for s in states for y in years}, states, years, 40, 470, 2000, 300, PAL, label_w=200))
    bp = collections.Counter(); first = {}
    for r in rows:
        k = re.sub(r"[^A-Z0-9]", "", (r["payee"] or "?").upper())
        first.setdefault(k, re.sub(r"\s+", " ", (r["payee"] or "?").upper())[:50]); bp[first[k]] += amt(r["amount_usd"])
    svg.append(txt(40, 800, f"Recipients receiving the most (the {min(16, len(bp))} largest of {len(bp)}; committees and candidates as named on the state filing)", 22, weight="bold"))  # X40-1932
    svg.append(bar_chart([(k, v, None) for k, v in bp.most_common(16)], 40, 820, 2000, 600, label_w=760, colour=lambda r: PAL[6]))
    subtitle = ('Sources: California Secretary of State, New York State Board of Elections and other state records. Reed Hastings is shown as an Anthropic board member; employees are grouped into one line.')
    footnote = ('<b>What the record does not show.</b> State giving goes to state officials and ballot campaigns, not to Congress; it links to a member only where the state official later won a House or Senate seat (three sitting members). ActBlue California passes money through; it is not a recipient. A contribution is not a vote. Coverage is mostly California; other states were sampled.')
    figure(stem, "State money", subtitle, "\n".join(svg), footnote, ids, height=1900, legend_html=legend([(PAL[i], o) for i, o in enumerate(offices)]))


# ---------------------------------------------------------------- 21 grants layer
def fig21():
    stem = "congress-21-grants-to-intermediaries"
    # 2026-09-23 (Codex X4c #10, lane C131): a 990-PF line 'approved for future payment' is a commitment, not a payment; it is held out of the bars and totalled in the footnote
    fut = [r for r in GR if ev(r) and amt(r["amount_usd"]) > 0 and "990_group=approved_future" in (r["note"] or "")]
    rows = [r for r in GR if ev(r) and amt(r["amount_usd"]) > 0 and "990_group=approved_future" not in (r["note"] or "")]
    # X53 (2026-10-11): a tax-return payment that may restate a counted award, identity neither proven nor disproven, is shown
    # apart and never added to the award (research/grant_payment_unproven.csv)
    _unp = {r["row_id"] for r in load("grant_payment_unproven")}
    apart = [r for r in rows if r["row_id"] in _unp]
    rows = [r for r in rows if r["row_id"] not in _unp]
    ids = [r["row_id"] for r in rows] + [r["row_id"] for r in apart]
    def funder(r):
        n = (r["payer"] or "").upper()
        if "TALLINN" in n or "SFF" in n or "SURVIVAL" in n:
            return "Jaan Tallinn / Survival and Flourishing Fund"
        if "COEFFICIENT" in n or "OPEN PHIL" in n and "ACTION" not in n:
            return "Coefficient Giving (Open Philanthropy)"
        if "OPEN PHILANTHROPY ACTION" in n:
            return "Open Philanthropy Action Fund (advocacy arm)"
        if "GOOD VENTURES" in n:
            return "Good Ventures Foundation"
        if "FUTURE OF LIFE" in n:
            return "Future of Life Institute"
        if "SCHMIDT" in n:
            return "Schmidt funds"
        if "MCCALEB" in n:
            return "Jed McCaleb"
        return public_name(r["payer"], r.get("payer_type", ""))
    # 2026-09-27 (Kevin): grants split by cause; the top panel and the grantee ranking are the network's AI, technology,
    # biosecurity and catastrophic-risk work, and the second panel is the same funders' grants to every other cause
    ai_rows = [r for r in rows if cause_of(r) == "ai_tech_biosecurity_gcr"]
    other_rows = [r for r in rows if cause_of(r) != "ai_tech_biosecurity_gcr"]
    def yr(r):
        return (r["date"] or r["fiscal_year"] or "")[:4]
    cells = collections.defaultdict(float)
    for r in ai_rows:
        if "2015" <= yr(r) <= "2026":
            cells[(funder(r), yr(r))] += amt(r["amount_usd"])
    funders = [f for f, _ in collections.Counter({f: sum(v for (ff, _), v in cells.items() if ff == f) for (f, _) in cells}).most_common(7)]
    years = [str(y) for y in range(2015, 2027)]
    svg = [txt(40, 40, "Grants for AI, technology, biosecurity and catastrophic-risk work, by the seven largest network funders, by year", 24, weight="bold")]
    svg.append(stacked_bars({(f, y): cells.get((f, y), 0.0) for f in funders for y in years}, funders, years, 40, 60, 2000, 420, PAL, label_w=200))
    ocols = ["#8c6d46", "#7a5195", "#5b8c3a", "#c0392b", "#2c6fbb", "#d4a72c", "#e8a09a", "#9a9a9a", "#bdbdbd"]
    causes = [c for c in CAUSE_LABEL if c != "ai_tech_biosecurity_gcr"]
    ocells = collections.defaultdict(float)
    for r in other_rows:
        if "2015" <= yr(r) <= "2026":
            ocells[(cause_of(r), yr(r))] += amt(r["amount_usd"])
    causes = [c for c in causes if any(ocells.get((c, y)) for y in years)]
    svg.append(txt(40, 510, "The same funders' grants to other causes, by cause and year", 22, weight="bold"))
    svg.append(stacked_bars({(c, y): ocells.get((c, y), 0.0) for c in causes for y in years}, causes, years, 40, 530, 2000, 420, ocols, label_w=200))
    for i, c in enumerate(causes):  # four legend entries per row
        lx, ly = 240 + (i % 4) * 470, 962 + (i // 4) * 28
        svg.append(f'<rect x="{lx}" y="{ly}" width="16" height="16" fill="{ocols[i % len(ocols)]}"/>')
        svg.append(txt(lx + 22, ly + 14, CAUSE_LABEL[c], 15))
    _gh = len(svg); svg.append("")  # heading filled once the grantee count is known (X40-2978)
    bg = collections.Counter(); gfirst = {}
    def gkey(v):
        return re.sub(r"(GROUP)?(AI)?$", "", re.sub(r"(INC|LLC|CORPORATION)$", "", re.sub(r"^THE", "", re.sub(r"[^A-Z0-9]", "", (v or "?").upper()))))  # 2026-09-27: "Redwood Research Group Inc." and "Epoch AI" are the same grantees as "Redwood Research" and "Epoch"
    for r in ai_rows:
        k = gkey(r["payee"]); gfirst.setdefault(k, re.sub(r"\s+", " ", r["payee"] or "?")[:54]); bg[gfirst[k]] += amt(r["amount_usd"])
    svg[_gh] = txt(40, 1080, f"Grantees receiving the most for AI, technology, biosecurity and catastrophic-risk work (the {min(18, len(bg))} largest of {len(bg)}; all funders)", 22, weight="bold")
    svg.append(bar_chart([(k, v, None) for k, v in bg.most_common(18)], 40, 1100, 2000, 660, label_w=760, colour=lambda r: PAL[4]))
    _mh = len(svg); svg.append("")
    mf = [r for r in rows if (r["member_facing_function"] or "").strip()]
    cm = collections.Counter()
    mfirst = {}
    for r in mf:
        k = gkey(r["payee"]); mfirst.setdefault(k, re.sub(r"\s+", " ", r["payee"] or "?")[:44]); cm[(mfirst[k], funder(r)[:34])] += amt(r["amount_usd"])
    svg[_mh] = txt(40, 1790, f"Grants to member-facing work (fellowships in offices, Hill programmes, advocacy), every cause (the {min(12, len(cm))} largest grantee-funder pairs of {len(cm)})", 22, weight="bold")
    svg.append(bar_chart([(f"{p}  ←  {f}", v, None) for (p, f), v in cm.most_common(12)], 40, 1810, 2000, 460, label_w=900, colour=lambda r: PAL[6]))
    subtitle = ("Sources: IRS Form 990 grant schedules, the funders' own published grant lists (Coefficient Giving, SFF, FLI) and one group's reports to Congress. Amounts are as filed or published.")
    footnote = (f"<b>What the record does not show.</b> A grant to an organisation is not money to a member; no grant in the record reaches a member's office directly (fellowship placements are in figure 24). The largest grantees are research groups; the chart does not measure whether their work reaches Congress. Each grant is placed in one cause by what it paid for, from its stated purpose, its grant page or the recipient's own mission. Grants approved for future years are left out. Where a funder's tax return lists a payment that may be the same money as a published award drawn here, and no document settles it, the award is drawn and the payment is not added: {len(apart)} such payment{'s' if len(apart) != 1 else ''}, {money(sum(amt(r["amount_usd"]) for r in apart))}{' in all' if len(apart) != 1 else ''}. Grant lists lag and tax filings arrive a year late, so 2025–2026 are floors. Open Philanthropy's grants appear under its new name, Coefficient Giving.")
    figure(stem, "The grants layer", subtitle, "\n".join(svg), footnote, ids, height=2720, legend_html=legend([(PAL[i], f) for i, f in enumerate(funders)]))


# ---------------------------------------------------------------- 22 network roster
def fig22():
    stem = "congress-22-network-roster"
    ents = {}
    for r in EN:
        if ev(r) and r["tier"] in ("T1", "T2", "T3", "T4", "T5") and r["name"].strip():
            k = (r["tier"], r["name"].strip().lower())
            ents.setdefault(k, {"name": r["name"].strip(), "tier": r["tier"], "type": r["entity_type"] or "", "ids": [], "rows": collections.Counter()})
            ents[k]["ids"].append(r["row_id"])
    idset = {i for e in ents.values() for i in e["ids"]}
    by_id = {i: k for k, e in ents.items() for i in e["ids"]}
    by_name = {}
    for k, e in ents.items():
        by_name.setdefault(norm_name(e["name"]) if e["type"] == "person" else re.sub(r"[^A-Z0-9]", "", e["name"].upper()), k)
    TABLES = [("HM", HM, "payer"), ("SP", SP, "payer"), ("LC", LC, "payer"), ("VN", VN, "payer"), ("GR", GR, "payer"), ("SG", SG, "payer"), ("TV", TV, "sponsor"), ("MS", MS, "entity_named"), ("RD", RD, "org_now"), ("FG", FG, "recipient"), ("LB", LB, "client")]
    for tab, rows, col in TABLES:
        for r in rows:
            if not ev(r):
                continue
            k = by_id.get((r.get("entity_id") or "").strip())
            if not k:
                v = r.get(col) or ""
                k = by_name.get(norm_name(v)) or by_name.get(re.sub(r"[^A-Z0-9]", "", v.upper()))
            if k:
                ents[k]["rows"][tab] += 1
    order = {"T1": 0, "T2": 1, "T3": 2, "T4": 3, "T5": 4}
    items = sorted(ents.values(), key=lambda e: (order[e["tier"]], -sum(e["rows"].values()), e["name"]))
    cand = [e for e in items if e["tier"] in ("T1", "T2", "T3", "T5") or sum(e["rows"].values()) > 0]
    # X33-087: every tier drawn; T5 holds only private individuals (large donors), who are counted, not named (2026-09-29)
    PER_TIER = 14  # X40-2981 (2026-10-11): about fourteen per tier, extended so the cut never splits a tie in record counts
    def _keep(lst):
        if len(lst) <= PER_TIER:
            return lst
        floor = sum(lst[PER_TIER - 1]["rows"].values())
        return [x for i, x in enumerate(lst) if i < PER_TIER or sum(x["rows"].values()) == floor]
    shown = [e for tier in ("T1", "T2", "T3", "T4") for e in _keep([x for x in cand if x["tier"] == tier])]
    tabs = [t for t, _, _ in TABLES]
    x0, y0, rh = 40, 110, 22
    svg = [txt(x0, 40, "The network by tier, and the confirmed records each member appears on (as giver, sponsor, client, employer or named organisation)", 23, weight="bold"),
           txt(x0, 70, "T1 funders of Anthropic or the AI-safety field, and vehicles they control · T2 their grantmaking arms · T3 Anthropic, its leaders, lobbyists and political vehicles · T4 network-funded groups that work with Congress · T5 large donors (T6 network grantees with no congressional role are not shown)", 16, fill=MUTED)]
    for j, t in enumerate(tabs):
        svg.append(txt(x0 + 760 + j * 95, y0 - 10, {"HM": "donations", "SP": "super PACs", "LC": "lobbyists", "VN": "AI vendor", "GR": "grants", "SG": "state", "TV": "travel", "MS": "statements", "RD": "jobs", "FG": "federal", "LB": "lobbying"}.get(t, t), 13, anchor="middle", fill=MUTED, weight="bold"))
    svg.append(txt(x0 + 760 + len(tabs) * 95 + 30, y0 - 10, "total", 14, fill=MUTED, weight="bold"))
    ids = []
    for i, e in enumerate(shown):
        y = y0 + i * rh
        if i % 2 == 0:
            svg.append(f'<rect x="{x0}" y="{y}" width="2060" height="{rh}" fill="#efece4"/>')
        svg.append(txt(x0 + 6, y + 16, e["tier"], 14, weight="bold", fill=PAL[order[e["tier"]]]))
        svg.append(txt(x0 + 50, y + 16, f"{e['name'][:60]}", 15)); svg.append(txt(x0 + 600, y + 16, e["type"], 13, fill=MUTED))
        for j, t in enumerate(tabs):
            n = e["rows"].get(t, 0)
            if n:
                svg.append(txt(x0 + 760 + j * 95, y + 16, f"{n:,}", 13, anchor="middle"))
        svg.append(txt(x0 + 760 + len(tabs) * 95 + 30, y + 16, f"{sum(e['rows'].values()):,}", 14, weight="bold"))
        ids += e["ids"]
    rest = [e for e in items if e not in shown]
    by_tier = collections.Counter(e["tier"] for e in rest); with_rows = sum(1 for e in rest if sum(e["rows"].values()) > 0)
    svg.append(txt(x0, y0 + len(shown) * rh + 24, f"{len(rest)} further network entities (people and organisations; T5's large donors are private individuals and are counted, not named) are not shown (" + ", ".join(f"{v} {k}" for k, v in sorted(by_tier.items())) + f"); {with_rows} of them appear in the records and {len(rest) - with_rows} do not.", 15, fill=MUTED))
    subtitle = ("Sources: the study's list of network organisations and people, matched to their FEC, lobbying, tax and congressional identifiers, and counted against every confirmed record by identifier or exact name. Tiers follow the study's written roster criteria (documented money, control, roles and a congressional function).")
    footnote = ("<b>What the record does not show.</b> A record count shows how much was found, not importance: Jaan Tallinn's count comes from a published grant list; a person whose giving runs through a group that does not disclose donors has a low count. Names are matched exactly, so unusual spellings are undercounted. A tier is a documented relationship under written criteria, not a finding about conduct; namesakes found by employer and city are left out.")
    figure(stem, "Who the network is, and where each appears", subtitle, "\n".join(svg), footnote, ids, height=y0 + len(shown) * rh + 520)


# ---------------------------------------------------------------- 23 record composition
def fig23():
    stem = "congress-23-record-composition"
    tabs = [("hard_money", HM), ("super_pac_c4", SP), ("lobbyist_contributions", LC), ("vendors", VN), ("member_statements", MS), ("entities", EN), ("lobbying", LB), ("grants", GR), ("state_government", SG), ("travel", TV), ("revolving_door", RD), ("timeline", TL), ("member_disclosures", PD), ("federal_money", FG)]
    PLAIN = {"hard_money": "Campaign contributions", "super_pac_c4": "Super PACs and nonprofits", "lobbyist_contributions": "Lobbyists' own gifts", "vendors": "Payments to AI labs", "member_statements": "Members' statements",
             "entities": "Network list", "lobbying": "Lobbying reports", "grants": "Grants", "state_government": "State money", "travel": "Travel and events", "revolving_door": "Job moves", "timeline": "Timeline events",
             "member_disclosures": "Financial disclosures", "federal_money": "Federal money"}
    cells = {}; tot = collections.Counter(); ids = []
    for name, rows in tabs:
        c = collections.Counter(ROLE.get(r["row_id"], "unbound") for r in rows)
        for k, v in c.items():
            cells[(k, PLAIN[name])] = float(v); tot[k] += v
    roles = ["evidence", "context", "negative", "unbound"]
    svg = [txt(40, 40, "Every record in the study, by source and how it was classified (counts)", 24, weight="bold")]
    svg.append(stacked_bars(cells, roles, [PLAIN[n] for n, _ in tabs], 40, 60, 2000, 560, [DEM, GREY, REP, "#e3dfd5"], label_w=420, fmt=lambda v: f"{int(v):,}"))
    svg.append(txt(40, 660, "What the classes mean", 22, weight="bold"))
    lines = [f"confirmed ({tot['evidence']:,} records): checked against the original filing or page; the connection and money figures use only these.",
             f"held but not counted ({tot['context']:,}): a duplicate copy of a record already held, a restatement, a namesake, or a record that could not be tied to a person; kept for reference, never counted.",
             f"searched, nothing found ({tot['negative']:,}): one line per search that came back empty; the record of what was looked for.",
             f"not yet classified ({tot['unbound']:,}): timeline copies and statements still awaiting a match to a member."]
    for i, l in enumerate(lines):
        svg.append(txt(40, 690 + i * 26, l, 15, fill=MUTED))
    # 2026-09-20 correction: the first rule matched "429" and "gap" anywhere in the note, so genuine none-found rows that say
    # "Not a 429" / "Not a fetch_gap", or that cite a lane named "...gaps-after-429", were counted as gaps (1,902 instead of ~240).
    neg_re = re.compile(r"not a fetch[_ ]gap|not=fetch_gap|not a 429|genuine empty|recoded_from_false_cloudflare_wall|closes=", re.I)  # 2026-09-24 (Codex X8b): explicit no-gap markers
    pos_re = re.compile(r"source_type=fetch_gap|\bfetch[_ ]gap\b|HTTP[ =]?(403|429|5\d\d)|status[ =:]?(403|429|5\d\d)|rate[- ]limit(ed)?|timed out|timeout|cloudflare|incapsula|captcha|OVER_RATE_LIMIT", re.I)
    closed = set()
    for name, rows in tabs:
        for r in rows:
            closed.update(re.findall(r"closes=\w+#([A-Z]{2}\d+)", r.get("note") or ""))
    gaps = collections.Counter()
    for name, rows in tabs:
        if name == "timeline":
            continue  # timeline rows restate gaps recorded in their source tables
        for r in rows:
            if ROLE.get(r["row_id"]) not in ("negative", "context"):
                continue
            n = re.sub(r"lane=research/grok-out/\S+", "", r.get("note") or "")
            if r["row_id"] in closed:
                continue  # a later re-pull row carries closes=<table>#<row_id>
            if (r.get("source_type") or "").lower() == "fetch_gap" or (pos_re.search(n) and not neg_re.search(n)):
                gaps[name] += 1
                ids.append(r["row_id"])  # the lower panel draws these gap rows; the upper panel counts every row
    svg.append(txt(40, 820, "Searches that could not be completed (the website blocked the request, limited it or timed out) and were never successfully repeated", 22, weight="bold"))
    svg.append(bar_chart([(PLAIN[k], v, None) for k, v in gaps.most_common(10)], 40, 840, 2000, 360, label_w=420, colour=lambda r: REP, fmt=lambda v: f"{int(v):,} search{'es' if int(v) != 1 else ''}"))
    subtitle = ('Sources: every record in the study, by how the reviewers classified it after checking it against the original. The connection and money figures use confirmed records only; figures 07, 22 and this one describe the record itself.')
    footnote = ('<b>What the record does not show.</b> Counts measure how much was collected, not the size of any connection: one super PAC can file tens of thousands of lines, while one career is one record. An empty search rules out only what was searched. One machine-reading pass over scanned Senate forms was discarded and redone.')
    figure(stem, "What the record is made of", subtitle, "\n".join(svg), footnote, ids, height=1650, legend_html=legend([(DEM, "confirmed"), (GREY, "held but not counted"), (REP, "searched, nothing found"), ("#e3dfd5", "not yet classified")]))


# ---------------------------------------------------------------- 24 fellowship pipeline
import build_figures as _bf  # noqa: E402


def person_stem(name: str) -> str:
    """One person per first-name stem and surname (Codex X1b #7): Max Katz and Maximilian Peter Katz are one key."""
    toks = [t for t in re.split(r"[\s,.]+", (name or "").lower()) if t and len(t) > 1 and t not in ("jr", "sr", "ii", "iii")]
    return (toks[0][:3] + " " + toks[-1]) if len(toks) >= 2 else " ".join(toks)


def horizon_placements():
    """Horizon fellows' host placements from this pack's evidence rows, as the programme's own roster lists them
    (record=programme_placement), one per (person, host office or committee), earliest start. TechCongress is context
    under the roster criteria (Kevin, 2026-10-11, E6) and is excluded from every network total (X39-0925)."""
    rd_rows = [r for r in RD if ev(r) and r["direction"] == "network->hill" and "record=programme_placement" in (r["note"] or "")
               and "horizon" in (r["prior_org"] or "").lower()]
    plc = {}
    for r in rd_rows:
        host = _bf.host_key(r["org_now"], r["member_bioguide"])  # X33-024 (2026-09-29): one host per office or committee, whatever the spelling
        k = (person_stem(r["person"]), host)
        st_full = (r["start"] or r["date"] or "").strip()
        if k not in plc or (st_full and (not plc[k]["start_full"] or st_full < plc[k]["start_full"])):  # 2026-09-24 (Grok A9 #20): the earliest full date decides, the year is drawn
            plc[k] = {"person": k[0], "host": host, "start": st_full[:4], "start_full": st_full, "member_bioguide": r["member_bioguide"], "row_ids": []}
    for r in rd_rows:
        plc[(person_stem(r["person"]), _bf.host_key(r["org_now"], r["member_bioguide"]))]["row_ids"].append(r["row_id"])
    return list(plc.values()), [r["row_id"] for r in rd_rows]


PAYROLL_SOURCES = ("house_sod", "senate_exp", "senate_secretary")  # House statements of disbursements; Senate expense and Secretary reports


def fig24():
    stem = "congress-24-fellowship-pipeline"
    rows, ids = horizon_placements()
    fellows = {r["person"] for r in rows}
    # X39-0995: a payroll record "also exists" only where an evidence payroll row names the same person and records Horizon as the prior post
    pay = {person_stem(r["person"]): r["row_id"] for r in RD if ev(r) and r["source_type"] in PAYROLL_SOURCES and "horizon" in (r["prior_org"] or "").lower()}
    matched = sorted(f for f in fellows if f in pay)
    ids += [pay[f] for f in matched]
    yc = collections.Counter(r["start"] for r in rows if r["start"].isdigit() and r["start"] >= "2016")
    svg = [txt(40, 40, f"Horizon Institute fellows placed in congressional offices, by start year ({len(rows)} placements of {len(fellows)} fellows, as the programme's roster lists them)", 24, weight="bold")]
    svg.append(bar_chart([(y, v, None) for y, v in sorted(yc.items())], 40, 60, 2000, 34 * len(yc) + 40, label_w=200, colour=lambda r: NEUTRAL, fmt=lambda v: f"{int(v)} placements"))
    yp = 60 + 34 * len(yc) + 80
    svg.append(txt(40, yp, "By the host's party (committee placements have no single party)", 22, weight="bold")); svg.append(party_key(KEY_X, yp))
    hp = collections.Counter(PARTY.get(r["member_bioguide"], "") for r in rows)
    plab = {"D": "Democrat", "R": "Republican", "I": "independent", "": "committee or office (no single party)"}
    svg.append(bar_chart([(plab.get(k, k), v, k) for k, v in hp.most_common()], 40, yp + 20, 2000, 34 * len(hp) + 40, label_w=520, colour=lambda k: party_colour(k), fmt=lambda v: f"{int(v)}"))
    yh = yp + 20 + 34 * len(hp) + 80
    MIN_HOST = 2  # X39-0990: cutoff derived from the Horizon-only rows; after E6 no host has four, so the panel shows every host with more than one, ties included
    ho = [(k, v) for k, v in collections.Counter(r["host"] or "(office not recorded)" for r in rows).most_common() if v >= MIN_HOST]
    svg.append(txt(40, yh, "Host offices and committees with more than one placement", 22, weight="bold"))
    svg.append(bar_chart([(k, v, None) for k, v in ho], 40, yh + 20, 2000, 34 * len(ho) + 40, label_w=900, colour=lambda r: NEUTRAL, fmt=lambda v: f"{int(v)}"))
    height = yh + 20 + 34 * len(ho) + 120 + 420
    subtitle = (f"Sources: Horizon Institute placement pages and alumni lists; a House or Senate payroll record also exists for {len(matched)} of the {len(fellows)} fellows. "
                "Horizon Institute is funded in part by network grants (see figure 21); TechCongress is excluded as context under the roster criteria.")
    footnote = ("<b>What the record does not show.</b> A fellow and a host office choose each other; the programme pays the stipend and the office directs the work. Placement lists name the office as of the fellowship year. Horizon also has funders outside the network, so a placement is a programme connection, not a principal's. Fellows with no start date are left out of the first panel.")
    figure(stem, "The fellowship pipeline into offices", subtitle, "\n".join(svg), footnote, ids, height=height)


# ---------------------------------------------------------------- 25 IE for and against members
def fig25():
    stem = "congress-25-ie-for-and-against-members"
    sup = sorted([m for m in SITTING if float(m["t3b_support_usd"] or 0) > 0], key=lambda m: -float(m["t3b_support_usd"]))[:18]
    opp = sorted([m for m in SITTING if float(m["t3b_oppose_usd"] or 0) > 0], key=lambda m: -float(m["t3b_oppose_usd"]))[:18]
    ids = [m["row_id"] for m in sup + opp]
    tot = collections.defaultdict(float); n = collections.Counter()
    for m in SITTING:
        p = (m["party"] or "?")[:1].upper()
        tot[("support", p)] += float(m["t3b_support_usd"] or 0); tot[("oppose", p)] += float(m["t3b_oppose_usd"] or 0)
        if float(m["t3b_support_usd"] or 0) > 0: n[("support", p)] += 1
        if float(m["t3b_oppose_usd"] or 0) > 0: n[("oppose", p)] += 1
    svg = [txt(40, 40, "Super PAC spending for and against sitting members, by committees that received network money (the committee's total spending on that member)", 24, weight="bold")]
    svg.append(txt(40, 80, "  ".join(f"{'for' if s == 'support' else 'against'} {'Democrats' if p == 'D' else 'Republicans' if p == 'R' else 'independents'}: {money(tot[(s, p)])} across {n[(s, p)]} members" for s in ("support", "oppose") for p in ("D", "R", "I") if tot[(s, p)]), 16, fill=MUTED))
    svg.append(txt(40, 130, f"Most spent in support (the {len(sup)} largest of {sum(1 for m in SITTING if float(m['t3b_support_usd'] or 0) > 0)} members)", 22, weight="bold"))  # X40-2619
    svg.append(bar_chart([(member_label(m["member_bioguide"]), float(m["t3b_support_usd"]), m) for m in sup], 40, 150, 1000, 700, label_w=440, colour=lambda m: party_colour(m["party"])))
    svg.append(txt(1080, 130, f"Most spent against (the {len(opp)} largest of {sum(1 for m in SITTING if float(m['t3b_oppose_usd'] or 0) > 0)} members)", 22, weight="bold"))
    svg.append(bar_chart([(member_label(m["member_bioguide"]), float(m["t3b_oppose_usd"]), m) for m in opp], 1080, 150, 1000, 700, label_w=440, colour=lambda m: party_colour(m["party"])))
    subtitle = ('Sources: FEC outside-spending reports, added up per member, from committees the network gave money to (SMP, House Majority PAC, LCV Victory Fund, Priorities USA Action, FF PAC, MoveOn, the Public First family and others; see figure 09).')
    footnote = ("<b>What the record does not show.</b> This is the committees' money, most of it not from the network: SMP and House Majority PAC raise from thousands of donors, and the network's share is in figure 09. Outside spending is not coordination with the member supported, and a member attacked received nothing. Spending against an opponent counts as support only where the filing names the member. Records that could not be confirmed are left out.")
    figure(stem, "Outside spending for and against members", subtitle, "\n".join(svg), footnote, ids, height=1350, legend_html=legend([(DEM, "Democrat"), (REP, "Republican"), (IND, "independent")]))


ALL = {"congress-08-member-type-heatmap": fig08, "congress-09-ie-committees-and-network-receipts": fig09, "congress-10-lobbyists-own-contributions": fig10, "congress-11-corporate-pacs": fig11,
       "congress-12-outside-money-flows": fig12, "congress-13-hard-money-by-vehicle-and-recipient": fig13, "congress-14-dollars-by-cycle-and-type": fig14, "congress-15-travel-and-events": fig15,
       "congress-16-member-statements": fig16, "congress-17-ai-bills-fellows-and-lobbying-on-members-bills": fig17, "congress-18-lobbying-bills-and-issues": fig18, "congress-19-ai-lab-vendors": fig19,
       "congress-20-state-money": fig20, "congress-21-grants-to-intermediaries": fig21, "congress-22-network-roster": fig22, "congress-23-record-composition": fig23,
       "congress-24-fellowship-pipeline": fig24, "congress-25-ie-for-and-against-members": fig25}

if __name__ == "__main__":
    want = sys.argv[1:] or list(ALL)
    for stem in want:
        ALL[stem]()
