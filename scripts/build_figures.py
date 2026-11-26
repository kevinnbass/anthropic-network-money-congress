#!/usr/bin/env python3
"""S9 figures (PLAN.md §4): decided after the join. Each figure carries the plain source line, no motive, no
two-sides framing, and a footnote stating what the record does not show. Row ids cited in a hidden comment so
`casework verify` and scripts/audit.py can resolve every citation. Renders HTML + PNG + JPG into figures/.

Usage: python3 scripts/build_figures.py [stem ...]   (no args = all)
"""
from __future__ import annotations
import csv, json, re, sys, collections, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from casework.figures.common import shell, render, esc, money, hidden_rows, legend  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "research"
OUT = ROOT / "figures"
KICKER = "Anthropic's network and Congress"
NOW = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
INK, MUTED = "#191b1a", "#666960"
DEM, REP, IND, GREY = "#2f5fa8", "#b8322a", "#6a8f3a", "#b9bbb3"
PAL = ["#2f5fa8", "#b8322a", "#6a8f3a", "#c98a1c", "#7a4fa3", "#1f8a8a", "#a3573a", "#4b6b8a", "#8a8a2a", "#c25b8a", "#3a7a5a", "#8a4b2a"]
TYPES = ["1", "2", "3a", "3b", "4a", "4b", "5", "6", "7", "8", "9", "10", "11", "12"]
TYPE_LABEL = {"1": "Direct contributions from network people", "2": "Contributions from network PACs (and one lobbying firm's PAC)", "3a": "Network money into super PACs and nonprofits", "3b": "Super PAC spending for or against (indirect)",
              "4a": "Lobbying reports naming the member's bill", "4b": "Lobbyists' own contributions (indirect)", "5": "Staff and fellows moving to or from the Hill", "6": "Network grants to think tanks and advocacy groups",
              "7": "Federal money to the network", "8": "Holdings and household income", "9": "Travel and events", "10": "Campaigns buying from AI labs", "11": "Public statements naming the network", "12": "State-level money"}


def load(name: str) -> list[dict[str, str]]:
    with open(R / f"{name}.csv", encoding="utf-8", errors="replace", newline="") as fh:
        return list(csv.DictReader(l for l in fh if not l.startswith("#")))


def roles() -> dict[str, str]:
    case = json.load(open(ROOT / "case.json", encoding="utf-8"))
    out: dict[str, str] = {}
    for cl in case["claims"]:
        for el in cl.get("elements", []):
            for b in el.get("bindings", []):
                if out.get(b["row_id"]) != "evidence":
                    out[b["row_id"]] = b.get("role", "evidence")
    return out


ROLE = roles()
ev = lambda r: ROLE.get(r["row_id"]) == "evidence"  # noqa: E731


def amt(v: str) -> float:
    try:
        return float((v or "0").replace(",", "").replace("$", "") or 0)
    except ValueError:
        return 0.0


def party_colour(p: str) -> str:
    return {"D": DEM, "R": REP, "I": IND, "ID": IND}.get((p or "").strip().upper(), GREY)


def txt(x, y, s, size=18, anchor="start", weight="normal", fill=INK, extra=""):
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}" fill="{fill}" {extra}>{esc(s)}</text>'


def bar_chart(rows, x0, y0, w, h, label_w=520, colour=lambda r: DEM, fmt=money, title="", label_max=64):
    """rows: list of (label, value, row). Horizontal bars."""
    if not rows:
        return txt(x0, y0 + 30, "none found in the record", 20, fill=MUTED)
    mx = max(v for _, v, _ in rows) or 1
    bh = min(34, (h - 40) / max(1, len(rows)))
    out = [txt(x0, y0, title, 22, weight="bold")] if title else []
    for i, (lab, v, r) in enumerate(rows):
        y = y0 + 20 + i * bh
        bw = (w - label_w - 200) * v / mx
        out.append(txt(x0 + label_w - 14, y + bh * 0.72, lab[:label_max], 17, anchor="end"))
        out.append(f'<rect x="{x0+label_w}" y="{y+2}" width="{max(2,bw):.1f}" height="{bh-6:.1f}" fill="{colour(r)}" rx="3"/>')
        out.append(txt(x0 + label_w + max(2, bw) + 10, y + bh * 0.72, fmt(v), 17, fill=MUTED))
    return "\n".join(out)


def figure(stem: str, title: str, subtitle: str, body_svg: str, footnote: str, ids, width=2200, height=1600, legend_html=""):
    doc = shell(title, KICKER, subtitle, legend_html + f'<svg width="{width-120}" height="{height-420}" viewBox="0 0 {width-120} {height-420}">{body_svg}</svg>',
                footnote, width, height) + "\n" + hidden_rows(ids)
    html, png, jpg = render(stem, doc, width, height, OUT)
    print(f"rendered {html.name} ({len(set(ids))} row ids cited)")


# ---------- data ----------
MB = load("members_network")
HM = load("hard_money"); SP = load("super_pac_c4"); LB = load("lobbying"); RD = load("revolving_door"); FG = load("federal_money")
EN = load("entities"); TL = load("timeline")
SITTING = [m for m in MB if m["cohort"] == "sitting"]
# 2026-09-29 (Kevin: "do both for lobbyist gifts"): measure B of type 4b, per LD-203 item (research/lb_4b_measures.csv)
MEAS4B = {r["row_id"]: r["measure"] for r in csv.DictReader(l for l in open(ROOT / "research/lb_4b_measures.csv", encoding="utf-8") if not l.startswith("#"))} if (ROOT / "research/lb_4b_measures.csv").exists() else {}
MBP = {m["member_bioguide"]: (m["party"] or "?").upper()[:1] for m in MB if m["member_bioguide"].strip()}  # party fallback by bioguide (Codex X1 #3)
UUID_RE = re.compile(r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})")


def once_per_filing(rows):
    """One LDA filing counts once: rows restating a filing under the same UUID collapse onto the lowest row id (Codex X1 #7, X3 #2)."""
    seen = set(); out = []
    for r in sorted(rows, key=lambda r: (len(r["row_id"]), r["row_id"])):
        u = UUID_RE.search((r.get("url") or "") + " " + (r.get("note") or ""))  # 2026-09-23 (Codex X4d #1): a query-URL row carries its filing UUID in the note
        if u and u.group(1) in seen:
            continue
        if u:
            seen.add(u.group(1))
        out.append(r)
    return out


def fig01_table():
    """Figure 01 as first drawn, a table (kept so it can be drawn again: scripts/alt_fig01.py t). Not registered."""
    stem = "congress-01-connection-table-v1"
    # per type: members with >=1 evidence row, split by party
    cols = TYPES
    x0, y0 = 40, 40
    cw = 130; rh = 44
    svg = [txt(x0, y0, "Sitting members with at least one confirmed record, by kind of connection and party (535 seats)", 24, weight="bold")]
    hdr_y = y0 + 50
    svg.append(txt(x0, hdr_y, "connection", 18, weight="bold", fill=MUTED))
    XS = {"members": 820, "D": 960, "R": 1100, "I": 1240, "rows": 1420, "amount": 1700}
    for lab, x in XS.items():
        svg.append(txt(x0 + x, hdr_y, "amount (this kind only)" if lab == "amount" else "records" if lab == "rows" else lab, 18, weight="bold", fill=MUTED, anchor="end"))
    ids = []
    for i, t in enumerate(cols):
        y = hdr_y + 40 + i * rh
        ms = [m for m in SITTING if int(m[f"t{t}_n"]) > 0]
        by_p = collections.Counter((m["party"] or "?").upper() for m in ms)
        rows = sum(int(m[f"t{t}_n"]) for m in ms)
        usd = sum(float(m[f"t{t}_usd"] or 0) for m in ms)
        ids += [m["row_id"] for m in ms]
        svg.append(txt(x0, y, TYPE_LABEL[t], 19))
        svg.append(txt(x0 + XS["members"], y, str(len(ms)), 19, anchor="end", weight="bold"))
        svg.append(txt(x0 + XS["D"], y, str(by_p.get("D", 0)), 19, anchor="end", fill=DEM))
        svg.append(txt(x0 + XS["R"], y, str(by_p.get("R", 0)), 19, anchor="end", fill=REP))
        svg.append(txt(x0 + XS["I"], y, str(by_p.get("I", 0) + by_p.get("ID", 0)), 19, anchor="end", fill=IND))
        svg.append(txt(x0 + XS["rows"], y, f"{rows:,}", 19, anchor="end"))
        svg.append(txt(x0 + XS["amount"], y, money(usd) if usd else "—", 19, anchor="end", fill=MUTED))
        bw = 300 * len(ms) / 535
        svg.append(f'<rect x="{x0+1740}" y="{y-20}" width="{bw:.1f}" height="26" fill="{PAL[i % len(PAL)]}" rx="3"/>')
    # party totals of all 535 sitting members, unlabelled, under the D / R / I columns (the baseline for each row)
    ty = hdr_y + 40 + len(cols) * rh
    svg.append(f'<line x1="{x0 + XS["D"] - 90}" y1="{ty - 26}" x2="{x0 + XS["I"] + 4}" y2="{ty - 26}" stroke="{MUTED}" stroke-width="1"/>')
    base = collections.Counter((m["party"] or "?").upper() for m in SITTING)
    svg.append(txt(x0 + XS["D"], ty, str(base.get("D", 0)), 19, anchor="end", weight="bold", fill=DEM))
    svg.append(txt(x0 + XS["R"], ty, str(base.get("R", 0)), 19, anchor="end", weight="bold", fill=REP))
    svg.append(txt(x0 + XS["I"], ty, str(base.get("I", 0) + base.get("ID", 0)), 19, anchor="end", weight="bold", fill=IND))
    # 2026-09-29: type 4b's stricter measure beside the counted one
    _lc = {r["row_id"]: r for r in load("lobbyist_contributions")}
    _b = [(m, i) for m in SITTING for i in m["t4b_ids"].split() if MEAS4B.get(i) == "named"]
    svg.append(txt(x0, ty + 40, f"Lobbyists' own contributions, stricter count (the lobbyist is also named on the network client's own lobbying filings): {len({m['row_id'] for m, _ in _b})} members, {len(_b):,} records, {money(sum(amt(_lc[i]['amount_usd']) for _, i in _b if i in _lc))}", 17, fill=MUTED))
    # second block: grid of members by count of types touched
    gy = hdr_y + 40 + (len(cols) + 1) * rh + 50
    svg.append(txt(x0, gy, "How many of the fourteen kinds of connection listed above touch each sitting member", 24, weight="bold"))
    touched = collections.Counter()
    for m in SITTING:
        n = sum(1 for t in TYPES if int(m[f"t{t}_n"]) > 0)
        touched[n] += 1
    mx = max(touched.values()) or 1
    for k in range(0, 13):
        x = x0 + k * 160
        h = 220 * touched.get(k, 0) / mx
        svg.append(f'<rect x="{x}" y="{gy+270-h:.1f}" width="120" height="{h:.1f}" fill="{DEM if k else GREY}" rx="3"/>')
        svg.append(txt(x + 60, gy + 300, f"{k} kind{'s' if k != 1 else ''}", 16, anchor="middle", fill=MUTED))
        svg.append(txt(x + 60, gy + 262 - h, str(touched.get(k, 0)), 17, anchor="middle"))
    subtitle = ('Sources: FEC, lobbying, grant, spending and travel filings and public statements, each record checked against the original document. A member counts under a connection if at least one confirmed record links them; duplicates and searches that found nothing are left out. Dollar amounts are added up only within one kind of connection, never across.')
    footnote = (f"<b>What the record does not show.</b> A contribution is not a vote, and outside spending is not coordination with the candidate. Super PAC spending and lobbyists' own gifts are indirect: the committee or the lobbyist acted, not the network's principals. Super PAC totals are those committees' counted spending for or against sitting members, and most of that money did not come from the network. Staff moves, holdings, travel and statements carry no dollar amount. Some FEC records could not be retrieved and are not counted. Built {NOW}.")
    figure(stem, "Which of the twelve kinds of connection reach which members", subtitle, "\n".join(svg), footnote, ids, height=1630)


# ---------- figure 01, the chamber (2026-11-26, Kevin: "we should use version a"; the table drawing is kept as fig01_table) ----------
RAMP01 = ["#eec06c", "#e3a03c", "#cf7d22", "#ad5a16", "#84400f", "#56270a"]  # one hue, light to dark: 1 to 6 kinds
NONE01, TRACK01 = "#c9cbc3", "#e8e3d8"
SHORT01 = {"1": "direct contributions", "2": "PAC contributions", "3b": "super PAC spending", "4a": "lobbying on members' bills", "4b": "lobbyists' own gifts",
           "5": "staff and fellows", "8": "holdings", "9": "travel and events", "10": "AI-lab purchases", "11": "public statements", "12": "state money"}


def _party(m) -> str:
    p = (m["party"] or "?").upper()
    return "I" if p in ("I", "ID") else p[:1]


def _seats(n: int, rows: int, r0: float, r1: float, cx: float, cy: float) -> list:
    """n seat positions on concentric half-rings, ordered left to right (then inner to outer)."""
    import math
    radii = [r0 + (r1 - r0) * i / (rows - 1) for i in range(rows)]
    counts = [int(n * r / sum(radii)) for r in radii]
    i = rows - 1
    while sum(counts) < n:  # the remainder goes to the outer rings
        counts[i] += 1
        i = i - 1 if i else rows - 1
    pts = [(math.pi * (1 - (k + 0.5) / c), r) for r, c in zip(radii, counts) for k in range(c)]
    pts.sort(key=lambda p: (-p[0], p[1]))
    return [(cx + r * math.cos(a), cy - r * math.sin(a)) for a, r in pts]


def _bar_end(x, y, w, h, fill, op=1.0, r=4) -> str:
    """A bar square at the left and rounded at its right end."""
    if w <= 0:
        return ""
    r = min(r, w, h / 2)
    return f'<path d="M{x:.1f},{y:.1f} h{w - r:.1f} a{r},{r} 0 0 1 {r},{r} v{h - 2 * r:.1f} a{r},{r} 0 0 1 -{r},{r} h-{w - r:.1f} z" fill="{fill}" opacity="{op}"/>'


def fig01():
    stem = "congress-01-connection-grid"
    # per kind: sitting members with at least one evidence row, split by party; a kind that reaches no member is not drawn
    kinds = []
    for t in TYPES:
        ms = [m for m in SITTING if int(m[f"t{t}_n"]) > 0]
        kinds.append({"t": t, "label": TYPE_LABEL[t], "n": len(ms), "by": collections.Counter(_party(m) for m in ms), "usd": sum(float(m[f"t{t}_usd"] or 0) for m in ms),
                      "set": {m["row_id"] for m in ms}, "indirect": "(indirect)" in TYPE_LABEL[t]})
    omitted = [k["label"] for k in kinds if not k["n"]]
    kinds = sorted([k for k in kinds if k["n"]], key=lambda k: -k["n"])
    ids = [i for k in kinds for i in sorted(k["set"])]
    breadth = {m["row_id"]: sum(1 for k in kinds if m["row_id"] in k["set"]) for m in SITTING}
    dist = collections.Counter(breadth.values())
    n_any = sum(1 for v in breadth.values() if v)
    only_indirect = sum(1 for m in SITTING if breadth[m["row_id"]] and not any(m["row_id"] in k["set"] for k in kinds if not k["indirect"]))
    base = collections.Counter(_party(m) for m in SITTING)
    # seat order: Democrats from the left edge (most kinds outermost), independents, Republicans to the right edge
    by_p = collections.defaultdict(list)
    for m in SITTING:
        by_p[_party(m)].append(m)
    order = (sorted(by_p["D"], key=lambda m: -breadth[m["row_id"]]) + sorted(by_p["I"], key=lambda m: -breadth[m["row_id"]]) + sorted(by_p["R"], key=lambda m: breadth[m["row_id"]])
             + [m for p, ms in by_p.items() if p not in "DIR" for m in ms])
    cx, cy, r0, r1 = 640, 720, 215, 620
    svg = []
    for (x, y), m in zip(_seats(len(SITTING), 12, r0, r1, cx, cy), order):
        v = breadth[m["row_id"]]
        svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="11.5" fill="{RAMP01[min(v, len(RAMP01)) - 1]}"/>' if v else f'<circle cx="{x:.1f}" cy="{y:.1f}" r="10" fill="none" stroke="{NONE01}" stroke-width="2.5"/>')
    svg.append(txt(cx, cy - 62, str(n_any), 150, anchor="middle", weight="bold", extra='letter-spacing="-5"'))
    svg.append(txt(cx, cy - 14, f"of {len(SITTING)} members", 32, anchor="middle", fill=MUTED))
    svg.append(txt(cx - r1 - 12, cy + 46, f"{base.get('D', 0)} Democrats", 22, weight="bold", fill=DEM))
    svg.append(txt(cx + r1 + 12, cy + 46, f"{base.get('R', 0)} Republicans", 22, anchor="end", weight="bold", fill=REP))
    if base.get("I"):
        svg.append(txt(cx, cy + 46, f"{base['I']} independents between them", 18, anchor="middle", fill=MUTED))
    # the scale, with the number of members at each step
    ly, x = cy + 118, cx - r1 - 12
    svg.append(txt(x, ly - 34, "Each dot is one member, shaded by how many kinds of connection are on record", 21, weight="bold"))
    for v in range(0, max(dist) + 1):
        svg.append(f'<circle cx="{x + 13:.1f}" cy="{ly + 14}" r="13" fill="{RAMP01[min(v, len(RAMP01)) - 1]}"/>' if v else f'<circle cx="{x + 13:.1f}" cy="{ly + 14}" r="11.5" fill="none" stroke="{NONE01}" stroke-width="2.5"/>')
        svg.append(txt(x + 36, ly + 10, str(dist.get(v, 0)), 22, weight="bold"))
        svg.append(txt(x + 36, ly + 32, "none" if v == 0 else f"{v} kind" + ("s" if v != 1 else ""), 16, fill=MUTED))
        x += 178
    # the kinds, ranked by the members they reach
    xk = 1345
    wk = 735
    svg.append(txt(xk, 44, "Members reached by each kind of connection", 24, weight="bold"))
    for i, k in enumerate(kinds):
        y = 96 + i * 74
        svg.append(txt(xk, y, k["label"], 19))
        svg.append(f'<rect x="{xk}" y="{y + 12}" width="430" height="14" fill="{TRACK01}"/>')
        svg.append(_bar_end(xk, y + 12, 430 * k["n"] / len(SITTING), 14, INK, 0.42 if k["indirect"] else 1.0))
        svg.append(txt(xk + 446, y + 27, str(k["n"]), 24, weight="bold"))
        svg.append(txt(xk + 512, y + 26, " · ".join(f"{k['by'].get(p, 0)} {p}" for p in "DRI" if k["by"].get(p, 0)), 16, fill=MUTED))
        if k["usd"]:
            svg.append(txt(xk + wk, y + 26, money(k["usd"]), 18, anchor="end", fill=MUTED))
    svg.append(txt(xk, 96 + len(kinds) * 74 + 6, "Bars are a share of all the seats. Paler bars are indirect: a committee or a lobbyist acted.", 16, fill=MUTED))
    short = lambda k: SHORT01.get(k["t"], k["label"].lower())  # noqa: E731
    top = [short(k) for k in kinds[:3]]
    indirect = [short(k) for k in kinds if k["indirect"]]
    subtitle = (f"The widest kinds are {', '.join(top[:-1])} and {top[-1]}. " + (f"{(lambda x: x[0].upper() + x[1:])(' and '.join(indirect))} are indirect, and for {only_indirect} of the {n_any} members they are the only kinds on record. " if indirect else "")
                + f"{dist.get(0, 0)} members have none. Sources: FEC, lobbying, grant, spending and travel filings and public statements, each record checked against the original document. "
                "A member counts under a kind of connection if at least one confirmed record links them; duplicates and searches that found nothing are left out. "
                "Dollar amounts are added up only within one kind of connection, never across.")
    # type 4b's stricter measure (2026-09-29) and the kinds that reach no member, in the footnote
    _lc = {r["row_id"]: r for r in load("lobbyist_contributions")}
    _b = [(m, i) for m in SITTING for i in m["t4b_ids"].split() if MEAS4B.get(i) == "named"]
    footnote = ("<b>What the record does not show.</b> A contribution is not a vote, and outside spending is not coordination with the candidate. Super PAC spending and lobbyists' own gifts are indirect: "
                "the committee or the lobbyist acted, not the network's principals. Super PAC totals are those committees' counted spending for or against sitting members, and most of that money did not come from the network. "
                "Staff moves, holdings, travel and statements carry no dollar amount. Some FEC records could not be retrieved and are not counted. "
                f"Lobbyists' own contributions, stricter count (the lobbyist is also named on the network client's own lobbying filings): {len({m['row_id'] for m, _ in _b})} members, {len(_b):,} records, "
                f"{money(sum(amt(_lc[i]['amount_usd']) for _, i in _b if i in _lc))}. "
                + (f"Kinds with no counted record for a sitting member are not drawn ({'; '.join(x[0].lower() + x[1:] for x in omitted)}). " if omitted else "") + f"Built {NOW}.")
    figure(stem, f"{n_any} of Congress's {len(SITTING)} members have a documented connection to Anthropic's network", subtitle, "\n".join(svg), footnote, ids, height=1370)


def fig02():
    stem = "congress-02-public-first-family-by-race"
    PF = {"C00930503": "Public First", "C30003586": "Public First Action", "C00928374": "Jobs and Democracy PAC", "C00928390": "Defending Our Values PAC"}
    ie = [r for r in SP if ev(r) and r["payer_id"] in PF and r["money_type"] in ("independent_expenditure", "electioneering_communication")]
    per = collections.defaultdict(lambda: {"support": 0.0, "oppose": 0.0, "ids": [], "name": "", "party": ""})
    for r in ie:
        k = r["member_bioguide"] or r["payee"]
        d = per[k]; so = (r["support_oppose"] or "").lower()
        if so in ("support", "oppose"):
            d[so] += amt(r["amount_usd"])
        else:
            d["undesignated"] = d.get("undesignated", 0.0) + amt(r["amount_usd"])  # an electioneering communication carries no for/against designation (Codex X1 #1)
        d["ids"].append(r["row_id"]); d["name"] = r["member_name"] or r["payee"]; d["party"] = r["party"] or d["party"] or {"ALLRED": "D"}.get((r["member_name"] or r["payee"] or "").split(",")[0].strip().upper(), "")  # X33-071: former member, party blank on the rows
    # X39-0036 (2026-10-11): ranked from the rows after the E1 rebinds; a candidate whose remaining rows sum to nothing is not drawn
    rows = sorted(((k, d) for k, d in per.items() if d["support"] + d["oppose"] + d.get("undesignated", 0.0) > 0), key=lambda kv: -(kv[1]["support"] + kv[1]["oppose"]))[:22]
    rec = [r for r in SP if ev(r) and r["payee_id"] in PF and r["money_type"] in ("outside_receipt", "transfer")]
    # AUDIT-A1 finding 3-5: the same Schedule A line was promoted from more than one lane pull; count one transaction per
    # (payer, payee, date, amount); and print only organisations and PLAN §1.1 principals by name, folding other individuals
    principals = {norm_name(r["name"]) for r in EN if r["tier"] in ("T1", "T2", "T3") and r["entity_type"] == "person" and ev(r)}
    uniq = {}
    for r in rec:
        key = (re.sub(r"[^A-Z0-9]", "", (r["payer"] or "").upper()), r["payee_id"], (r["date"] or "").strip(), round(amt(r["amount_usd"]), 2))
        uniq.setdefault(key, r)
    by_payer = collections.Counter()
    def payer_label(r):
        nm = re.sub(r"[.,]", "", (r["payer"] or "?").upper()); nm = re.sub(r"\s+INC$", "", nm).strip()
        if r["payer_id"] in PF:
            return nm[:52] + " (transfer within the family)"
        if (r["payer_type"] or "") == "individual" or ("," in (r["payer"] or "") and " " in (r["payer"] or "").strip()):
            return nm[:60] if norm_name(r["payer"]) in principals else "other individual contributors (not named; private individuals)"
        return nm[:60]
    for r in uniq.values():
        by_payer[payer_label(r)] += amt(r["amount_usd"])
    svg = [txt(40, 40, "Independent expenditures by the Public First family, by candidate (support and oppose shown separately)", 24, weight="bold")]
    mx = max([d["support"] + d["oppose"] for _, d in rows] + [1])
    ids = []
    for i, (k, d) in enumerate(rows):
        y = 90 + i * 40
        svg.append(txt(560, y + 24, f"{d['name'][:40]} ({d['party'] or '?'})", 18, anchor="end"))
        ws = 900 * d["support"] / mx; wo = 900 * d["oppose"] / mx
        svg.append(f'<rect x="580" y="{y+4}" width="{ws:.1f}" height="30" fill="{DEM}" rx="3"/>')
        svg.append(f'<rect x="{580+ws:.1f}" y="{y+4}" width="{wo:.1f}" height="30" fill="{REP}" rx="3"/>')
        svg.append(txt(590 + ws + wo, y + 25, f"{money(d['support'])} for · {money(d['oppose'])} against" + (f" · {money(d['undesignated'])} electioneering, no designation" if d.get("undesignated") else ""), 16, fill=MUTED))
        ids += d["ids"]
    y2 = 90 + len(rows) * 40 + 60
    svg.append(txt(40, y2, "Money into the Public First committees, by giver (each contribution counted once; Anthropic's gifts are as Anthropic disclosed them)", 24, weight="bold"))
    top = by_payer.most_common(12)
    svg.append(bar_chart([(p, v, None) for p, v in top], 40, y2 + 20, 1900, 520, label_w=700, colour=lambda r: IND))
    ids += [r["row_id"] for r in uniq.values()]
    ANTH_PFA = sum(amt(r["amount_usd"]) for r in SP if r["row_id"] in ("SP053", "SP054"))  # Anthropic's issuer-disclosed gifts to Public First Action
    subtitle = (f"Sources: FEC outside-spending reports and contribution records of Public First, Public First Action, Jobs and Democracy PAC and Defending Our Values PAC. Anthropic's {money(ANTH_PFA)} to Public First Action, a group that does not disclose donors, is as Anthropic itself announced it. One bar per candidate named; ads that name a candidate without saying for or against are shown separately.")
    footnote = ('<b>What the record does not show.</b> Outside spending is not coordination: the filing states the committee acted alone. Money given to a group that does not disclose its donors stays unattributed. A candidate named in an attack ad received nothing. Records that could not be confirmed against the original filing are left out.')
    figure(stem, "Public First family money in and out, by race", subtitle, "\n".join(svg), footnote, ids, height=1700,
           legend_html='<div class="legend">' + legend([(DEM, "spent in support"), (REP, "spent in opposition"), (IND, "money into the committees")]) + "</div>")


def norm_name(s: str) -> tuple[str, str]:
    s = re.sub(r"[^A-Za-z, ]", " ", s or "").strip()
    if "," in s:
        last, first = [x.strip() for x in s.split(",", 1)]
    else:
        toks = s.split()
        if not toks:
            return ("", "")
        last, first = toks[-1], toks[0]
    return (last.lower(), first.split()[0].lower() if first.split() else "")


def fig03():
    stem = "congress-03-principals-hard-money-by-party-and-cycle"
    principals = {norm_name(r["name"]): (r["name"], r["tier"]) for r in EN if r["tier"] in ("T1", "T2", "T3") and r["entity_type"] == "person" and ev(r)}
    sitting = {m["member_bioguide"] for m in SITTING}
    rows = [r for r in HM if ev(r) and r["money_type"] == "hard_money" and r["payer_type"] == "individual" and r["hop"] != "2" and norm_name(r["payer"]) in principals and r["member_bioguide"] in sitting]  # AUDIT-A1 finding 8; X33-002: hop-2 LD-203 copies of an FEC line are type 4b
    cells = collections.defaultdict(float); cnt = collections.Counter(); ids = []
    cycles = sorted({r["cycle"] for r in rows if r["cycle"]})
    for r in rows:
        p = ((r["party"] or "").upper()[:1]) or MBP.get(r["member_bioguide"], "?")  # a blank row party falls back to the member's roster party
        cells[(r["cycle"], p)] += amt(r["amount_usd"]); cnt[(r["cycle"], p)] += 1; ids.append(r["row_id"])
    by_payer = collections.Counter()
    for r in rows:
        by_payer[principals[norm_name(r["payer"])][0]] += amt(r["amount_usd"])
    svg = [txt(40, 40, "Direct contributions from the network's principals to sitting members, by election cycle and the recipient's party", 24, weight="bold")]
    mx = max(list(cells.values()) + [1])
    x0 = 120
    for i, c in enumerate(cycles):
        x = x0 + i * 190
        yb = 520
        for j, p in enumerate(["D", "R", "I"]):
            v = cells.get((c, p), 0.0); h = 380 * v / mx
            svg.append(f'<rect x="{x + j*55}" y="{yb-h:.1f}" width="48" height="{h:.1f}" fill="{party_colour(p)}" rx="3"/>')
            if v:
                svg.append(txt(x + j * 55 + 24, yb - h - 8, money(v), 13, anchor="middle"))
        svg.append(txt(x + 80, yb + 28, c, 17, anchor="middle", fill=MUTED))
    svg.append(txt(40, 620, "By giver, split by the recipient's party", 24, weight="bold"))
    by_pp = collections.defaultdict(float)  # giver x recipient party
    for r in rows:
        p = ((r["party"] or "").upper()[:1]) or MBP.get(r["member_bioguide"], "?")
        by_pp[(principals[norm_name(r["payer"])][0], p if p in ("D", "R", "I") else "I")] += amt(r["amount_usd"])
    givers = [k for k, v in by_payer.most_common(14) if len(k.strip()) > 2]
    gmx = max([by_payer[k] for k in givers] + [1])
    width = 1900  # page width
    bx, bwmax, bh = 40 + 520, width - 520 - 420, 34
    for i, k in enumerate(givers):
        y = 660 + i * bh
        svg.append(txt(bx - 14, y + bh * 0.72, k[:64], 17, anchor="end"))
        x = bx
        for p in ("D", "R", "I"):
            v = by_pp.get((k, p), 0.0)
            if v:
                w = max(2.0, bwmax * v / gmx)
                svg.append(f'<rect x="{x:.1f}" y="{y + 2}" width="{w:.1f}" height="{bh - 6}" fill="{party_colour(p)}"/>')
                x += w
        parts = " · ".join(f"{p} {money(by_pp[(k, p)])}" for p in ("D", "R", "I") if by_pp.get((k, p)))
        svg.append(txt(x + 10, y + bh * 0.72, f"{money(by_payer[k])}   ({parts})", 15, fill=MUTED))
    subtitle = ("Sources: FEC contribution records where the giver is one of the network's named principals and the recipient is a sitting member's campaign, leadership PAC or joint fundraising committee. Pass-through entries are never added twice.")
    footnote = ("<b>What the record does not show.</b> A contribution is not a vote. A person's giving is their own, not their employer's. Party and super PAC giving are shown in other figures. Givers are matched by name and confirmed by employer or city; namesakes that could not be confirmed are left out. A gift to a joint fundraising committee counts once there; the committee's later allocations to its members are not added again. The 2026 cycle is still open, so 2026 is a floor.")
    figure(stem, "Principals' hard money to sitting members", subtitle, "\n".join(svg), footnote, ids, height=1580,
           legend_html='<div class="legend">' + legend([(DEM, "to Democrats"), (REP, "to Republicans"), (IND, "to independents")]) + "</div>")


def client_label(name: str) -> str:
    n = (name or "?").upper()
    if "ANTHROPIC" in n:
        return "ANTHROPIC PBC (in-house and its outside lobbying firms)"
    if "FEDERATION OF AMERICAN SCIENTISTS" in n:
        return "FEDERATION OF AMERICAN SCIENTISTS"
    if re.search(r"\bIFP ACTION\b", n):  # X33-003: 'SLEVIN ADVISORY LLC O/B/O THE IFP ACTION' is the same client
        return "IFP ACTION"
    if "CENTER FOR AI SAFETY" in n or n.startswith("CAIS"):
        return "CENTER FOR AI SAFETY ACTION FUND"
    if "AMERICANS FOR RESPONSIBLE INNOVATION" in n:
        return "AMERICANS FOR RESPONSIBLE INNOVATION"
    n = re.sub(r",?\s*(INC\.?|LLC|CORPORATION)$", "", n).strip(" ,.")
    return n[:44]


def fig04():
    stem = "congress-04-lobbying-spend-and-hill-origins"
    ld2 = [r for r in LB if ev(r) and r["filing_type"] == "LD-2" and r["amount_usd"].strip()]
    spend = collections.defaultdict(float); ids = []
    # 2026-10-11 (audit X39 E5, Kevin approved): under the LDA guidance an in-house filer's expenses already include what it paid
    # outside firms, so in any quarter with an in-house report for a client only that report counts; outside firms' income
    # counts only for quarters with no in-house report.
    def _nz(s):
        return re.sub(r"\b(INC|LLC|PBC|CORP|CORPORATION|THE)\b", "", re.sub(r"[^A-Z0-9 ]", " ", (s or "").upper())).split()
    def inhouse(r):
        a, b = " ".join(_nz(r["registrant"])), " ".join(_nz(r["client"]))
        return bool(a) and (a == b or a in b or b in a)
    filings = [r for r in once_per_filing(ld2) if "2016" <= (r["period"] or r["date"] or "")[:4] <= "2026"]
    inq = {(client_label(r["client"]), (r["period"] or r["date"] or "")[:7]) for r in filings if inhouse(r)}
    for r in filings:
        yr = (r["period"] or r["date"] or "")[:4]
        if (client_label(r["client"]), (r["period"] or r["date"] or "")[:7]) in inq and not inhouse(r):
            continue
        spend[(client_label(r["client"]), yr)] += amt(r["amount_usd"]); ids.append(r["row_id"])
    clients = collections.Counter()
    for (c, y), v in spend.items():
        clients[c] += v
    top = [c for c, _ in clients.most_common(10)]
    years = sorted({y for (_, y) in spend if y})
    colw = int(1380 / max(1, len(years)))
    svg = [txt(40, 40, "Lobbying spend as reported, by client and year, 2016–2026 (fees for lobbying firms, costs for in-house teams)", 24, weight="bold")]
    mx = max(list(spend.values()) + [1])
    for i, c in enumerate(top):
        y = 90 + i * 66
        svg.append(txt(560, y + 30, c, 17, anchor="end"))
        for j, yr in enumerate(years):
            v = spend.get((c, yr), 0.0)
            w = (colw - 30) * v / mx
            if v:
                svg.append(f'<rect x="{580 + j*colw}" y="{y+8}" width="{max(2,w):.1f}" height="36" fill="{PAL[j % len(PAL)]}" rx="3"/>')
                svg.append(txt(580 + j * colw + max(2, w) + 4, y + 32, money(v), 13, fill=MUTED))
    for j, yr in enumerate(years):
        svg.append(txt(580 + j * colw, 82, yr, 16, fill=MUTED))
    # 2026-09-23 (Codex X4d #1): LD-1/LD-2 filings of 2016–2026 whose covered-position field names a role (an all-placeholder field such as "n/a ;; n/a" is not a disclosure)
    def names_role(v: str) -> bool:
        parts = [p.strip().lower() for p in re.split(r";;|;|\|", v or "") if p.strip()]
        return any(not re.fullmatch(r"(?:[a-z .'\-]+:)?\s*(?:n/?a|none|not applicable|-)?", p) for p in parts)
    cov = once_per_filing([r for r in LB if ev(r) and r["filing_type"] in ("LD-1", "LD-2") and "2016" <= (r["period"] or r["date"] or "")[:4] <= "2026" and names_role(r["covered_positions"])])
    by_client = collections.Counter(client_label(r["client"] or r["registrant"]) for r in cov)
    y2 = 90 + len(top) * 66 + 60
    svg.append(txt(40, y2, "Lobbying reports, 2016–2026, that disclose a lobbyist's former government job, by client (each report counted once)", 24, weight="bold"))
    svg.append(bar_chart([(c, v, None) for c, v in by_client.most_common(12) if c.strip() and c != "?"], 40, y2 + 20, 1900, 520, label_w=700, colour=lambda r: DEM, fmt=lambda v: f"{int(v)} filings"))
    ids += [r["row_id"] for r in cov]
    subtitle = ("Sources: quarterly Senate lobbying reports filed for network clients, 2016–2026. Spend is the amount printed on each report; the lower panel counts only reports that actually name a lobbyist's prior government role. Variant client spellings are merged (Anthropic's own reports and those its outside lobbying firms file for it are one line); in a quarter with the client's own in-house report only that report counts, because it already includes the firms' fees.")
    footnote = ("<b>What the record does not show.</b> Reported amounts are rounded by the filer. A client's own in-house report already includes what it paid outside firms, so the two are not added; Tower 19's fees count as Aquia Group's subcontract for Anthropic, whose own report covers them (Tower 19's registration names Anthropic as the principal; audit X54). Reports before 2016 (RAND's and FAS's among them) are left out. A former government job is a job history, not evidence it was used. Amended reports appear once.")
    figure(stem, "Lobbying spend and the lobbyists' Hill origins", subtitle, "\n".join(svg), footnote, ids, height=1650)


def person_key(name: str) -> str:
    toks = [t for t in re.split(r"[\s,.]+", (name or "").lower()) if t and len(t) > 1 and t not in ("jr", "sr", "ii", "iii", "iv", "dr", "mr", "ms")]
    # first three letters of the first name fold a short form onto the full name (Max / Maximilian); the surname decides the rest
    return (toks[0][:3] + " " + toks[-1]) if len(toks) >= 2 else " ".join(toks) or "?"


HOST_COMM = [("homeland", "Homeland Security"), ("foreign affairs", "Foreign Affairs"), ("foreign relations", "Foreign Relations"),
             ("judiciary", "Judiciary"), ("energy and commerce", "Energy and Commerce"), ("energy commerce", "Energy and Commerce"),
             ("commerce", "Commerce, Science, and Transportation"), ("strategic competition", "Select Committee on the CCP"),
             ("select committee on china", "Select Committee on the CCP"), ("ccp", "Select Committee on the CCP"), ("banking", "Banking"),
             ("science", "Science, Space, and Technology"), ("appropriations", "Appropriations"), ("oversight", "Oversight"), ("intelligence", "Intelligence"),
             ("ways and means", "Ways and Means"), ("finance", "Finance"), ("armed services", "Armed Services"), ("rules", "Rules"),
             ("small business", "Small Business"), ("health, education", "HELP"), ("help", "HELP")]
_MBROW = {m["member_bioguide"]: m for m in MB if m["member_bioguide"].strip()}
_SURN = collections.defaultdict(set)
for _b, _m in _MBROW.items():
    _SURN[re.sub(r"[^a-z]", "", (_m["member_name"] or "").split(",")[0].lower())].add(_b)


def host_key(org_now: str, bioguide: str = "") -> str:
    """X33-005/X33-024 (2026-09-29): one host per member office or committee, whatever the spelling: a member's office by the row's
    bioguide id (or an unambiguous 'Sen./Rep. <surname>'), a committee by its name with majority, minority, party staff and
    subcommittees folded in; anything else keeps its own text."""
    def office(b):
        m = _MBROW[b]; ch = "Sen." if (m["chamber"] or "").lower().startswith("s") else "Rep."
        nm = (m["member_name"] or b); nm = " ".join(reversed([x.strip() for x in nm.split(",", 1)])) if "," in nm else nm
        return f"{ch} {nm.title()} ({(m['party'] or '?')[:1].upper()}-{(m['state'] or '').upper()})"
    b = (bioguide or "").strip()
    if b in _MBROW:
        return office(b)
    o = re.sub(r"\s+", " ", (org_now or "").strip()); ol = o.lower().replace("&", "and")  # X34-0647: 'Energy & Commerce' 
    for pat, k in HOST_COMM:
        if pat in ol:
            ch = "Senate " if ("senate" in ol or "senator" in ol) else "House " if "house" in ol else ""
            if k == "Homeland Security" and ("governmental affairs" in ol or "hsgac" in ol):
                ch = "Senate "
            if k == "Homeland Security" and ch == "Senate ":  # X34-0663: the Senate committee's full name; the House one is Homeland Security
                k = "Homeland Security and Governmental Affairs"
            return f"{ch}{k}" + ("" if "Committee" in k else " committee")
    m = re.search(r"(?:sen\.|senator|rep\.|representative)\s+([a-z\u00e0-\u00ff .'\-]+)", ol)
    if m and m.group(1).split():
        s = re.sub(r"[^a-z]", "", m.group(1).split()[-1])
        if len(_SURN.get(s, ())) == 1:
            return office(next(iter(_SURN[s])))
    return o


def fig05():
    stem = "congress-05-revolving-door-both-directions"
    rows = [r for r in RD if ev(r) and r["direction"] in ("hill->network", "network->hill")]
    ids = [r["row_id"] for r in rows]
    ACR = {"Nscai": "NSCAI", "Rand": "RAND", "Llc": "LLC", "Llp": "LLP", "Dla": "DLA", "Dc": "DC", "U.s.": "U.S.", "Ai": "AI", "Csis": "CSIS", "Cset": "CSET", "Cnas": "CNAS", "Fas": "FAS", "Ari": "ARI", "Fli": "FLI", "Metr": "METR", "Govai": "GovAI", "Iii": "III", "Jr.": "Jr.", "Ii": "II", "Rep.": "Rep.", "Sen.": "Sen.", "Nist": "NIST", "Aisi": "AISI", "Us": "US", "(us)": "(US)", "(Us)": "(US)", "A": "a", "Inc.": "Inc."}
    def org(v: str) -> str:
        v = re.sub(r"\s+", " ", (v or "").strip())
        v = re.sub(r",\s+and\b", " and", v)  # 2026-09-23 (Codex X1b #7): an Oxford-comma variant of a committee name is the same host
        if not v:
            return ""
        words = [ACR.get(w.title(), w.title()) for w in v.split(" ")]
        v = " ".join(words)
        for small in ("Of", "And", "The", "On", "For", "In"):
            v = re.sub(rf"(?<!^)\b{small}\b", small.lower(), v)
        if v.lower().startswith("public first"):
            v = "Public First / Public First Action (the family)"
        if v.upper() in ("CNAS", "CNAS.") or v.lower().startswith("center for a new american security"):  # X39 E8: one organisation, two spellings
            v = "Center for a New American Security"
        v = re.sub(r"\bLlc\b", "LLC", v).replace("(Formerly ", "(formerly ")  # X40-2948: "Navigators Global LLC (formerly DC Navigators, LLC)"
        return v[:84]
    # one record per person and direction; the organisation comes from any of that person's rows
    per = collections.defaultdict(lambda: {"now": set(), "prior": set(), "ids": []})
    for r in rows:
        k = (r["direction"], person_key(r["person"]))  # 2026-09-23 (Codex X1b #7): spelling variants and middle initials are one person
        d = per[k]; d["ids"].append(r["row_id"])
        if r["org_now"].strip():
            d["now"].add(host_key(r["org_now"], r["member_bioguide"]) if r["direction"] == "network->hill" else org(r["org_now"]))
        if r["prior_org"].strip():
            d["prior"].add(org(r["prior_org"]))
    n2h = {k: d for k, d in per.items() if k[0] == "network->hill"}
    h2n = {k: d for k, d in per.items() if k[0] == "hill->network"}
    by_now = collections.Counter(); by_hire = collections.Counter()
    for d in n2h.values():
        for o in (d["now"] or {"(office not stated on the rows)"}):
            by_now[o] += 1
    for d in h2n.values():
        for o in (d["now"] or {"(organisation not stated on the rows)"}):
            by_hire[o] += 1
    svg = [txt(40, 40, f"Network → Hill: {len(n2h)} people, by the office or committee that hosted or employed them (a person with two offices counts in both)", 24, weight="bold")]
    MIN_PEOPLE = 2  # X40-2947 (2026-10-11): the panel ends at a stated count, so no tie is cut; hosts below it are counted in a line
    hosts = [(c, v) for c, v in by_now.most_common() if v >= MIN_PEOPLE]
    rest = sum(1 for v in by_now.values() if v < MIN_PEOPLE)
    svg.append(bar_chart([(c, v, None) for c, v in hosts], 40, 60, 1900, min(560, 34 * len(hosts) + 40), label_w=900, colour=lambda r: DEM, fmt=lambda v: f"{int(v)}"))
    if rest:
        svg.append(txt(40, 60 + min(560, 34 * len(hosts) + 40) + 24, f"and {rest} other offices and committees with one person each", 17, fill=MUTED))
    svg.append(txt(40, 640, f"Hill → network: {len(h2n)} people, by the network organisation, or the lobbying firm working for a network client, that employs them", 24, weight="bold"))
    svg.append(bar_chart([(c, v, None) for c, v in [kv for kv in by_hire.most_common() if kv[1] >= 2]], 40, 660, 1900, 560, label_w=900, colour=lambda r: REP, fmt=lambda v: f"{int(v)}"))
    subtitle = ("Sources: House and Senate staff payroll reports, TechCongress and Horizon fellowship pages, lobbyists' disclosed former posts and organisations' staff pages. Each person counts once per direction, however many jobs they held.")
    footnote = ('<b>What the record does not show.</b> Taking a job is not evidence about the work done in it. Fellows count in the office that hosted them; who paid them is stated only where a payroll record was found. TechCongress is held as context under the roster criteria, so its placements are not counted as network-to-Hill moves. People for whom only one side of the move could be established are not drawn. Some staff directories could not be reached.')
    figure(stem, "The revolving door, both directions", subtitle, "\n".join(svg), footnote, ids, height=1650)


def fig06():
    stem = "congress-06-federal-money-to-the-network"
    # only awards the reviewer bound to a network entity (entity_id set); homonym non-matches recorded as bind=no are excluded
    bound = lambda r: bool(r["entity_id"].strip()) or "bind=yes" in (r["note"] or "")  # noqa: E731
    rows = [r for r in FG if ev(r) and amt(r["amount_usd"]) > 0 and bound(r) and r["money_type"] == "federal_award"]  # AUDIT-A1 finding 16: $0 obligations not drawn
    ids = [r["row_id"] for r in FG if ev(r) and (r["entity_id"].strip() or r["provision"] or r["bill"])]  # every held federal-context row is cited
    by_rec = collections.Counter(); by_agency = collections.Counter()
    for r in rows:
        by_rec[(r["recipient"] or "?")[:56]] += amt(r["amount_usd"]); by_agency[(r["agency"] or "?")[:56]] += amt(r["amount_usd"])
    prov_all = [r for r in FG if ev(r) and (r["provision"] or r["bill"])]
    # 2026-09-23 (Codex X3 #9): only a row with both a bill identifier and a bound network entity is a provision naming a network body
    prov = [r for r in prov_all if r["bill"].strip() and r["entity_id"].strip()]
    svg = [txt(40, 40, f"Federal awards to network organisations, by recipient (USAspending, as reported; {len(rows)} awards)", 24, weight="bold")]
    svg.append(bar_chart([(c, v, None) for c, v in by_rec.most_common(12)], 40, 60, 1900, 480, label_w=700, colour=lambda r: DEM))
    svg.append(txt(40, 560, "By awarding agency", 24, weight="bold"))
    svg.append(bar_chart([(c, v, None) for c, v in by_agency.most_common(10)], 40, 580, 1900, 420, label_w=700, colour=lambda r: IND))
    enacted = [r for r in prov if re.search(r"PLAW|public law|enacted|RDT&E|PE 0", (r["provision"] or "") + (r["note"] or ""), re.I)]
    svg.append(txt(40, 1020, (f"Bill text naming a network organisation: {len(prov)} passage{'s' if len(prov) != 1 else ''} ({len(enacted)} enacted, {len(prov)-len(enacted)} proposed)" if prov
                              else "Bill text naming a network organisation for its network-funded work: none in the record (passages naming RAND's other work are context)"), 21, weight="bold"))
    for i, r in enumerate(prov[:9]):
        svg.append(txt(40, 1050 + i * 26, f"{(r['bill'] or '')[:18]}  {(r['provision'] or '')[:150]}", 15, fill=MUTED))
    subtitle = ('Sources: federal award records from USAspending and bill text from govinfo. Award amounts are money committed, as printed on the award record; the bill passages are quoted from bill text on govinfo and the Congressional Record.')
    footnote = ('<b>What the record does not show.</b> An award to an organisation is not a payment to a person, and money committed is not money spent. A bill that names an organisation does not mean the organisation asked for it. Some searches timed out and are gaps, not zeros. Look-alike names (such as a biotech firm with a similar name) are left out. RAND, CNAS, the Carnegie Endowment and FAS count only for awards on the lines the network funds there, from the date it first funded each line; their other federal work is held as context.')
    figure(stem, "Federal money to the network", subtitle, "\n".join(svg), footnote, ids, height=1550)


def fig07():
    stem = "congress-07-time-axis"
    rows = load("timeline_all")
    q = collections.defaultdict(collections.Counter)
    latest = ""
    for r in rows:
        if r["role"] != "evidence":
            continue
        d = r["date"]
        if len(d) < 7 or d[:4] < "2016":
            continue
        q[d[:4]][r["conn_type"]] += 1
        latest = max(latest, d[:10])
    keys = sorted(q)
    types = ["1/2", "3a/3b", "4a", "4b", "5", "6", "7", "8", "9", "10", "11", "12"]
    NAMES = {"1/2": "campaign contributions", "3a/3b": "outside spending (super PACs)", "4a": "lobbying reports", "4b": "lobbyists' own gifts", "5": "staff and fellows", "6": "grants",
             "7": "federal awards and bills", "8": "financial disclosures", "9": "travel and events", "10": "campaigns paying AI labs", "11": "public statements", "12": "state money"}
    SHORT = {"1/2": "contributions", "3a/3b": "outside spending", "4a": "lobbying reports", "4b": "lobbyists' gifts", "5": "staff", "6": "grants", "7": "federal", "8": "disclosures", "9": "travel", "10": "AI-lab payments", "11": "statements", "12": "state money"}
    totals = {k: sum(v for t, v in q[k].items() if t in types) for k in keys}  # X34-0597: print what the bars draw
    mx = max(list(totals.values()) + [1])
    step = 1000 if mx <= 6000 else 2000
    top = ((mx // step) + 1) * step
    x0, yb, W, H = 150, 900, 1900, 700
    bw = W / max(1, len(keys))
    # the story in numbers
    def share(k, t):
        return 100 * q[k].get(t, 0) // max(1, totals.get(k, 1))
    even = [k for k in ("2018", "2020", "2022", "2024") if k in q]; odd = [k for k in ("2017", "2019", "2021") if k in q]  # X33-010: the years the sentence names
    even_share = [share(k, "3a/3b") for k in even]; odd_share = [share(k, "1/2") for k in odd]  # 2026-09-29: after the X33a window rule, direct contributions lead the off years
    late = {k: q[k].get("1/2", 0) + q[k].get("10", 0) for k in ("2025", "2026") if k in q}
    late_share = [100 * v // totals[k] for k, v in late.items()]
    svg = [txt(40, 40, "Confirmed records per year, coloured by kind of connection, 2016–2026 (height = number of records dated in that year)", 24, weight="bold")]
    svg.append(txt(40, 72, f"Election years (red) are outside-spending years: super PAC ad buys and money into super PACs are {min(even_share)}–{max(even_share)}% of 2018, 2020, 2022 and 2024. Off years are led by campaign contributions (blue), {min(odd_share)}–{max(odd_share)}% of 2017, 2019 and 2021.", 16, fill=MUTED))
    svg.append(txt(40, 96, f"In 2025 and 2026 the mix changes: individuals' contributions plus campaigns paying Anthropic and other AI labs make up {min(late_share)}–{max(late_share)}% of those years. 2026 is not over yet.", 16, fill=MUTED))
    for g in range(0, top + 1, step):
        y = yb - H * g / top
        svg.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x0 + W}" y2="{y:.1f}" stroke="#d9d4c8" stroke-width="1"/>')
        svg.append(txt(x0 - 12, y + 5, f"{g:,}", 14, anchor="end", fill=MUTED))
    svg.append(txt(x0 - 12, yb - H - 22, "records", 13, anchor="end", fill=MUTED))
    pad = 14
    for i, k in enumerate(keys):
        y = yb; bx = x0 + i * bw + pad; bwid = bw - 2 * pad
        for jj, t in enumerate(types):
            v = q[k].get(t, 0)
            if not v:
                continue
            h = H * v / top
            svg.append(f'<rect x="{bx:.1f}" y="{y-h:.1f}" width="{bwid:.1f}" height="{h:.1f}" fill="{PAL[jj % len(PAL)]}"/>')
            if h >= 34:  # a segment tall enough to carry its own count and name
                svg.append(txt(bx + bwid / 2, y - h / 2 + 5, f"{v:,} {SHORT[t]}", 13, anchor="middle", weight="bold", fill="#ffffff"))
            y -= h
        svg.append(txt(bx + bwid / 2, y - 10, f"{totals[k]:,}", 16, anchor="middle", weight="bold"))
        label = k + (" (to date)" if k == "2026" else "")
        svg.append(txt(bx + bwid / 2, yb + 26, label, 16, anchor="middle", weight="bold" if int(k) % 2 == 0 else "normal", fill=INK if int(k) % 2 == 0 else MUTED))
        if int(k) % 2 == 0 and k < "2026":
            svg.append(txt(bx + bwid / 2, yb + 46, "election year", 13, anchor="middle", fill=PAL[1]))
    # spine: milestones spread across the years, boilerplate rows skipped, at most two per year
    spine = [r for r in TL if (r["category"] or "") in ("gov-pipeline", "legislation", "policy-fight") and r["date"][:4] >= "2016"
             and not re.search(r"congress\.gov|count=|pagination|api member", (r["event"] or ""), re.I)]
    ids = [r["row_id"] for r in spine]
    picked = []; per_year = collections.Counter(); seen_ev = []
    for r in sorted(spine, key=lambda r: (r["date"], 0 if r["category"] == "gov-pipeline" else 1)):
        y = r["date"][:4]
        words = {w for w in re.findall(r"[A-Za-z]{5,}", (r["event"] or "")) if w.lower() not in ("sponsored", "cosponsor", "pursuant", "member", "national", "report")}
        if per_year[y] >= 2 or any(yy == y and len(words & ww) >= 2 for yy, ww in seen_ev):
            continue
        seen_ev.append((y, words)); per_year[y] += 1; picked.append(r)
    picked = picked[:16]
    sy = yb + 90
    svg.append(txt(40, sy, f"Key moments: the network's people entering government, AI bills and policy fights ({len(picked)} shown, at most two per year)", 22, weight="bold"))
    for i, r in enumerate(picked):
        svg.append(txt(40, sy + 32 + i * 24, f"{r['date'][:10]:<11}", 15, fill=MUTED, extra='font-family="monospace"'))
        svg.append(txt(170, sy + 32 + i * 24, (lambda e: e if len(e) <= 150 else e[:147].rstrip() + "…")(re.sub(r"\s*\(GSA Committee No\. \d+\)|;?\s*pack-\d+\b.*$|\bnatsec\b", lambda m: "national security" if m.group(0) == "natsec" else "", r['event'] or '').strip()), 15, fill=INK))
    subtitle = ("What this is: each record is one filed document or one line in it: a super PAC ad buy, a campaign contribution, a campaign's payment to an AI company, a lobbyist's own gift, a grant, a federal award, a public statement. It shows when the paper trail exists, not how much money moved.")
    footnote = ('<b>What the record does not show.</b> Counts follow filing calendars and how deeply each period was searched: 2024–2026 were searched more thoroughly than 2016–2019, and one super PAC can file thousands of small ad-buy lines in a year. Records dated only by year (annual holdings, jobs with only a start year) are not in the bars. Most key moments are dated events copied from the timeline of a companion study, not rows reviewed in this pack.')
    figure(stem, "Election years spike with outside spending; 2025–26 shift to donations and AI-lab payments", subtitle, "\n".join(svg), footnote, ids, height=1440 + 24 * len(picked),
           legend_html='<div class="legend">' + legend([(PAL[j], NAMES[t]) for j, t in enumerate(types)]) + "</div>")

ALL = {"congress-01-connection-grid": fig01, "congress-02-public-first-family-by-race": fig02, "congress-03-principals-hard-money-by-party-and-cycle": fig03,
       "congress-04-lobbying-spend-and-hill-origins": fig04, "congress-05-revolving-door-both-directions": fig05, "congress-06-federal-money-to-the-network": fig06,
       "congress-07-time-axis": fig07}

if __name__ == "__main__":
    want = sys.argv[1:] or list(ALL)
    for stem in want:
        ALL[stem]()
