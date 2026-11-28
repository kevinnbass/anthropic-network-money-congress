#!/usr/bin/env python3
"""Test whether the giver's filing names Anthropic as employer (PLAN K14, X93-32).

The shared selector is used by the two money alternates and story_data. It reads
filed fields transcribed in the note or excerpted from the filing. An exact
company name in occupation can resolve a missing/placeholder employer or a
clear swap with a job title. The join's measure 1 has its own roster-based scope.
"""
import re

EMP_KEY = r"(?:employer as filed|employer_as_filed|contributor_employer|employer)"
OCC_KEY = r"(?:occupation as filed|occupation_as_filed|contributor_occupation|occupation)"
# The notes also use a short chain of key=value fields to transcribe filed
# identity, without semicolons between the contributor, employer and job.
FIELD_VALUE = r'''(?:'[^'\n]*'|"[^"\n]*"|(?:(?!\b(?:former|previous|prior|past)\b)[^=;\n])+?)'''
FIELD_START = (
    rf"(?:\A|[;\n]|(?<=\.)[ \t]+|\b(?:Identity(?: fields from held HM line| beyond name match)?"
    rf"|Contributor identity beyond name match|Exact filed transaction):?[ \t]+"
    rf"|\b(?:payer|contributor(?:_name)?)={FIELD_VALUE}[ \t]+"
    rf"|\bIdentity:[ \t]*city={FIELD_VALUE}[ \t]+)"
)
NEXT_KEY = re.compile(rf"\s+(?=(?:{EMP_KEY}|{OCC_KEY}|[A-Za-z_]\w*)\s*=)", re.I)
FIELD_EMP = re.compile(rf"{FIELD_START}[ \t]*{EMP_KEY}[ \t]*=[ \t]*([^;\n]*)", re.I)
FIELD_OCC = re.compile(
    rf"{FIELD_START}(?:[ \t]*{EMP_KEY}[ \t]*=[ \t]*{FIELD_VALUE}[ \t]+)?"
    rf"[ \t]*{OCC_KEY}[ \t]*=[ \t]*([^;\n]*)", re.I,
)
FORMER = re.compile(rf"\b(?:former|previous|prior|past)\s+(?:{EMP_KEY}|{OCC_KEY})\s*=", re.I)
QUOTE_EMP = re.compile(r'(?:\A|[,{])\s*"contributor_employer"\s*:\s*(?:"([^"]*)"|null\b)', re.I)
QUOTE_OCC = re.compile(r'(?:\A|[,{])\s*"contributor_occupation"\s*:\s*(?:"([^"]*)"|null\b)', re.I)
ALIASES = {
    "ANTHROPIC", "ANTHROPIC PBC", "ANTHROPIC AI", "ANTHROPICAI",
    "ANTHROPIC INC", "ANTHROPIC LLC", "ANTHROPIC MACHINE LEARNING",
    "ANTHROPIC FELLOWS PROGRAM", "ANTHROPIC RESEARCH SERVICES",
    "ANTRHOPIC", "ANTROPIC", "ANTROPIC PBC",
}
PLACEHOLDERS = {
    "", "N/A", "NA", "N.A", "NONE", "NULL", "UNKNOWN", "SELF", "SELF EMPLOYED",
    "SELF-EMPLOYED", "INFORMATION REQUESTED", "INFORMATION REQUESTED PER BEST EFFORTS",
    "INFORMATION NOT PROVIDED", "NOT EMPLOYED", "UNEMPLOYED", "RETIRED",
    "NOT AVAILABLE", "NOT APPLICABLE", "NOT PROVIDED", "NOT DISCLOSED", "-",
}
JOB_TITLE = re.compile(
    r"(?:(?:AI|AI SAFETY|MACHINE LEARNING|SOFTWARE|RESEARCH|TECHNICAL|PRODUCT|SENIOR|STAFF) )*"
    r"(?:ENGINEER|RESEARCHER|SCIENTIST|PROGRAMMER|MANAGER)"
    r"|MEMBER OF (?:THE )?(?:TECHNICAL|OPERATIONS|RESEARCH) STAFF"
)


def _normalize(value):
    value = (value or "").upper().strip().strip(".,")
    return " ".join(value.replace(",", " ").split())


def _value(match):
    """Read to the next semicolon or key=value field."""
    if not match:
        return ""
    value = match.group(1).strip()
    if value.startswith(("'", '"')) and value[0] in value[1:]:
        end = value.find(value[0], 1)
        if end + 1 == len(value) or value[end + 1] in ", 	":
            return value[1:end].strip()
    return NEXT_KEY.split(value, maxsplit=1)[0].strip()


def _note_fields(note, pattern):
    return tuple(dict.fromkeys(_value(match) for match in pattern.finditer(note)))


def employer(note: str) -> str:
    """The employer as filed, from the first applicable field in the note."""
    return next((value for value in _note_fields(note or "", FIELD_EMP) if value), "")


def names_anthropic(text: str) -> bool:
    return _normalize(text) in ALIASES


def filed_fields(row):
    note, quote = row.get("note") or "", row.get("quote_300") or ""
    employers = _note_fields(note, FIELD_EMP) if "employer" in note.lower() else ()
    occupations = _note_fields(note, FIELD_OCC) if "occupation" in note.lower() else ()
    quoted_emp = QUOTE_EMP.search(quote) if "contributor_employer" in quote.lower() else None
    quoted_occ = QUOTE_OCC.search(quote) if "contributor_occupation" in quote.lower() else None
    if quoted_emp:
        employers = (*employers, quoted_emp.group(1) or "")
    if quoted_occ:
        occupations = (*occupations, quoted_occ.group(1) or "")
    return tuple(dict.fromkeys(employers)), tuple(dict.fromkeys(occupations))


def assess(row):
    """Return the attribution verdict, the filed values considered and the reason."""
    employers, occupations = filed_fields(row)
    named = {_normalize(value) for value in employers} - PLACEHOLDERS
    occupation_names = {_normalize(value) for value in occupations} - PLACEHOLDERS
    if named and named <= ALIASES:
        return True, employers, occupations, "approved filed employer"
    if occupation_names and occupation_names <= ALIASES:
        if not named and not FORMER.search(row.get("note") or ""):
            return True, employers, occupations, "company alone in occupation with blank or placeholder employer"
        if named and len(named) == 1 and all(JOB_TITLE.fullmatch(value) for value in named):
            return True, employers, occupations, "job title in employer and company alone in occupation"
    reason = "different or unapproved filed employer" if named else "no current approved employer shown"
    return False, employers, occupations, reason


def anthropic_employee(r: dict) -> bool:
    return assess(r)[0]
