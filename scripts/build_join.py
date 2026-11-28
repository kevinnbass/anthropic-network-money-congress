#!/usr/bin/env python3
"""S9 consolidation (PLAN.md §4), Claude-local, deterministic.

Writes:
  research/members_network.csv   MB rows: one per sitting member (535 roster), plus former members and
                                 candidates that appear anywhere in the tables; one column group per
                                 connection type (count, summed amount within that type only, row ids);
                                 join columns from 05-bills-by-party, 02-horizon-fellows, 04-policy-shops,
                                 and the C34–C36 statements. Nothing sums across types.
  research/timeline_all.csv      every dated row from every table, 2016→2026, one line per row (derived,
                                 not a promoted table; TL keeps curated events).
  research/timeline.csv          appends the anthropic-investors 05-timeline.csv gov-pipeline rows as the
                                 spine (TL ids minted here) when not already present by (date, event).

Counting rules (from REVIEW-PROTOCOL.md and PLAN.md §1.3):
  * only rows bound with role=evidence in case.json count; role=context (reconciliation restatements)
    and role=negative (bounded none-found) are listed in *_ctx_ids but never counted or summed;
  * amounts are summed only within a type and only for that type's summable money_type;
    memo rows (jfc_memo, conduit_memo, redesignation_memo, reattribution_memo) are never summed;
  * 3b and 4b are second hop (hop=2); their totals sit in their own columns;
  * a contribution is not a vote; an independent expenditure is not coordination.
"""
from __future__ import annotations
import csv, json, re, sys, os, datetime, collections
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "research"
ROSTER = R / "inputs/member_roster.csv"
BILLS_DIR = R / "inputs/bills"
HORIZON = R / "inputs/horizon_offices_bills.csv"
CITATIONS = R / "inputs/policy_shop_citations.csv"
SPINE = R / "inputs/timeline_spine.csv"
NOW = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
BIO = re.compile(r"^[A-Z]\d{6}$")
MEMO = {"jfc_memo", "conduit_memo", "redesignation_memo", "reattribution_memo"}



def bind_no(note: str) -> bool:
    """The latest explicit binding decision in an append-only note: bind=yes(was no) overrides an earlier bind=no (Codex X8d, 2026-09-24)."""
    n = note or ""  # a bind=no with no later bind=yes; a correction writes bind=yes(was no) and may quote the old value
    return bool(re.search(r"\bbind=no\b", n)) and not re.search(r"\bbind=yes\b", n)

def load(path: Path) -> tuple[list[str], list[dict[str, str]], list[str]]:
    comments, lines = [], []
    with open(path, encoding="utf-8", errors="replace", newline="") as fh:
        for line in fh:
            (comments if line.startswith("#") else lines).append(line)
    rows = list(csv.DictReader(lines))
    header = list(rows[0].keys()) if rows else next(csv.reader(lines))
    return header, rows, comments


def money(v: str) -> float:
    v = (v or "").strip().replace(",", "").replace("$", "")
    try:
        return float(v)
    except ValueError:
        return 0.0


def date_of(row: dict[str, str]) -> str:
    for k in ("date", "start", "event_date", "period"):
        v = (row.get(k) or "").strip()
        m = re.match(r"(\d{4}-\d{2}-\d{2})", v) or re.match(r"(\d{4}-\d{2})", v) or re.match(r"(\d{4})", v)
        if m:
            return m.group(1)
    return ""


def receipt_day(row: dict[str, str]) -> str:
    """Return a usable filed day for the K13 receipt and expenditure comparison."""
    day = (row.get("date") or "").strip()
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", day):
        return ""
    try:
        datetime.date.fromisoformat(day)
    except ValueError:
        return ""
    return day


def main() -> int:
    # roles from case.json bindings
    case = json.load(open(ROOT / "case.json", encoding="utf-8"))
    role: dict[str, str] = {}
    for cl in case["claims"]:
        for el in cl.get("elements", []):
            for b in el.get("bindings", []):
                rid = b.get("row_id", "")
                r = b.get("role", "evidence")
                # a row bound as evidence anywhere counts as evidence
                if role.get(rid) != "evidence":
                    role[rid] = r
    tables = {}
    for name in ["hard_money", "lobbyist_contributions", "super_pac_c4", "vendors", "travel", "grants",
                 "federal_money", "member_disclosures", "member_statements", "revolving_door",
                 "state_government", "lobbying", "entities", "timeline"]:
        tables[name] = load(R / f"{name}.csv")[1]

    roster = list(csv.DictReader(open(ROSTER, encoding="utf-8")))
    # 2026-11-26 (PLAN amendment S43; Kevin: "members serving today"): the sitting cohort is the members serving on the as_of_date of
    # research/roster_serving.csv (one line per voting seat, built from the chambers' own lists by lane C185 and checked by audit X65b).
    # A member of the companion roster (the Congress as first seated) who no longer serves stays in the join as former_or_other; a
    # member seated since is added from the serving roster. A vacant seat has no line here; figures state the vacancies.
    serving: dict[str, dict] = {}
    _rp = R / "roster_serving.csv"
    if _rp.exists():
        serving = {x["member_bioguide"]: x for x in csv.DictReader(l for l in open(_rp, encoding="utf-8", newline="") if not l.startswith("#"))
                   if BIO.match(x.get("member_bioguide") or "")}
    members: dict[str, dict] = {}
    for r in roster:
        b = r["member_id"].strip()
        members[b] = {"key": b, "member_bioguide": b, "member_name": r["member_name"], "party": r["party"],
                      "chamber": r["chamber"], "state": r["state"], "district": r["district"],
                      "cohort": "sitting" if (not serving or b in serving) else "former_or_other", "fec_candidate_id": r["fec_candidate_ids"]}
    for b, x in serving.items():
        if b not in members:
            members[b] = {"key": b, "member_bioguide": b, "member_name": x["member_name"], "party": x["party"], "chamber": x["chamber"],
                          "state": x["state"], "district": x["district"], "cohort": "sitting", "fec_candidate_id": x["fec_candidate_ids"].split(";")[0].split("|")[0].split(",")[0].strip()}
    # former members seen anywhere
    seen_names: dict[str, tuple[str, str, str]] = {}
    for name, rows in tables.items():
        col = "sponsor_bioguide" if name == "federal_money" else "member_bioguide"
        for r in rows:
            b = (r.get(col) or "").strip()
            if BIO.match(b) and b not in members:
                seen_names.setdefault(b, (r.get("member_name") or r.get("sponsor_name") or r.get("speaker") or "",
                                          r.get("party") or "", r.get("chamber") or ""))
    import glob as _glob
    legis: dict[str, dict] = {}
    for lf in _glob.glob(str(R / "primary" / "*" / "legislators-*.json")):
        try:
            for x in json.load(open(lf, encoding="utf-8")):
                b = (x.get("id") or {}).get("bioguide", "")
                terms = x.get("terms") or []
                if b and terms:
                    t = terms[-1]
                    legis.setdefault(b, {"name": (x.get("name") or {}).get("official_full") or f"{(x.get('name') or {}).get('first','')} {(x.get('name') or {}).get('last','')}".strip(),
                                         "party": {"Democrat": "D", "Republican": "R", "Independent": "I"}.get(t.get("party", ""), t.get("party", "")[:1]),
                                         "chamber": {"rep": "House", "sen": "Senate"}.get(t.get("type", ""), ""), "state": t.get("state", "")})
        except Exception:
            continue
    for b, (nm, party, chamber) in sorted(seen_names.items()):
        lg = legis.get(b, {})
        members[b] = {"key": b, "member_bioguide": b, "member_name": nm or lg.get("name", ""), "party": party or lg.get("party", ""), "chamber": chamber or lg.get("chamber", ""),
                      "state": lg.get("state", ""), "district": "", "cohort": "former_or_other", "fec_candidate_id": ""}
    # candidates: entity rows with an FEC candidate id and no bioguide
    cand_committees: dict[str, set[str]] = collections.defaultdict(set)
    cid_to_bio = {(e.get("fec_candidate_id") or "").strip(): (e.get("bioguide_id") or "").strip() for e in tables["entities"] if (e.get("fec_candidate_id") or "").strip() and (e.get("bioguide_id") or "").strip()}
    for b, cid in ((b, c) for c, b in cid_to_bio.items()):
        if b in members and not members[b]["fec_candidate_id"]:
            members[b]["fec_candidate_id"] = cid
    for e in tables["entities"]:
        cid = (e.get("fec_candidate_id") or "").strip()
        if cid in cid_to_bio or "superseded" in (e.get("note") or "").lower():
            continue  # AUDIT-A2 finding 2: a former member keyed by bioguide is never also a CAND: row
        if cid and not (e.get("bioguide_id") or "").strip() and (e.get("entity_type") or "") in ("person", "") and role.get(e["row_id"]) == "evidence":
            key = "CAND:" + cid
            if key not in members:
                members[key] = {"key": key, "member_bioguide": "", "member_name": e.get("name", ""), "party": "",
                                "chamber": "", "state": "", "district": "", "cohort": "candidate", "fec_candidate_id": cid}
            if (e.get("fec_committee_id") or "").strip():
                cand_committees[key].add(e["fec_committee_id"].strip())
    committee_to_key = {c: k for k, cs in cand_committees.items() for c in cs}

    # connection type assignment
    TYPES = ["1", "2", "3a", "3b", "4a", "4b", "5", "6", "7", "8", "9", "10", "11", "12"]
    # AUDIT-A2 finding 4: a conduit earmark is the recipient's own receipt and is never summed twice, so type 1 sums hard_money and refund only
    SUMMABLE = {"1": {"hard_money"}, "2": {"corporate_pac"}, "3a": {"outside_receipt", "transfer"},
                "3b": {"independent_expenditure", "electioneering_communication"}, "4a": set(), "4b": {"hard_money"},
                "5": set(), "6": {"filed_grant", "award", "federal_award"}, "7": {"federal_award", "award"}, "8": set(),
                "9": {"travel", "sponsorship"}, "10": {"vendor"}, "11": set(), "12": {"state_contribution", "lobbying_spend"}}
    acc: dict[str, dict[str, dict]] = {k: {t: {"ids": [], "ctx": [], "usd": 0.0, "n": 0, "support": 0.0, "oppose": 0.0,
                                               "stance": collections.Counter(), "direction": collections.Counter()} for t in TYPES}
                                       for k in members}

    def add(key: str, t: str, r: dict[str, str], force_ctx: bool = False):
        a = acc[key][t]
        rid = r["row_id"]
        if role.get(rid) == "evidence" and not force_ctx:
            a["ids"].append(rid); a["n"] += 1
            mt = (r.get("money_type") or "").strip()
            if mt in SUMMABLE[t] and mt not in MEMO:
                amt = money(r.get("amount_usd", ""))
                a["usd"] += amt
                so = (r.get("support_oppose") or "").strip().lower()
                if t == "3b" and so in ("support", "oppose"):
                    a[so] += amt
        else:
            a["ctx"].append(rid)
        if t == "11":
            a["stance"][(r.get("stance") or "").strip() or "unstated"] += 1
        if t == "5":
            a["direction"][(r.get("direction") or "").strip() or "unstated"] += 1

    def keys_for(r: dict[str, str], col: str = "member_bioguide") -> list[str]:
        out = []
        b = (r.get(col) or "").strip()
        if BIO.match(b) and b in members:
            out.append(b)
        pid = (r.get("payee_id") or "").strip()
        if pid in committee_to_key:
            out.append(committee_to_key[pid])
        cid = (r.get("payee_id") or "").strip()
        if "CAND:" + cid in members:
            out.append("CAND:" + cid)
        return sorted(set(out))

    # 2026-09-29 (audit X33a): registration windows per registrant; the registrant id comes from the row's note, else from
    # another row of the same registrant name
    WIN = collections.defaultdict(list)
    for w in csv.DictReader(l for l in open(ROOT / "research/lb_network_windows.csv", encoding="utf-8") if not l.startswith("#")):
        if w["status"] == "window":
            WIN[w["registrant_id"]].append((w["window_start"], w["window_end"] or "9999-12-31"))
    def reg_of(r):
        n = r.get("note") or ""
        rid = re.search(r"(?:lda_registrant_id=|registrant=[^;]+ id=)(\d+)", n)
        nm = re.search(r"registrant=([^;]+?)(?: id=|;)", n)
        return (rid.group(1) if rid else ""), (nm.group(1).strip() if nm else "")
    REG_BY_NAME = {}
    for _t in ("lobbyist_contributions", "hard_money"):
        for _r in tables[_t]:
            _i, _n = reg_of(_r)
            if _i and _n:
                REG_BY_NAME.setdefault(_n, _i)
    def in_4b_window(r):
        i, nm = reg_of(r)
        i = i or REG_BY_NAME.get(nm, "")
        d = (r.get("date") or "").strip()[:10]
        return bool(d) and any(s <= d <= e for s, e in WIN.get(i, ()))
    lc_keys = {((r.get("payer") or "").strip().upper(), (r.get("payee") or "").strip().upper(), money(r.get("amount_usd", "")), (r.get("date") or "").strip()) for r in tables["lobbyist_contributions"]}
    for r in tables["hard_money"]:
        mt = (r.get("money_type") or "").strip()
        hop = (r.get("hop") or "").strip()
        if hop == "2":
            # AUDIT-A2 finding 1: lobbyists' own contributions stored in HM before the LC table existed are type 4b;
            # when the same item is held as an LC row the HM copy is reconciliation (context), never counted twice
            key = ((r.get("payer") or "").strip().upper(), (r.get("payee") or "").strip().upper(), money(r.get("amount_usd", "")), (r.get("date") or "").strip())
            for k in keys_for(r):
                if key in lc_keys:
                    acc[k]["4b"]["ctx"].append(r["row_id"])
                else:
                    add(k, "4b", r, force_ctx=not in_4b_window(r))  # 2026-09-29 (X33a): same registration window as the LC rows
            continue
        if mt == "transfer":
            # AUDIT-A2 finding 4: a transfer is 3a money when the payee is a super PAC or c4; otherwise it is not typed
            if (r.get("payee_type") or "") in ("super_pac", "hybrid_pac", "c4", "nonconnected_pac"):
                for k in keys_for(r): add(k, "3a", r)
            continue
        # 2026-09-23 (Codex X3 #3, #4): a PAC payer (corporate or nonconnected network PAC) is type 2; a type-1 membership needs a
        # hard_money line (a refund, a blank-typed line or a memo is context for the member), and refunds are never summed.
        pt = (r.get("payer_type") or "")
        t = "2" if mt == "corporate_pac" or pt == "corporate_pac" or (pt == "nonconnected_pac" and re.search(r"ANTHROPAC|RESPONSIBLE INNOVATION|ARI PAC", (r.get("payer") or "").upper())) else "1"
        # 2026-09-23 (Codex X1b #10): type 1 is an individual's money; a committee-to-committee line or an outgoing disbursement is context
        for k in keys_for(r): add(k, t, r, force_ctx=(t == "1" and (mt != "hard_money" or pt != "individual")) or (t == "2" and mt not in ("corporate_pac", "")))
    # 2026-09-23 (Codex X3 #5, #6): type 3b is a Schedule E line (independent_expenditure or electioneering_communication) by a
    # committee into which the record holds an itemised network receipt (an SP outside_receipt/transfer, or a hop-1 hard-money or
    # transfer line whose payee is that committee). An issuer statement with hop=2 is context, and a Schedule E line by a committee
    # with no itemised network receipt in the record is context (the wider universe stays drawn on figure 14 as such).
    def ckey(r, side):
        cid = (r.get(f"{side}_id") or "").strip().upper(); nm = re.sub(r"[^A-Z0-9]", "", (r.get(side) or "").upper())
        return cid or NAME2ID.get(nm, nm)
    NAME2ID = {}
    for r in tables["super_pac_c4"] + tables["hard_money"]:
        for side in ("payer", "payee"):
            cid = (r.get(f"{side}_id") or "").strip().upper(); nm = re.sub(r"[^A-Z0-9]", "", (r.get(side) or "").upper())
            if cid.startswith("C") and nm:
                NAME2ID.setdefault(nm, cid)
    # 2026-11-27 (K13; gap sweep G13, lane GS9; PLAN bullet of that day): a committee's spending counts from the day of its earliest
    # itemised network receipt on record, that day included; spending dated before it is context (money cannot flow backwards; the
    # same rule as 4b's registration window). GS9 searched the FEC's Schedule A from 2015 for an earlier network receipt at each of the
    # 34 committees: 31 none found, two found (promoted as C197 and C198), one not public (Public First Action's Form 9).
    linked = {}
    unresolved_dates = {"receipts": [], "expenditures": []}

    def link(r):
        d = receipt_day(r)
        if not d:
            unresolved_dates["receipts"].append(r["row_id"])
            return
        k = ckey(r, "payee")
        linked[k] = min(linked.get(k, d), d)

    for r in tables["super_pac_c4"]:
        if role.get(r["row_id"]) == "evidence" and (r.get("money_type") or "") in ("outside_receipt", "transfer"):
            link(r)
    for r in tables["hard_money"]:
        if role.get(r["row_id"]) == "evidence" and (r.get("money_type") or "") in ("hard_money", "transfer") and (r.get("hop") or "") == "1":
            link(r)
    for r in tables["super_pac_c4"]:
        mt = (r.get("money_type") or "").strip()
        is_ie = mt in ("independent_expenditure", "electioneering_communication")
        t = "3b" if is_ie or (r.get("hop") or "") == "2" else "3a"
        day = receipt_day(r) if is_ie else ""
        if is_ie and not day and role.get(r["row_id"]) == "evidence":
            unresolved_dates["expenditures"].append(r["row_id"])
        first = linked.get(ckey(r, "payer")) if t == "3b" else None
        force_ctx = t == "3b" and (not day or first is None or day < first)
        for k in keys_for(r):
            add(k, t, r, force_ctx=force_ctx)
    if any(unresolved_dates.values()):
        print("  3b unresolved-date:", " ".join(f"{kind}={len(ids)}" for kind, ids in unresolved_dates.items()))
    # 2026-09-23 (Codex X1b #1): type 4b is the lobbyist's own FECA money; an LD-203 item whose contributor is a PAC is context
    # 2026-09-29 (audit X33a, PLAN §1.3 "while registered for a network client"): an item counts only if dated inside a window in
    # which the filing's registrant was registered for a network client (research/lb_network_windows.csv); other items are context
    for r in tables["lobbyist_contributions"]:
        n = r.get("note") or ""
        caf = (re.search(r"contributor_as_filed=([^;]+)", n) or [None, ""])[1].strip().upper()
        pac_payer = (r.get("payer_type") or "") in ("nonconnected_pac", "corporate_pac") or ("PAC" in caf.split() or caf.endswith("PAC") or ".ORG" in caf)
        for k in keys_for(r): add(k, "4b", r, force_ctx=pac_payer or not in_4b_window(r))
    for r in tables["revolving_door"]:
        for k in keys_for(r): add(k, "5", r)
    for r in tables["grants"]:
        for k in keys_for(r): add(k, "6", r)
    # 2026-09-23 (Codex X3 #9): a type-7 row must be bound to a network entity; a generic AI bill or agreement row is context
    for r in tables["federal_money"]:
        for k in keys_for(r, "sponsor_bioguide"): add(k, "7", r, force_ctx=not (r.get("entity_id") or "").strip())
    # audit-5 2026-09-17 (Claude figure audit): a type-8 connection is a holding the reviewer bound to a network
    # entity. Index listings that only show a filing exists ("filing exists", "no ... exposure", "Index row only")
    # and name matches the lane itself marked "Name match is not identity" (Constellation Energy / Constellation
    # Brands stock against the network org Constellation, EN390) are kept as context, never counted.
    for r in tables["member_disclosures"]:
        bound = (bool((r.get("entity_id") or "").strip()) and "Name match is not" not in (r.get("note") or "")
                 and not bind_no(r.get("note") or ""))  # 2026-09-20: vision lanes mark look-alikes bind=no
        for k in keys_for(r): add(k, "8", r, force_ctx=not bound)
    # 2026-09-20: the Senate gift-rule vision lanes record similar-name sponsors as rows with bind=no (kept so the
    # look-alike is on the record); a row the lane or reviewer marked bind=no is context, never a type-9 connection.
    for r in tables["travel"]:
        nb = bool(bind_no(r.get("note") or ""))
        for k in keys_for(r): add(k, "9", r, force_ctx=nb)
    # audit-5 2026-09-17 (Claude figure audit): PLAN §1.3 type 10 is a campaign or office paying a network firm. The vendor
    # lanes also pulled OpenAI/ChatGPT comparison lines and whole Schedule B disbursement lists of network-backed committees;
    # a member-bound vendor row counts only when the payee is a network firm (entity_id bound, or Anthropic / Claude by name).
    for r in tables["vendors"]:
        net = bool((r.get("entity_id") or "").strip()) or bool(re.search(r"ANTHROPIC|CLAUDE", (r.get("payee") or "").upper()))
        for k in keys_for(r): add(k, "10", r, force_ctx=not net)
    for r in tables["member_statements"]:
        for k in keys_for(r): add(k, "11", r)
    # type 12: state rows name state officials, not members; a row joins only when official_name equals a
    # roster member_name exactly (state legislators who later entered Congress); otherwise unjoined.
    by_name: dict[str, list[str]] = collections.defaultdict(list)
    for k, m in members.items():
        if m["member_name"]:
            by_name[m["member_name"].strip().lower()].append(k)
    for r in tables["state_government"]:
        nm = (r.get("official_name") or "").strip().lower()
        st = (r.get("state") or "").strip().upper()
        # AUDIT-A2 finding 3: an exact name is not an identity; the SG state must match the member's roster state
        cands = [k for k in by_name.get(nm, []) if members[k]["state"] and members[k]["state"].upper() == st]
        if len(cands) == 1:
            add(cands[0], "12", r)

    # 05 join: bills sponsored / cosponsored, restriction vs promotion
    src = json.load(open(BILLS_DIR / "research/source_records.json", encoding="utf-8"))
    final = {x["bill_number"]: x for x in csv.DictReader(open(BILLS_DIR / "research/classification_final.csv", encoding="utf-8"))}
    sponsor_of: dict[str, str] = {}
    # X39 E27 (2026-10-11): a bill number names a bill only within one Congress; the companion records carry it in the BILLSTATUS path
    congress_of_bill = {rec["bill_number"]: m.group(1) for rec in src if (m := re.search(r"BILLSTATUS/(\d+)/", rec.get("source_url") or ""))}
    for rec in src:
        p = BILLS_DIR / rec["raw_path"]
        if p.exists():
            m = re.search(r"<sponsors>.*?<bioguideId>([A-Z]\d{6})</bioguideId>", p.read_text(encoding="utf-8", errors="replace"), re.S)
            if m:
                sponsor_of[rec["bill_number"]] = m.group(1)
    bills_by_member: dict[str, list[str]] = collections.defaultdict(list)
    for bill, b in sponsor_of.items():
        bills_by_member[b].append(bill)
    cos = collections.defaultdict(set)
    for x in csv.DictReader(open(BILLS_DIR / "research/cosponsor_records.csv", encoding="utf-8")):
        if x.get("active", "") == "Y" and BIO.match(x.get("bioguideId", "")):
            cos[x["bioguideId"]].add(x["bill_number"])
    # 4a join: LDA filings naming a bill the member sponsored
    def norm_bill(s: str) -> str:
        return re.sub(r"[\s.]", "", s.upper())
    lb_norm: dict[str, list[str]] = collections.defaultdict(list)
    # 2026-11-26 (PLAN §1.3 amendment and §1.1a; re-check X66b-5): a report of a multi-line institution links to a bill only where
    # research/lb_bill_scope.csv says the report names that bill on its network-funded line. The table lists those clients by id
    # and, per report and bill, the section that names the bill; a bill of such a client with no line there links nothing.
    scope_clients: set[str] = set(); scope_ok: set[tuple[str, str]] = set()
    _sp = R / "lb_bill_scope.csv"
    if _sp.exists():
        for x in csv.DictReader(l for l in open(_sp, encoding="utf-8", newline="") if not l.startswith("#")):
            scope_clients.add((x.get("client_id") or "").strip())
            if x.get("in_funded_line") == "yes":
                scope_ok.add((x["row_id"], x["bill_key"]))
    # 2026-09-23 (Codex X3 #2): one LDA filing counts once; bill-name restatement rows that reuse a filing's UUID collapse onto the lowest row id
    seen_uuid: dict[str, str] = {}
    for r in sorted(tables["lobbying"], key=lambda r: (len(r["row_id"]), r["row_id"])):
        if role.get(r["row_id"]) != "evidence":
            continue
        u = re.search(r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", (r.get("url") or "") + " " + (r.get("note") or ""))  # 2026-09-24 (Grok A9 #19): the UUID may sit in the note
        if u:
            if u.group(1) in seen_uuid:
                continue
            seen_uuid[u.group(1)] = r["row_id"]
        y = (r.get("period") or r.get("date") or "")[:4]
        cg = str((int(y) - 1789) // 2 + 1) if y.isdigit() else ""  # the 1st Congress convened in 1789
        for bn in re.findall(r"\b(?:H\.?\s?R\.?|S\.?|H\.?\s?J\.?\s?Res\.?|H\.?\s?Res\.?|S\.?\s?Res\.?)\s?\d+", r.get("bills_named") or "", re.I):
            if cg:
                if (r.get("client_id") or "").strip() in scope_clients and (r["row_id"], f"{cg}:{norm_bill(bn)}") not in scope_ok:
                    continue
                lb_norm[f"{cg}:{norm_bill(bn)}"].append(r["row_id"])
    # 4a sponsor key (2026-11-26, PLAN amendment S38; audits X64d and X65a): a lobbying report links to a member through a stand-alone
    # bill the report names and the member sponsored, whether or not the companion AI-bill set above holds the bill.
    # research/bill_sponsor_keys.csv lists every bill the evidence reports name, with its sponsor, its kind and whether it is counted:
    # broad vehicles (annual authorisations, appropriations, budget, reconciliation) and numbers whose title does not match the filing
    # are listed there with counted=no. A filing that prints a number without a Congress and names a bill of the previous Congress is
    # keyed by cited_as_congress (the Congress of the report's year) and counted only for the rows in cited_by.
    lb_by_sponsor: dict[str, set[str]] = collections.defaultdict(set)
    not_counted: set[str] = set()  # "<congress>:<bill>" keys the table lists with counted=no; they link from neither source
    _kp = R / "bill_sponsor_keys.csv"
    if _kp.exists():
        for x in csv.DictReader(l for l in open(_kp, encoding="utf-8", newline="") if not l.startswith("#")):
            if x.get("counted") != "yes":
                not_counted.add(f"{x['congress']}:{norm_bill(x['bill'])}")
                continue
            if not BIO.match(x.get("sponsor_bioguide") or ""):
                continue
            hits = set(lb_norm.get(f"{x.get('cited_as_congress') or x['congress']}:{norm_bill(x['bill'])}", ()))
            if (x.get("cited_by") or "").strip():
                hits &= set(x["cited_by"].split())
            lb_by_sponsor[x["sponsor_bioguide"]].update(hits)
    # 02 join: Horizon fellow in office
    horizon: dict[str, list[str]] = collections.defaultdict(list)
    for x in csv.DictReader(open(HORIZON, encoding="utf-8")):
        if x.get("kind") == "office_summary" and BIO.match(x.get("member_bioguide", "")):
            horizon[x["member_bioguide"]].append(f"{x['fellow']} ({x['placement_start_year']}-{x['placement_end_year']}; {x['row_id']})")
    # 04 join: policy-shop hearing documents where the member chaired (chair_name matched to the roster)
    def last_first(nm: str) -> tuple[str, str]:
        nm = re.sub(r"\(.*?\)", "", nm).replace(",", " ").strip()
        toks = [t for t in re.split(r"\s+", nm) if t and t[0].isalpha()]
        return (toks[-1].lower(), toks[0].lower()) if toks else ("", "")
    roster_idx: dict[str, list[str]] = collections.defaultdict(list)
    for k, m in members.items():
        if m["cohort"] == "sitting":
            ln, fn = last_first(m["member_name"])
            roster_idx[ln].append(k)
    chair_docs: dict[str, set[str]] = collections.defaultdict(set)
    for x in csv.DictReader(open(CITATIONS, encoding="utf-8")):
        ch = (x.get("chair_name") or "").strip()
        if not ch:
            continue
        ln, fn = last_first(ch)
        cands = roster_idx.get(ln, [])
        if len(cands) == 1:
            chair_docs[cands[0]].add(x.get("document") or x.get("row_id"))

    # 2026-09-23 (Codex X3 #3): a PAC contribution appears on the PAC's Schedule B and the recipient's Schedule A; count one line per
    # (payer, payee, date, amount) in type 2, the later copies becoming context for that member
    rows_by_id = {r["row_id"]: r for t in tables.values() for r in t}
    for k, a in acc.items():
        seen2 = {}; keep = []
        for rid in sorted(a["2"]["ids"], key=lambda x: (len(x), x)):
            r = rows_by_id.get(rid, {})
            key2 = (re.sub(r"[^A-Z0-9]", "", (r.get("payer") or "").upper()), re.sub(r"[^A-Z0-9]", "", (r.get("payee") or "").upper()), (r.get("date") or "").strip(), round(money(r.get("amount_usd", "")), 2))
            sched = "B" if "schedule_b" in (r.get("url") or "") else "A"  # 2026-09-23 (Codex X1b #5): collapse only a Schedule A copy against a Schedule B copy
            if key2 in seen2 and seen2[key2] != sched:
                a["2"]["ctx"].append(rid); a["2"]["n"] -= 1
                if (r.get("money_type") or "") in SUMMABLE["2"]:
                    a["2"]["usd"] -= money(r.get("amount_usd", ""))
            else:
                seen2[key2] = sched; keep.append(rid)
        a["2"]["ids"] = keep

    # write MB
    fields = ["row_id", "key", "member_bioguide", "member_name", "party", "chamber", "state", "district", "cohort", "fec_candidate_id"]
    for t in TYPES:
        fields += [f"t{t}_n", f"t{t}_usd", f"t{t}_ids", f"t{t}_ctx_ids"]
    fields += ["t3b_support_usd", "t3b_oppose_usd", "t5_directions", "t11_stances",
               "bills_sponsored_n", "bills_sponsored", "bills_restrict_n", "bills_promote_n", "bills_other_n",
               "bills_cosponsored_n", "lda_filings_naming_sponsored_bills_n", "lda_filings_naming_sponsored_bills_ids",
               "horizon_fellows_n", "horizon_fellows", "policy_shop_docs_as_chair_n", "any_connection",
               "source_url", "quote_300", "checked_utc", "note"]
    out_rows = []
    # PLAN §1.2: a candidate is in the join only if network money reached or targeted them; a name-search homonym with no rows is not
    for k in [k for k, m in members.items() if m["cohort"] == "candidate"]:
        if all(acc[k][t]["n"] == 0 and not acc[k][t]["ctx"] for t in TYPES):
            del members[k]; del acc[k]
    order = sorted(members.values(), key=lambda m: ({"sitting": 0, "former_or_other": 1, "candidate": 2}[m["cohort"]], m["chamber"], m["state"], m["member_name"]))
    for i, m in enumerate(order, 1):
        k = m["key"]; a = acc[k]
        row = {"row_id": f"MB{i:04d}", **{f: m.get(f, "") for f in fields[1:10]}}
        anyc = False
        for t in TYPES:
            row[f"t{t}_n"] = a[t]["n"]; row[f"t{t}_usd"] = f"{a[t]['usd']:.2f}" if SUMMABLE[t] else ""
            row[f"t{t}_ids"] = " ".join(a[t]["ids"]); row[f"t{t}_ctx_ids"] = " ".join(a[t]["ctx"])
            anyc = anyc or a[t]["n"] > 0
        row["t3b_support_usd"] = f"{a['3b']['support']:.2f}"; row["t3b_oppose_usd"] = f"{a['3b']['oppose']:.2f}"
        row["t5_directions"] = "; ".join(f"{d}={n}" for d, n in sorted(a["5"]["direction"].items()))
        row["t11_stances"] = "; ".join(f"{d}={n}" for d, n in sorted(a["11"]["stance"].items()))
        b = m["member_bioguide"]
        bills = sorted(bills_by_member.get(b, []))
        row["bills_sponsored_n"] = len(bills); row["bills_sponsored"] = "; ".join(bills)
        cls = collections.Counter(final.get(bn, {}).get("final_class", "OTHER") for bn in bills)
        row["bills_restrict_n"] = cls.get("RESTRICT", 0); row["bills_promote_n"] = cls.get("PROMOTE", 0)
        row["bills_other_n"] = len(bills) - cls.get("RESTRICT", 0) - cls.get("PROMOTE", 0)
        row["bills_cosponsored_n"] = len(cos.get(b, ()))
        lb_ids = sorted({rid for bn in bills if f"{congress_of_bill.get(bn, '')}:{norm_bill(bn)}" not in not_counted
                         for rid in lb_norm.get(f"{congress_of_bill.get(bn, '')}:{norm_bill(bn)}", [])} | lb_by_sponsor.get(b, set()))
        row["lda_filings_naming_sponsored_bills_n"] = len(lb_ids); row["lda_filings_naming_sponsored_bills_ids"] = " ".join(lb_ids)
        # type 4a per member = LDA filings that name a bill this member sponsored (no amount is attributed to a member)
        row["t4a_n"] = len(lb_ids); row["t4a_ids"] = " ".join(lb_ids); anyc = anyc or bool(lb_ids)
        hf = horizon.get(b, [])
        row["horizon_fellows_n"] = len(hf); row["horizon_fellows"] = "; ".join(hf)
        row["policy_shop_docs_as_chair_n"] = len(chair_docs.get(k, ()))
        row["any_connection"] = "yes" if (anyc or bills or hf) else "no"
        row["source_url"] = "research/*.csv (row ids in the *_ids cells); 06-ai-money-per-member/research/member_roster.csv; 05-bills-by-party/research; 02-horizon-fellows/research/offices_bills.csv; 04-policy-shops/research/citations.csv"
        row["quote_300"] = ""
        row["checked_utc"] = NOW
        row["note"] = ("derived by scripts/build_join.py; counts are role=evidence rows only, *_ctx_ids are reconciliation/none-found rows never counted; "
                       "each t*_usd sums one money type only and never across types; 3b and 4b are hop=2 (the principal did not direct the second hop); "
                       "a contribution is not a vote and an independent expenditure is not coordination; state rows (type 12) join only on an exact official-name match")
        out_rows.append(row)
    # the engine registers MB at research/member_join.csv (casework.json); PLAN.md §4 names research/members_network.csv.
    # both are written from the same rows by this script and scripts/audit.py asserts they are byte-identical.
    for fname in ("member_join.csv", "members_network.csv"):
        # 2026-11-26 (X66-1931): the header states the cohort the rows carry: the dated serving roster when it is present
        _dates = sorted({x.get("as_of_date", "") for x in serving.values()})
        cohort_line = (f"one row per member serving on {_dates[-1]} by research/roster_serving.csv ({len(serving)} members; cohort=sitting)" if serving
                       else "one row per member of the 535 cohort")
        with open(R / fname, "w", encoding="utf-8", newline="") as fh:
            fh.write(f"# congress MB table (member_join.csv = engine path; members_network.csv = PLAN.md §4 name; identical); derived join written by scripts/build_join.py {NOW}; {cohort_line} plus former members and candidates that appear in the tables; one column group per connection type: t<k>_n (evidence rows), t<k>_usd (sum within that type only), t<k>_ids, t<k>_ctx_ids (context/negative rows, never counted); no column sums across types; rebuilt in place on every run, never hand-edited\n")
            w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n"); w.writeheader(); w.writerows(out_rows)
    print(f"MB rows={len(out_rows)} sitting={sum(1 for m in order if m['cohort']=='sitting')} former={sum(1 for m in order if m['cohort']=='former_or_other')} candidates={sum(1 for m in order if m['cohort']=='candidate')} any_connection={sum(1 for r in out_rows if r['any_connection']=='yes')}")
    for t in TYPES:
        n = sum(r[f"t{t}_n"] for r in out_rows); usd = sum(float(r[f"t{t}_usd"] or 0) for r in out_rows)
        print(f"  type {t:>2}: members_with_rows={sum(1 for r in out_rows if r[f't{t}_n']>0):4d} rows={n:6d} usd={usd:,.0f}")

    # timeline_all (derived)
    tl_fields = ["row_id", "table", "conn_type", "date", "actor", "counterparty", "member_bioguide", "money_type", "hop", "amount_usd", "role", "note_120"]
    tmap = {"hard_money": ("1/2", "payer", "payee"), "lobbyist_contributions": ("4b", "payer", "payee"), "super_pac_c4": ("3a/3b", "payer", "payee"),
            "vendors": ("10", "payer", "payee"), "travel": ("9", "sponsor", "traveler"), "grants": ("6", "payer", "payee"), "federal_money": ("7", "agency", "recipient"),
            "member_disclosures": ("8", "filer", "asset"), "member_statements": ("11", "speaker", "entity_named"), "revolving_door": ("5", "person", "org_now"),
            "state_government": ("12", "payer", "payee"), "lobbying": ("4a", "registrant", "client"), "timeline": ("TL", "people_orgs", "event")}
    tl_rows = []
    # 2026-09-29 (audit X34-0596): a hop-2 hard_money row is a lobbyist's LD-203 item (type 4b), not a campaign contribution, and one
    # that restates an evidence LC row (same payee, date and amount) is a copy the timeline does not count again
    def _lk(r):
        return (re.sub(r"[^A-Z0-9]", "", (r.get("payee") or "").upper()), money(r.get("amount_usd", "")), (r.get("date") or "").strip()[:10])
    lc_ev = {_lk(r) for r in tables["lobbyist_contributions"] if role.get(r["row_id"]) == "evidence"}
    for name, (ct, a_col, c_col) in tmap.items():
        for r in tables[name]:
            d = date_of(r)
            if not d or not ("2016" <= d[:4] <= "2026"):
                continue
            rl = role.get(r["row_id"], "")
            if name == "hard_money" and (r.get("hop") or "").strip() == "2":
                ct_r = "4b"
                if rl == "evidence" and _lk(r) in lc_ev:
                    rl = "context"
            else:
                ct_r = ct
            tl_rows.append({"row_id": r["row_id"], "table": name, "conn_type": ct_r, "date": d, "actor": (r.get(a_col) or "")[:80], "counterparty": (r.get(c_col) or "")[:80],
                            "member_bioguide": (r.get("member_bioguide") or r.get("sponsor_bioguide") or ""), "money_type": r.get("money_type", ""), "hop": r.get("hop", ""),
                            "amount_usd": r.get("amount_usd", ""), "role": rl, "note_120": (r.get("note") or r.get("event") or "")[:120]})
    tl_rows.sort(key=lambda x: (x["date"], x["table"], x["row_id"]))
    with open(R / "timeline_all.csv", "w", encoding="utf-8", newline="") as fh:
        fh.write(f"# congress derived timeline_all.csv written by scripts/build_join.py {NOW} (PLAN.md §4): every dated row from every table, 2016-2026, one line per row; not a promoted table (TL holds the curated events); rebuilt in place\n")
        w = csv.DictWriter(fh, fieldnames=tl_fields, lineterminator="\n"); w.writeheader(); w.writerows(tl_rows)
    print(f"timeline_all rows={len(tl_rows)}")

    # TL spine: append 05-timeline rows not already present by (date, event)
    tl_header, tl_existing, tl_comments = load(R / "timeline.csv")
    have = {((r.get("date") or "").strip(), (r.get("event") or "").strip().lower()) for r in tl_existing}
    ids = [int(re.sub(r"^TL", "", r["row_id"])) for r in tl_existing if re.match(r"^TL\d+$", r["row_id"])]
    nxt = max(ids) + 1 if ids else 1
    added = []
    for s in csv.DictReader(open(SPINE, encoding="utf-8")):
        keyp = ((s.get("date") or "").strip(), (s.get("event") or "").strip().lower())
        if keyp in have:
            continue
        added.append({"row_id": f"TL{nxt:04d}", "date": s.get("date", ""), "event": s.get("event", ""), "people_orgs": s.get("people_orgs", ""),
                      "category": s.get("category", "") or "gov-pipeline", "source_url": s.get("source_url", ""), "checked_utc": NOW,
                      "note": "spine row copied from anthropic-investors/research/05-timeline.csv per PLAN.md §4 (gov-pipeline); provenance = that file; not re-collected"})
        nxt += 1
    if added:
        with open(R / "timeline.csv", "a", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=tl_header, lineterminator="\n", extrasaction="ignore"); w.writerows(added)
    print(f"TL spine rows appended={len(added)} (existing {len(tl_existing)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
