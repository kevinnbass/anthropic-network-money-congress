# Anthropic's network and Congress: the record, 29 figures, and the code that draws them

This repository holds a record of documented connections between Anthropic's network (Anthropic, its funders and the funders of the AI-safety field, the organisations they fund that work with Congress, and their officers, PACs and lobbyists) and the members of the 119th Congress: 132,991 rows in 15 tables (14 source tables, each row with its source, and a member table built from them). It also holds the 29 figures drawn from that record and the scripts that draw them, so anyone can rebuild every figure from the tables here.

**A connection is a documented record, not an allegation of influence.** A contribution is not a vote, and an independent expenditure is not coordination. No motive is asserted anywhere.

![Which of the twelve kinds of connection reach which members](figures/congress-01-connection-grid.jpg)

## What is here

| Path | What it is |
|---|---|
| [`figures/`](figures) | The 29 figures, each as `.html` (the page itself), `.png` and `.jpg`. |
| [`FIGURES.md`](FIGURES.md) | For each figure: what it shows, and what cuts against that reading. |
| [`research/`](research) | The record: 15 tables and the helper tables the figures read. [`research/README.md`](research/README.md) explains the files, the columns and what was changed for this public copy. |
| [`case.json`](case.json) | Which rows count: each row's role (evidence, context or negative). The same roles are in `research/row_roles.csv`. |
| [`scripts/`](scripts), [`lib/`](lib) | The scripts that build the member table and draw the figures, and the small drawing library they use. |
| [`figures-alt/`](figures-alt) | Three alternate views, drawn by the same code from the same rows. See "Alternate views" below for their status. |
| [`SCRUB-LOG.csv`](SCRUB-LOG.csv) | A count of every cell changed for this public copy. |
| `network-money-per-member.*`, [`data/`](data) | The first release of 2026-09-25, kept as published. See "The first release" below. |

## The figures

Titles are as printed on each figure. [`FIGURES.md`](FIGURES.md) gives the full reading of each one and its limits.

| # | Title | Files |
|---|---|---|
| 01 | Which of the twelve kinds of connection reach which members | [jpg](figures/congress-01-connection-grid.jpg) · [png](figures/congress-01-connection-grid.png) · [html](figures/congress-01-connection-grid.html) |
| 02 | Public First family money in and out, by race | [jpg](figures/congress-02-public-first-family-by-race.jpg) · [png](figures/congress-02-public-first-family-by-race.png) · [html](figures/congress-02-public-first-family-by-race.html) |
| 03 | Principals' hard money to sitting members | [jpg](figures/congress-03-principals-hard-money-by-party-and-cycle.jpg) · [png](figures/congress-03-principals-hard-money-by-party-and-cycle.png) · [html](figures/congress-03-principals-hard-money-by-party-and-cycle.html) |
| 04 | Lobbying spend and the lobbyists' Hill origins | [jpg](figures/congress-04-lobbying-spend-and-hill-origins.jpg) · [png](figures/congress-04-lobbying-spend-and-hill-origins.png) · [html](figures/congress-04-lobbying-spend-and-hill-origins.html) |
| 05 | The revolving door, both directions | [jpg](figures/congress-05-revolving-door-both-directions.jpg) · [png](figures/congress-05-revolving-door-both-directions.png) · [html](figures/congress-05-revolving-door-both-directions.html) |
| 06 | Federal money to the network | [jpg](figures/congress-06-federal-money-to-the-network.jpg) · [png](figures/congress-06-federal-money-to-the-network.png) · [html](figures/congress-06-federal-money-to-the-network.html) |
| 07 | Election years spike with outside spending; 2025–26 shift to donations and AI-lab payments | [jpg](figures/congress-07-time-axis.jpg) · [png](figures/congress-07-time-axis.png) · [html](figures/congress-07-time-axis.html) |
| 08 | Which members the most kinds of connection touch | [jpg](figures/congress-08-member-type-heatmap.jpg) · [png](figures/congress-08-member-type-heatmap.png) · [html](figures/congress-08-member-type-heatmap.html) |
| 09 | Who spends on members, and how much of that money came from the network | [jpg](figures/congress-09-ie-committees-and-network-receipts.jpg) · [png](figures/congress-09-ie-committees-and-network-receipts.png) · [html](figures/congress-09-ie-committees-and-network-receipts.html) |
| 10 | Lobbyists' own money, by firm, cycle and recipient | [jpg](figures/congress-10-lobbyists-own-contributions.jpg) · [png](figures/congress-10-lobbyists-own-contributions.png) · [html](figures/congress-10-lobbyists-own-contributions.html) |
| 11 | The network's PACs and where they give | [jpg](figures/congress-11-corporate-pacs.jpg) · [png](figures/congress-11-corporate-pacs.png) · [html](figures/congress-11-corporate-pacs.html) |
| 12 | Where the principals' outside money went | [jpg](figures/congress-12-outside-money-flows.jpg) · [png](figures/congress-12-outside-money-flows.png) · [html](figures/congress-12-outside-money-flows.html) |
| 13 | Where network individuals' contributions land | [jpg](figures/congress-13-hard-money-by-vehicle-and-recipient.jpg) · [png](figures/congress-13-hard-money-by-vehicle-and-recipient.png) · [html](figures/congress-13-hard-money-by-vehicle-and-recipient.html) |
| 14 | Money by election cycle, one kind at a time | [jpg](figures/congress-14-dollars-by-cycle-and-type.jpg) · [png](figures/congress-14-dollars-by-cycle-and-type.png) · [html](figures/congress-14-dollars-by-cycle-and-type.html) |
| 15 | Travel and events: how the network appears | [jpg](figures/congress-15-travel-and-events.jpg) · [png](figures/congress-15-travel-and-events.png) · [html](figures/congress-15-travel-and-events.html) |
| 16 | What members say about the network, in public | [jpg](figures/congress-16-member-statements.jpg) · [png](figures/congress-16-member-statements.png) · [html](figures/congress-16-member-statements.html) |
| 17 | Members' bills, the lobbying that named them, and the fellows in their offices | [jpg](figures/congress-17-ai-bills-fellows-and-lobbying-on-members-bills.jpg) · [png](figures/congress-17-ai-bills-fellows-and-lobbying-on-members-bills.png) · [html](figures/congress-17-ai-bills-fellows-and-lobbying-on-members-bills.html) |
| 18 | What the network lobbies on | [jpg](figures/congress-18-lobbying-bills-and-issues.jpg) · [png](figures/congress-18-lobbying-bills-and-issues.png) · [html](figures/congress-18-lobbying-bills-and-issues.html) |
| 19 | Committees and offices buying from the AI labs | [jpg](figures/congress-19-ai-lab-vendors.jpg) · [png](figures/congress-19-ai-lab-vendors.png) · [html](figures/congress-19-ai-lab-vendors.html) |
| 20 | State money | [jpg](figures/congress-20-state-money.jpg) · [png](figures/congress-20-state-money.png) · [html](figures/congress-20-state-money.html) |
| 21 | The grants layer | [jpg](figures/congress-21-grants-to-intermediaries.jpg) · [png](figures/congress-21-grants-to-intermediaries.png) · [html](figures/congress-21-grants-to-intermediaries.html) |
| 22 | Who the network is, and where each appears | [jpg](figures/congress-22-network-roster.jpg) · [png](figures/congress-22-network-roster.png) · [html](figures/congress-22-network-roster.html) |
| 23 | What the record is made of | [jpg](figures/congress-23-record-composition.jpg) · [png](figures/congress-23-record-composition.png) · [html](figures/congress-23-record-composition.html) |
| 24 | The fellowship pipeline into offices | [jpg](figures/congress-24-fellowship-pipeline.jpg) · [png](figures/congress-24-fellowship-pipeline.png) · [html](figures/congress-24-fellowship-pipeline.html) |
| 25 | Outside spending for and against members | [jpg](figures/congress-25-ie-for-and-against-members.jpg) · [png](figures/congress-25-ie-for-and-against-members.png) · [html](figures/congress-25-ie-for-and-against-members.html) |
| 26 | Network witnesses before Congress: 58 appearances since 2015 | [jpg](figures/congress-26-committee-testimony.jpg) · [png](figures/congress-26-committee-testimony.png) · [html](figures/congress-26-committee-testimony.html) |
| 27 | 8 people sit across separate network organisations; funder staff sit on grantees' boards | [jpg](figures/congress-27-shared-officers.jpg) · [png](figures/congress-27-shared-officers.png) · [html](figures/congress-27-shared-officers.html) |
| 28 | The network lobbied all three state AI-safety bills, as a handful of clients among many | [jpg](figures/congress-28-state-ai-bill-lobbying.jpg) · [png](figures/congress-28-state-ai-bill-lobbying.png) · [html](figures/congress-28-state-ai-bill-lobbying.html) |
| 29 | The network reported 0.5% of 2025's AI-issue lobbying; the frontier labs 6% | [jpg](figures/congress-29-federal-ai-lobbying-baseline.jpg) · [png](figures/congress-29-federal-ai-lobbying-baseline.png) · [html](figures/congress-29-federal-ai-lobbying-baseline.html) |

Rules that bind every figure:

- One connection type per figure or per column. Types are never added together.
- Second-hop money (independent expenditures by committees the network gave to, and lobbyists' own contributions) is labelled as second hop. The network did not direct it.
- Only rows reviewed and bound as evidence are drawn on the money and connection figures. Repeated lines, restated filings and searches that found nothing are kept in the record and never counted.
- People are named only in public roles.

## Rebuild the figures

You need Python 3 and about 1 GB of disk. The figures were rendered with Chromium through Playwright.

```
git clone https://github.com/kevinnbass/anthropic-network-money-congress
cd anthropic-network-money-congress
python3 -m venv .venv && . .venv/bin/activate
pip install playwright pillow
playwright install chromium

python3 scripts/setup_data.py                       # unpacks the one table stored gzipped
python3 scripts/build_join.py                       # optional: rebuilds the member table from the 14 source tables
PYTHONHASHSEED=0 python3 scripts/build_figures.py   # figures 01-07, written into figures/
PYTHONHASHSEED=0 python3 scripts/build_figures2.py  # figures 08-25
PYTHONHASHSEED=0 python3 scripts/build_figures3.py  # figures 26-29
python3 scripts/audit.py                            # every row id a figure cites exists; every member total re-sums
```

To draw one figure, give its name: `python3 scripts/build_figures2.py congress-12-outside-money-flows`. The alternate views are `scripts/alt_network_money.py`, `scripts/alt_anthropic_money.py` and `scripts/alt_fig10.py`; they write into `figures-alt/`.

What to expect:

- **The `.html` pages come out byte for byte the same as the ones here**, except that figure 01 prints the date it was built. This was tested on a fresh copy of these files.
- **`PYTHONHASHSEED=0` matters for figure 18 only.** Its lower panel breaks one tie between two issue codes by Python's set order, which changes from run to run without the setting.
- **The `.png` and `.jpg` files depend on your browser and fonts.** The ones here were made with Playwright 1.62.0 and its Chromium on Linux, Python 3.14 and Pillow 12.3, with Arial served by Liberation Sans. With another font the pixels differ and a long label may wrap; the script stops if a page overflows.
- `build_join.py` writes `research/members_network.csv` and `research/timeline_all.csv` again. They come out the same as the ones here except for the build time they record.
- `audit.py` should end with `problems=0`. On this copy it printed `tables=15 row_ids=132991 duplicates=0 MB_rows=1073 MB_cells=15022 figures=29 pngs=29 figure_citations=48605 problems=0` (2026-11-26).

The scripts are the project's own. Five things were changed so they run here: the path to the drawing library (which now calls the Python that runs it); the paths to five input files that live in the author's other projects (copied into `research/inputs/`); one read of the saved lobbying filings in figure 29's script (replaced by the small table `research/lda_filing_expenses.csv`, made from those filings); `audit.py` no longer requires a second copy of the member table under another name; and one comment that named a person.

## How the record was checked

Rows were collected from public sources (FEC, Senate and House lobbying and disclosure filings, IRS returns, USAspending, state registries, congressional records, organisations' own pages) by AI research agents, each row with its source's URL and an excerpt as fetched; the author keeps saved copies of the sources. Rows entered the tables through a row-by-row review of each batch by a separate agent. Independent audits then checked every evidence row a figure draws against a saved original, in both directions: what was kept and what was removed. A correction never overwrites: the earlier row is archived and the change noted on the row.

The project measures itself against a written standard with a script. On 2026-11-26 it printed:

```
== congress  bound rows 131,448  evidence rows 43,500
G1 PASS  drawn evidence document-checked 31,462/31,462 (100.0%); all evidence 97.2%
G2 PASS  errors disposed 31,404/31,404; errors+qualifications disposed 59,161/59,161 (100.0%)
G3 PASS  corrected rows archived 15,372/15,372 (ledger rows 15,416)
G4 PASS  audits 83: complete 40, well-formed closing line 83; incomplete and not carried to README/dispositions 0
G5 PASS  clean figures 29/29
```

G1 says every evidence row the 29 figures draw has a document check on file; it does not cover evidence rows no figure draws (97.2% of all evidence rows are checked). G4 counts 43 of the 83 audits as closed incomplete, each with its remainder written down. The open items are stated figure by figure in [`FIGURES.md`](FIGURES.md). The saved source documents (about 160 GB) and the audit files are not in this repository; every row carries the URL of its source.

## Names

People are named only in public roles. Individual contributors, staff members and fellows who are not public figures carry a label instead of a name, such as `individual contributor ABCDEFGH, not named`; the label is the same wherever that filed name appears, and the source URL and FEC transaction id stay on the row. Street addresses and phone numbers are removed for everyone. [`research/README.md`](research/README.md) gives the rules, and `SCRUB-LOG.csv` the counts. The figures rebuild to the same pages from the labelled tables as from the named ones.

## Alternate views

`figures-alt/` holds three more charts drawn from the same evidence rows by the same code. **They have not been audited element by element, as the 29 figures have.** Read their numbers as the scripts' own.

- `network-money-per-member`: the 40 sitting members receiving the most direct money in 2024–26, by giver.
- `anthropic-money-per-member`: the same for Anthropic employees and its PAC. Its count of 63 employees counts each filed spelling of a name; folding spellings by surname and first name gives 59.
- `congress-10-lobbyists-own-contributions-alt`: figure 10's money by cycle and party.

## The first release

`network-money-per-member.png` and `.html` at the top level, with `data/contributions.csv` and `data/member_totals_by_entity.csv`, are the first release of 2026-09-25, kept as published. That figure reads $2,141,813 to 183 sitting members in 2024–26. The record has been corrected and extended since. Run on the record as it stands, the same script gives $4.1M to 214 sitting members (`figures-alt/network-money-per-member`); figure 01's entry in [`FIGURES.md`](FIGURES.md) states the current counting rule, which now includes gifts to a member's single-member joint fundraising committee and leadership PAC.

## Caveats

- A person's contribution is their own money, not their employer's. Employer strings are self-reported.
- A PAC's money comes from its members and is given by the PAC.
- Counts follow filing calendars and search depth, not activity. The 2026 cycle is open, so its figures are floors.
- A blank means none found in the sources read, not none.

## Corrections

Open an issue naming the `row_id` and the source.
