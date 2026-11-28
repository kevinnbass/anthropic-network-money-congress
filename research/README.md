# The record

Fifteen tables hold the record; each row has a `row_id` whose letters name its table. The other files here are small helper tables the figures read. Rows are never deleted: a row that repeats another, restates a filing, or turned out to be someone else is kept and marked as context.

| File | Ids | Rows | What a row is |
|---|---|---|---|
| `entities.csv` | EN | 3,407 | the roster: people, organisations, committees and vehicles, with tier and identifiers |
| `hard_money.csv` | HM | 20,945 | itemised contributions (connection types 1 and 2), with the memo, conduit and repeated lines held as context |
| `super_pac_c4.csv.gz` | SP | 56,161 | money into super PACs and political nonprofits (3a) and their independent expenditures (3b) |
| `lobbying.csv` | LB | 2,879 | federal lobbying registrations and reports (4a) |
| `lobbyist_contributions.csv` | LC | 18,323 | lobbyists' own contributions as reported on LD-203 (4b) |
| `revolving_door.csv` | RD | 1,305 | roles on the Hill and at network organisations, one row per role (5) |
| `grants.csv` | GR | 3,081 | grants by network funders (6) |
| `federal_money.csv` | FG | 2,018 | federal awards and provisions (7) |
| `member_disclosures.csv` | PD | 1,057 | members' financial-disclosure lines (8) |
| `travel.csv` | TV | 2,022 | privately sponsored travel, events and committee testimony (9) |
| `vendors.csv` | VN | 9,838 | payments by committees and House offices to AI labs (10) |
| `member_statements.csv` | MS | 9,439 | statements and record mentions naming the network (11) |
| `state_government.csv` | SG | 3,100 | state-level contributions and lobbying (12) |
| `timeline.csv` | TL | 1,066 | dated events |
| `members_network.csv` | MB | 1,078 | the join: one row per member, and per connection type a count, a sum and the row ids behind them; written by scripts/build_join.py |
| `timeline_all.csv` |  | 109,700 | every dated row of every table on one line each; written by scripts/build_join.py |
| `lb_4b_measures.csv` |  | 13,128 | for each LD-203 item, which of figure 10's two counts it falls in |
| `lb_network_windows.csv` |  | 38 | the dates each lobbying firm was registered for a network client |
| `lda_baseline.csv` |  | 9,651 | federal lobbying reports naming an AI issue, for figure 29 |
| `lda_baseline_additions.csv` |  | 1,989 | more such reports, for figure 29 |
| `lda_filing_expenses.csv` |  | 11,640 | for each of those reports, whether the filing reports expenses (an in-house filer) or income (a firm); made for this copy from the saved filings |
| `lda_branch_censored.csv` |  | 432 | reports under the $5,000 threshold, with the box the filer ticked |
| `lda_precedence_pairs.csv` |  | 278 | outside-firm reports paired with the client's own in-house report |
| `grant_causes.csv` |  | 2,050 | the cause class of each grant row, for figure 21 |
| `interlocks.csv` |  | 235 | officers, directors and key employees on tax returns, for figure 27 |
| `network_line_starts.csv` |  | 37 | the date the network first funded each line of work at an organisation |
| `state_ai_bill_clients.csv` |  | 196 | the clients that reported lobbying on three state AI bills, for figure 28 |
| `travel_copies.csv` |  | 73 | travel rows that repeat a trip another row carries |
| `supersede_reviewed.csv` |  | 16 | pairs of rows settled as two distinct facts |

Also here: `bill_sponsor_keys.csv`, `grant_payment_unproven.csv`, `lb_4b_measures.before-gs-promote-20261127.csv`, `lb_4b_measures.before-gs-promote3-20261127.csv`, `lb_bill_scope.csv`, `lda_baseline_provisional_additions.csv`, `roster_serving.csv`, `testimony_from_statements.csv`, `aspen_classes.json` (the class of each Aspen conference row, for figure 15), `grok-out/C161-network-interlocks.csv` (the collected officer rows figure 27 also reads), `inputs/` (the files `scripts/build_join.py` reads from the author's sibling projects: the member roster, AI bills and cosponsors with their bill-status files, fellowship offices, hearing citations and a timeline) and `primary/` (the public congress-legislators files it reads).

## Which rows count

`../case.json` binds each row to a question with a role, and `row_roles.csv` lists the same roles one row per line: **evidence** (43,205 rows; the only rows the money and connection figures draw or count), **context** (85,789; kept, never counted) and **negative** (5,181; a search of the named source that found nothing, as of its date). A row in no binding is unbound and is not counted.

## Columns

Most tables share `task` (the collection batch), `date`, `source_type`, `url` (the source), `quote_300` (an excerpt of the source as fetched), `checked_utc` (when it was read), `entity_id` (the roster row it is tied to) and `note`. The money tables add `money_type`, `hop` (2 means second-hop money, which the network did not direct), `payer`, `payee`, their types and ids, `member_bioguide`, `amount_usd` and `cycle`. Amounts are as filed. Connection types are never added together.

The `note` column records how a row was collected, reviewed and corrected, in the project's own shorthand (batch names, audit ids, names of working files). Those working files are not in this repository; the names are kept so the history of a row stays readable. A corrected row keeps a note of what it said before.

## What was changed for this public copy

`../SCRUB-LOG.csv` counts every changed cell by table, column and kind of change. Nothing else differs from the working record.

- **Keys.** The value of an `api_key` in a saved request URL is removed.
- **Local file paths.** A path on the author's machine is replaced by the file's name; a path inside the project folder is left as a relative path.

Everything else is as the sources print it: names, employers, addresses and amounts are those of the public filings and pages each row cites.
