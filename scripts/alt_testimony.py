#!/usr/bin/env python3
"""Draft (figures-alt): network people and organisations testifying before Congress, 2011–2026. An appearance is a
committee hearing where the record lists the witness in a network organisation's capacity (lane C156, audit X20): the
travel.csv testimony rows with role evidence. 2026-09-29 (audit X33-025/X33-088): appearances are no longer added through a
match on a held member statement; the testimony rows those matches stood for were checked against the witness lists and
set to evidence themselves, with the six appearances X33 found held out on the record's capacity and line.
usage: python3 scripts/alt_testimony.py"""
from __future__ import annotations

import collections
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_figures as bf  # noqa: E402
import build_figures2 as b  # noqa: E402
from casework.figures.common import legend  # noqa: E402

bf.OUT = bf.ROOT / "figures-alt"
FINAL = False  # 2026-09-29: build_figures3.py sets True to render the registered figure into figures/
HOUSE, SENATE, OTHER = "#2c6fbb", "#c0392b", "#9a9a9a"
LARGE = ("RAND", "CNAS", "CARNEGIE", "FAS", "FEDERATION OF AMERICAN SCIENTISTS", "CENTER FOR A NEW AMERICAN SECURITY")


def surname(s: str) -> str:
    s = re.sub(r"\b(Mr|Ms|Mrs|Dr|Hon|PhD|Jr|Sr)\b\.?", "", s or "", flags=re.I)
    s = re.sub(r"The Honorable", "", s, flags=re.I).strip(" ,")
    if "," in s:
        head, tail = [x.strip() for x in s.split(",", 1)]
        if len(head.split()) == 1 and tail:  # "Amodei, Dario"
            return head.upper()
        s = head
    parts = s.split()
    return parts[-1].upper() if parts else ""


def display(s: str) -> str:
    s = re.sub(r"^(Mr\.|Ms\.|Mrs\.|Dr\.|The Honorable)\s*", "", (s or "").strip())
    head, _, tail = s.partition(",")
    if tail.strip() and len(head.split()) == 1:
        return f"{tail.strip()} {head.strip()}"
    return head.strip()


def main() -> int:
    stem = "congress-26-committee-testimony"
    if not FINAL:
        stem = "congress-testimony-draft"
    ent = {r["row_id"]: r["name"] for r in b.EN}
    rows, ids, pre = [], [], []
    for r in b.TV:
        if not (r["event"] or "").startswith("hearing testimony") or not (r["entity_id"] or "").strip():
            continue
        name = ent.get(r["entity_id"], "?")
        if b.ev(r):
            rows.append((r, name)); ids.append(r["row_id"])
        elif "before first network funding" in (r["note"] or ""):  # 2026-09-28: pre-funding appearances drawn hollow (PLAN §1.1a line dating)
            pre.append((r, name))
    # 2026-10-11 (audit X48): testimony collected as member_statements rows (C168/C169) is drawn too, organisation resolved in
    # research/testimony_from_statements.csv; an appearance already held as a travel row (same date and witness) is not added again
    held = {(r["date"], surname(r["traveler"])) for r, _ in rows}
    ms = {r["row_id"]: r for r in b.MS}
    for t in b.load("testimony_from_statements"):
        m = ms.get(t["row_id"])
        if not m or not b.ev(m) or (m["date"], surname(m["speaker"])) in held:
            continue
        rows.append(({"row_id": m["row_id"], "date": m["date"], "chamber": t["chamber"], "traveler": m["speaker"], "sponsor": t["committee"],
                      "event": f"hearing testimony: {t['hearing_title']}"}, ent.get(t["entity_id"], "?")))
        ids.append(m["row_id"])
    orgs = [o for o, _ in collections.Counter(n for _, n in rows + pre).most_common()]
    years = list(range(2015, 2027))
    x0, lw, cw, y0, rh = 40, 360, 136, 90, 54
    svg = [b.txt(40, 40, f"Committee appearances by witnesses the record lists in a network organisation's capacity, by year ({len(rows)} appearances)", 24, weight="bold")]
    for j, y in enumerate(years):
        svg.append(b.txt(x0 + lw + j * cw + cw / 2, y0 - 12, str(y), 15, anchor="middle", fill=b.MUTED))
    for i, o in enumerate(orgs):
        yy = y0 + i * rh
        if i % 2 == 0:
            svg.append(f'<rect x="{x0}" y="{yy}" width="{lw + len(years) * cw}" height="{rh}" fill="#efece4"/>')
        svg.append(b.txt(x0 + lw - 16, yy + rh * 0.62, {"Schmidt Special Competitive Studies Project": "SCSP (Schmidt)", "AI Futures Project Inc": "AI Futures Project"}.get(o, o), 18, anchor="end", weight="bold"))
        cell = collections.defaultdict(list)
        for r, n in rows:
            if n == o and (r["date"] or "")[:4].isdigit():
                cell[int(r["date"][:4])].append(r)
        for r, n in pre:
            if n == o and (r["date"] or "")[:4].isdigit():
                cell[int(r["date"][:4])].append(dict(r, _pre=True))
        for y, rr in cell.items():
            if y not in years:
                continue
            cx = x0 + lw + (y - years[0]) * cw + 16
            for k, r in enumerate(sorted(rr, key=lambda r: r["date"])):
                col = HOUSE if (r["chamber"] or "").startswith("House") else SENATE if (r["chamber"] or "").startswith("Senate") else OTHER
                if r.get("_pre"):
                    svg.append(f'<circle cx="{cx + (k % 6) * 13:.1f}" cy="{yy + rh / 2 - 7 + (k // 6) * 14:.1f}" r="4.8" fill="none" stroke="{col}" stroke-width="1.6"/>')
                else:
                    svg.append(f'<circle cx="{cx + (k % 6) * 13:.1f}" cy="{yy + rh / 2 - 7 + (k // 6) * 14:.1f}" r="5.5" fill="{col}"/>')
    ay = y0 + len(orgs) * rh + 70
    svg.append(b.txt(40, ay, "Anthropic's appearances", 22, weight="bold"))
    ant = sorted([r for r, n in rows if n.upper().startswith("ANTHROPIC")], key=lambda r: r["date"])
    for i, r in enumerate(ant):
        yy = ay + 40 + i * 34
        svg.append(b.txt(60, yy, r["date"], 17, fill=b.MUTED))
        svg.append(b.txt(200, yy, display(r["traveler"])[:30], 17, weight="bold"))
        svg.append(b.txt(520, yy, (r["sponsor"] or "").replace("the Strategic Competition Between the United States and the Chinese Communist Party", "the Chinese Communist Party")[:92], 16))
        svg.append(b.txt(1420, yy, (r["event"] or "").replace("hearing testimony: ", "").strip("“”\"")[:62], 16, fill=b.MUTED))
    height = ay + 40 + len(ant) * 34 + 480
    subtitle = ("What this is: every congressional committee hearing where the official witness list names the witness in a network organisation's role, "
                "from congress.gov, House committee pages and Senate hearing transcripts. For RAND, CNAS, the Carnegie Endowment and FAS only testimony on the work "
                "the network funds (AI, technology and security, biosecurity) counts; each dot is one appearance.")
    footnote = ("<b>What the record does not show.</b> Testifying is not lobbying, and a witness is invited by the committee. People who testified before joining a "
                "network organisation, or in a government role, are not counted. Senate witness lists come from hearing transcripts, which are published months late, "
                "so recent Senate hearings may be missing. An organisation counts only from the date the network first funded that line of its work; earlier "
                "appearances are drawn hollow and not counted. Eric Schmidt appears under the Special Competitive Studies Project and Schmidt Futures, "
                "organisations he and Wendy Schmidt fund and control. " + ("" if FINAL else "Draft figure.") + "")
    bf.figure(stem, f"Network witnesses before Congress: {len(rows)} appearances since 2015", subtitle, "\n".join(svg), footnote, ids,
              height=height, legend_html=legend([(HOUSE, "House hearing"), (SENATE, "Senate hearing"), ("#9a9a9a", "hollow: before the network first funded that line of work")]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
