#!/usr/bin/env python3
"""PLAN.md §4 audit: every id cited by a figure exists; every MB cell traces to rows; exit 0 before any figure ships.

Checks
  1. every row_id in research/*.csv is unique across tables;
  2. every id in members_network.csv t<k>_ids / t<k>_ctx_ids cells (and the LDA filing list) exists in the tables and sits in the table its prefix names;
  3. every MB t<k>_n equals the number of ids in t<k>_ids and every summable t<k>_usd re-sums from the cited rows (within 1 cent); support/oppose splits and other derived MB columns are not re-summed here;
  4. every row id cited in figures/*.html (text or the hidden rows comment) exists; every figure has a PNG;
  5. no MB cell sums across connection types (structural: the script only writes per-type sums; asserted here by recomputation);
  6. semantic: every counted type-1 line is an individual's hard-money line, type-2 a PAC contribution, type-3b a Schedule E or
     electioneering line, type-7/8 entity-bound (no homonym), type-10 a bound entity_id or an Anthropic/Claude payee name, no row whose latest binding decision is bind=no counted, no type-8 row noted as a name mismatch, no LDA UUID twice within one member's type-4a list. These test the rows' labels against the join, not the primary documents.
"""
import csv, re, sys, collections
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "research"
PREFIX_TABLE = {"EN": "entities", "HM": "hard_money", "LC": "lobbyist_contributions", "SP": "super_pac_c4", "VN": "vendors", "TV": "travel",
                "GR": "grants", "FG": "federal_money", "PD": "member_disclosures", "MS": "member_statements", "RD": "revolving_door",
                "SG": "state_government", "LB": "lobbying", "TL": "timeline", "MB": "members_network"}
MEMO = {"jfc_memo", "conduit_memo", "redesignation_memo", "reattribution_memo"}
SUMMABLE = {"1": {"hard_money"}, "2": {"corporate_pac"}, "3a": {"outside_receipt", "transfer"},
            "3b": {"independent_expenditure", "electioneering_communication"}, "4a": set(), "4b": {"hard_money"}, "5": set(),
            "6": {"filed_grant", "award", "federal_award"}, "7": {"federal_award", "award"}, "8": set(), "9": {"travel", "sponsorship"},
            "10": {"vendor"}, "11": set(), "12": {"state_contribution", "lobbying_spend"}}


def load(path):
    with open(path, encoding="utf-8", errors="replace", newline="") as fh:
        return list(csv.DictReader(l for l in fh if not l.startswith("#")))


def main() -> int:
    problems = []
    rows_by_id = {}
    dup = 0
    for prefix, name in PREFIX_TABLE.items():
        p = R / f"{name}.csv"
        if not p.exists():
            continue
        for r in load(p):
            rid = (r.get("row_id") or "").strip()
            if not rid:
                continue
            if rid in rows_by_id:
                dup += 1; problems.append(f"duplicate row_id {rid}")
            if not rid.startswith(prefix):
                problems.append(f"{name}: row_id {rid} does not carry prefix {prefix}")
            rows_by_id[rid] = r
    # 2026-11-26: no cell holds the value of an api_key (17 hard-money cells did, from saved request URLs; corrected the same day)
    for rid, r in rows_by_id.items():
        for col, v in r.items():
            if v and "api_key=" in v and re.search(r"api_key=(?!DEMO_KEY\b|REDACTED\b|omitted\b)[A-Za-z0-9_]{12,}", v):
                problems.append(f"{rid}.{col} holds an api_key value")
    mb = load(R / "members_network.csv")
    if (R / "member_join.csv").exists() and (R / "member_join.csv").read_bytes() != (R / "members_network.csv").read_bytes():
        problems.append("member_join.csv (engine MB path) and members_network.csv (PLAN §4 name) differ")
    types = ["1", "2", "3a", "3b", "4a", "4b", "5", "6", "7", "8", "9", "10", "11", "12"]
    cells = 0
    for m in mb:
        for t in types:
            ids = (m.get(f"t{t}_ids") or "").split()
            ctx = (m.get(f"t{t}_ctx_ids") or "").split()
            cells += 1
            if int(m.get(f"t{t}_n") or 0) != len(ids):
                problems.append(f"{m['row_id']} t{t}_n={m.get(f't{t}_n')} but {len(ids)} ids")
            for rid in ids + ctx:
                if rid not in rows_by_id:
                    problems.append(f"{m['row_id']} t{t} cites missing {rid}")
            if SUMMABLE[t]:
                total = 0.0
                for rid in ids:
                    r = rows_by_id.get(rid, {})
                    mt = (r.get("money_type") or "").strip()
                    if mt in SUMMABLE[t] and mt not in MEMO:
                        try:
                            total += float((r.get("amount_usd") or "0").replace(",", "").replace("$", "") or 0)
                        except ValueError:
                            pass
                if abs(total - float(m.get(f"t{t}_usd") or 0)) > 0.011:
                    problems.append(f"{m['row_id']} t{t}_usd={m.get(f't{t}_usd')} recomputed {total:.2f}")
        # semantic checks (2026-09-23, after the Codex audits; Codex X5b found the README claimed them before they existed)
        UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
        for t in types:
            ids = (m.get(f"t{t}_ids") or "").split()
            seen_uuid = set()
            for rid in ids:
                r = rows_by_id.get(rid, {})
                note = r.get("note") or ""
                mt = (r.get("money_type") or "").strip()
                if re.search(r"\bbind=no\b", note) and not re.search(r"\bbind=yes\b", note):  # a bind=no with no later bind=yes (Codex X8d)
                    problems.append(f"{m['row_id']} t{t} counts bind=no row {rid}")
                if t == "1" and (mt != "hard_money" or (r.get("payer_type") or "") != "individual"):
                    problems.append(f"{m['row_id']} t1 counts {rid} money_type={mt} payer_type={r.get('payer_type')}")
                if t == "2" and mt != "corporate_pac":
                    problems.append(f"{m['row_id']} t2 counts {rid} money_type={mt}")
                if t == "3b" and mt not in ("independent_expenditure", "electioneering_communication"):
                    problems.append(f"{m['row_id']} t3b counts {rid} money_type={mt}")
                if t in ("7", "8") and not (r.get("entity_id") or "").strip():
                    problems.append(f"{m['row_id']} t{t} counts {rid} with no bound entity")
                if t == "8" and "Name match is not" in note:
                    problems.append(f"{m['row_id']} t8 counts homonym row {rid}")
                if t == "10" and not ((r.get("entity_id") or "").strip() or re.search(r"ANTHROPIC|CLAUDE", (r.get("payee") or "").upper())):
                    problems.append(f"{m['row_id']} t10 counts {rid} whose payee is not Anthropic")
                if t == "4a":
                    u = UUID.search((r.get("url") or "") + " " + note)
                    if u:
                        if u.group(1) if False else u.group(0) in seen_uuid:
                            problems.append(f"{m['row_id']} t4a counts LDA filing {u.group(0)} twice ({rid})")
                        seen_uuid.add(u.group(0))
        for col in ("lda_filings_naming_sponsored_bills_ids",):
            for rid in (m.get(col) or "").split():
                if rid not in rows_by_id:
                    problems.append(f"{m['row_id']} {col} cites missing {rid}")
    figs = sorted((ROOT / "figures").glob("congress-*.html"))
    cited = 0; pngs = 0
    for h in figs:
        txt = h.read_text(encoding="utf-8")
        txt = re.sub(r' d="[^"]*"', "", txt)
        for rid in set(re.findall(r"\b((?:EN|HM|LC|SP|VN|TV|GR|FG|PD|MS|RD|SG|LB|TL|MB)\d{2,6})\b", txt)):
            cited += 1
            if rid not in rows_by_id:
                problems.append(f"{h.name} cites missing {rid}")
        if h.with_suffix(".png").exists():
            pngs += 1
        else:
            problems.append(f"{h.name} has no PNG")
    # 2026-10-11 (Kevin: superseded pairs are flagged, not moved): a row a review marked superseded must not count beside its
    # replacement unless the pair is recorded as two distinct facts in research/supersede_reviewed.csv
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
    from casework.supersede_check import open_pairs
    for pair in open_pairs(Path(__file__).resolve().parents[1])[0]:
        problems.append(f"superseded {pair['old_row']} still counts beside {pair['new_row']} on {pair['elements']}")
    print(f"tables={len(PREFIX_TABLE)} row_ids={len(rows_by_id)} duplicates={dup} MB_rows={len(mb)} MB_cells={cells} figures={len(figs)} pngs={pngs} figure_citations={cited} problems={len(problems)}")
    for x in problems[:30]:
        print("PROBLEM", x)
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
