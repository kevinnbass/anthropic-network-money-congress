#!/usr/bin/env python3
"""The pack's one test for "the giver's filing names Anthropic as employer" (2026-11-27, audit X79-5606 and lane C200).
Used by scripts/story_data.py, scripts/alt_anthropic_money.py and scripts/alt_network_money.py, which until 2026-11-27 each held their own
copy of a case-sensitive pattern: it missed the 38 gifts of lane C196 (notes written "Employer as filed=...") and would have missed the
misspelt employers of lane C200 (ANTRHOPIC, Antropic, Antrhopic, AnthropicAI) and gifts that put Anthropic in the occupation box.
The rule: the employer as filed (or, where the giver swapped the boxes, the occupation as filed) contains the word Anthropic, spelled as a
giver may misspell it, and not as part of a longer word (PHILANTHROPIC is not Anthropic; X41d moved such rows to context).
The join (scripts/build_join.py) does not use this test: its measure 1 counts every evidence gift by an individual, whatever the employer."""
import re

# X68-1501 (2026-11-27): notes also write the field as `employer=ANTHROPIC` or `employer='Anthropic'`; both are read
FIELD_EMP = re.compile(r"(?:employer as filed|contributor_employer|(?<![A-Za-z_])employer)\s*=\s*([^;]*)", re.I)
FIELD_OCC = re.compile(r"(?:occupation as filed|occupation|contributor_occupation)\s*=\s*([^;]*)", re.I)
QUOTE_EMP = re.compile(r'"contributor_employer":\s*"([^"]*)"')
ANTH = re.compile(r"(?<![A-Z])ANT(?:HR|RH|R)O?PH?IC")


def _val(m) -> str:
    """A field's value: up to the next ';' or the next ' key=' (a note may run several fields together without semicolons)."""
    if not m:
        return ""
    v = m.group(1)
    k = re.search(r"\s[A-Za-z_]+=", v)
    return (v[:k.start()] if k else v).strip().strip("'\"").strip()


def employer(note: str) -> str:
    """The employer as filed, from a row's note ('' when the note does not give it)."""
    return _val(FIELD_EMP.search(note or ""))


def names_anthropic(text: str) -> bool:
    return bool(ANTH.search((text or "").upper()))


def anthropic_employee(r: dict) -> bool:
    """True when the row's filing names Anthropic as the giver's employer (or occupation, where the boxes were swapped)."""
    note = r.get("note") or ""
    q = QUOTE_EMP.search(r.get("quote_300") or "")
    return (names_anthropic(employer(note)) or bool(re.search(r"Employer string ANTHROPIC", note, re.I))
            or bool(q and names_anthropic(q.group(1))) or names_anthropic(_val(FIELD_OCC.search(note))))
