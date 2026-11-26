# Anthropic's network and Congress: the record, 29 figures, and the code that draws them

This repository holds a record of documented connections between Anthropic's network (Anthropic, its funders and the funders of the AI-safety field, the organisations they fund that work with Congress, and their officers, PACs and lobbyists) and the members of the 119th Congress: 135,014 rows in 15 tables (14 source tables, each row with its source, and a member table built from them). Members are counted as the 533 serving on November 26, 2026; two seats were vacant (`research/roster_serving.csv`). It also holds the 29 figures drawn from that record and the scripts that draw them, so anyone can rebuild every figure from the tables here.

**A connection is a documented record, not an allegation of influence.** A contribution is not a vote, and an independent expenditure is not coordination. No motive is asserted anywhere.

![450 of Congress's 533 members have a documented connection to Anthropic's network](figures/congress-01-connection-grid.jpg)

## Status: updated November 26, 2026; three audits and the final check still running

On November 26, 2026 the record was extended with the filings made through the third quarter of 2026 (activity through September 30). This release holds 2,018 more source-table rows than the one published here before it, and members are now counted as the 533 serving on November 26, 2026 instead of the Congress as first seated. Every figure was redrawn. For serving members, against the version published here before:

| Kind of connection | Before (535 first seated) | Now (533 serving) |
|---|---|---|
| Individuals' contributions | 202 members, $5.2M | 235 members, $8.7M |
| PAC contributions | 118 members, $328K | 175 members, $527K |
| Outside spending by committees with a network receipt | 201 members, $525M | 213 members, $541M |
| Lobbyists' own contributions | 293 members, $1.2M | 323 members, $1.4M |
| Lobbying reports naming a bill the member sponsored | 8 members | 38 members |
| Any counted connection | 435 of 535 | 450 of 533 |

Independent audits (X64 to X69 in the project's numbering) checked the new rows, re-derived every number on the redrawn figures from the tables, and then re-derived what was changed afterwards. Each time the numbers agreed with the tables. What the audits changed:

- **Counted twice.** 91 records were held from two filings of one transaction (a 24- or 48-hour notice and the regular report, a filing and its amendment, the giver's report and the recipient's). Each is counted once now. As they came out during the day, outside spending for serving members went from $544M, the figure this page showed at midday, to $541M.
- **Not statements.** 73 rows in the statements table by people who are not members of Congress were read against their documents and were not a statement by the named speaker (witness and signatory lists, citations, reprints, second copies). They are no longer counted. 38 more had a wrong speaker, date, venue or excerpt and are corrected.
- **Missing member.** Four counted PAC contributions did not name the member they went to. They do now, which is why PAC contributions reach 175 members.
- **Captions and lists.** Captions that left out a condition the code applies were completed, and so were lists of cited rows that left out rows a figure counts.

**Not finished. Until these are done this update is not called verified:**

- Three audits started on November 26 are still running. One traces every memo, conduit, redesignation and refund line of the contributions table that is held as evidence (3,852 lines; no dollar figure adds them, but figures 07 and 23 count them as records) to the transaction it restates. Two read against a document the other evidence rows that no auditor had read: 596 rows of the network list, most of them the committees that tie money to members; 225 timeline rows; and 181 outside-spending lines of 2008 to 2012.
- Five pairs of counted rows that share a member, a day and a dollar amount are not settled as one transaction or two ($27,399 of outside spending, $5,400 of contributions, $3,500 of lobbyists' gifts). Both rows of each pair are counted.
- A final check of everything applied follows the audits.

Corrections that come out of those checks are pushed here as they are applied. [`FIGURES.md`](FIGURES.md) gives each figure's reading and limits as they stand today.

## What is here

| Path | What it is |
|---|---|
| [`figures/`](figures) | The 29 figures, each as `.html` (the page itself), `.png` and `.jpg`. |
| [`FIGURES.md`](FIGURES.md) | For each figure: what it shows, and what cuts against that reading. |
| [`research/`](research) | The record: 15 tables and the helper tables the figures read. [`research/README.md`](research/README.md) explains the files, the columns and what was changed for this public copy. |
| [`case.json`](case.json) | Which rows count: each row's role (evidence, context or negative). The same roles are in `research/row_roles.csv`. |
| [`scripts/`](scripts), [`lib/`](lib) | The scripts that build the member table and draw the figures, and the small drawing library they use. |
| [`figures-alt/`](figures-alt) | Three alternate views, drawn by the same code from the same rows. See "Alternate views" below for their status. |
| [`SCRUB-LOG.csv`](SCRUB-LOG.csv) | A count of the cells changed for this public copy: API keys and local file paths, nothing else. |
| `network-money-per-member.*`, [`data/`](data) | The chart of direct money per member and the rows it draws. See "Direct money per member" below. |

## The figures

Titles are as printed on each figure. [`FIGURES.md`](FIGURES.md) gives the full reading of each one and its limits.

| # | Title | Files |
|---|---|---|
| 01 | 450 of Congress's 533 members have a documented connection to Anthropic's network | [jpg](figures/congress-01-connection-grid.jpg) · [png](figures/congress-01-connection-grid.png) · [html](figures/congress-01-connection-grid.html) |
| 02 | Public First family money in and out, by race | [jpg](figures/congress-02-public-first-family-by-race.jpg) · [png](figures/congress-02-public-first-family-by-race.png) · [html](figures/congress-02-public-first-family-by-race.html) |
| 03 | Principals' hard money to sitting members | [jpg](figures/congress-03-principals-hard-money-by-party-and-cycle.jpg) · [png](figures/congress-03-principals-hard-money-by-party-and-cycle.png) · [html](figures/congress-03-principals-hard-money-by-party-and-cycle.html) |
| 04 | Lobbying spend and the lobbyists' Hill origins | [jpg](figures/congress-04-lobbying-spend-and-hill-origins.jpg) · [png](figures/congress-04-lobbying-spend-and-hill-origins.png) · [html](figures/congress-04-lobbying-spend-and-hill-origins.html) |
| 05 | The revolving door, both directions | [jpg](figures/congress-05-revolving-door-both-directions.jpg) · [png](figures/congress-05-revolving-door-both-directions.png) · [html](figures/congress-05-revolving-door-both-directions.html) |
| 06 | Federal money to the network | [jpg](figures/congress-06-federal-money-to-the-network.jpg) · [png](figures/congress-06-federal-money-to-the-network.png) · [html](figures/congress-06-federal-money-to-the-network.html) |
| 07 | Election years spike with outside spending; 2025–26 shift to donations and AI-lab payments | [jpg](figures/congress-07-time-axis.jpg) · [png](figures/congress-07-time-axis.png) · [html](figures/congress-07-time-axis.html) |
| 08 | Which members the most kinds of connection touch | [jpg](figures/congress-08-member-type-heatmap.jpg) · [png](figures/congress-08-member-type-heatmap.png) · [html](figures/congress-08-member-type-heatmap.html) |
| 09 | Who spends on members, and what the record shows those committees received | [jpg](figures/congress-09-ie-committees-and-network-receipts.jpg) · [png](figures/congress-09-ie-committees-and-network-receipts.png) · [html](figures/congress-09-ie-committees-and-network-receipts.html) |
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
- The figures name people only in public roles.

## Rebuild the figures

You need Python 3, and disk space for the checkout, the unpacked table, a Python environment and Chromium. The figures were rendered with Chromium through Playwright.

```
git clone https://github.com/kevinnbass/anthropic-network-money-congress
cd anthropic-network-money-congress
python3 -m venv .venv && . .venv/bin/activate
pip install playwright pillow
playwright install chromium

python3 scripts/setup_data.py                       # unpacks the one table stored gzipped
python3 scripts/build_join.py                       # optional: rebuilds the member table from the 14 source tables
python3 scripts/build_figures.py                    # figures 01-07, written into figures/
python3 scripts/build_figures2.py                   # figures 08-25
python3 scripts/build_figures3.py                   # figures 26-29
python3 scripts/audit.py                            # every row id a figure cites exists; every member total re-sums
```

To draw one figure, give its name: `python3 scripts/build_figures2.py congress-12-outside-money-flows`. The alternate views are `scripts/alt_network_money.py`, `scripts/alt_anthropic_money.py` and `scripts/alt_fig10.py`; they write into `figures-alt/`.

What to expect:

- **The `.html` pages come out byte for byte the same as the ones here**, except that figure 01 prints the date it was built. This was tested on a fresh copy of these files.
- **The `.png` and `.jpg` files depend on your browser and fonts.** The ones here were rendered with Playwright and its Chromium on Linux. With another browser or font the pixels differ and a long label may wrap; the script stops if a page overflows.
- `build_join.py` writes `research/members_network.csv` and `research/timeline_all.csv` again. They come out the same as the ones here except for the build time they record.
- `audit.py` should end with `problems=0`. On a fresh copy of these files it printed `tables=15 row_ids=135014 duplicates=0 MB_rows=1078 MB_cells=15092 figures=29 pngs=29 figure_citations=230952 problems=0` (2026-11-26, after the third-quarter update and its audits), and the three figure scripts wrote all 29 `.html` pages byte for byte as they are here.

The scripts are the project's own. Four things were changed so they run here: the path to the drawing library (which now calls the Python that runs it); the paths to five input files that live in the author's other projects (copied into `research/inputs/`); one read of the saved lobbying filings in figure 29's script (replaced by the small table `research/lda_filing_expenses.csv`, made from those filings); and `audit.py` no longer requires a second copy of the member table under another name.

## How the record was checked

Rows were collected from public sources (FEC, Senate and House lobbying and disclosure filings, IRS returns, USAspending, state registries, congressional records, organisations' own pages) by AI research agents, each row with its source's URL and an excerpt as fetched; the author keeps saved copies of the sources. Rows entered the tables through a row-by-row review of each batch by a separate agent. Independent audits then checked evidence rows against saved originals, in both directions: what was kept and what was removed. The measure below says how many. A correction never overwrites: the earlier row is archived and the change noted on the row.

The project measures itself against a written standard with a script. On 2026-11-26 at 14:07 UTC it printed:

```
== congress  bound rows 133,466  evidence rows 44,285
G1 FAIL  drawn evidence document-checked 43,106/44,285 (97.3%); all evidence 97.3%
G2 FAIL  errors disposed 32,293/32,467; errors+qualifications disposed 60,211/60,535 (99.5%)
G3 PASS  corrected rows archived 15,780/15,780 (ledger rows 15,826)
G4 FAIL  audits 100: complete 48, well-formed closing line 98; incomplete and not carried to README/dispositions 0; malformed ['X70-memo-and-conduit-lines-20261126', 'X71b-unread-timeline-and-money-rows-20261126']
G5 PASS  clean figures 29/29
```

G1 says how many of the evidence rows the 29 figures draw or count have a document check on file. Since figure 23 lists every row it counts, that is every evidence row in the record, so the two percentages on its line are now the same. Before the three running audits started, it read 43,237 of 44,285: 1,048 evidence rows that no auditor had compared with a document, the rows named under Status. Three audits were running when the lines above were printed, and the script reads their unfinished folders: every finding G2 counts as not yet settled is theirs (324), the two reports G4 calls malformed are theirs and not yet written, and a row they have so far marked wrong counts as unchecked in G1 until the finding is settled. G4 counts 50 of the 100 audits as closed incomplete, each with its remainder written down; the two it calls malformed are two of the running ones. The open items are stated figure by figure in [`FIGURES.md`](FIGURES.md). Earlier on 2026-11-26, before the update, figure 01 was redrawn as a chamber and figure 18's issue panel was changed to draw every code on three or more reports; an auditor that made neither change re-derived both from the tables and corrected two sentences in figure 01's footnote. The saved source documents and the audit files are not in this repository; rows carry the URL of their source where one was recorded.

## Names

The figures name people only in public roles. The tables carry the record as its public sources print it: contributors, lobbyists, staff, officers and witnesses appear as the FEC, lobbying, payroll, tax and congressional records name them, and each row carries the URL of its source. Two things were taken out of this copy: API keys in saved request URLs, and file paths on the author's machine. `SCRUB-LOG.csv` counts them.

## Alternate views

`figures-alt/` holds three more charts drawn from the same evidence rows by the same code. They are not among the 29 figures. An independent auditor re-derived all three from the tables on 2026-11-26, before the third-quarter update, and its corrections are in the code. They were redrawn on the updated record the same day, and a second independent audit (X69) re-derived the redrawn charts from the tables. It reproduced them and found four PAC contributions that did not name their member; with those added the network chart reads $7.8M to 265 sitting members in 2024–26, the Anthropic chart $5.8M to 195 sitting members from 88 filed employee names and the PAC, and the lobbyist chart $1.4M, with $879K in 2026 so far.

- `network-money-per-member`: the 40 sitting members receiving the most direct money in 2024–26, by giver.
- `anthropic-money-per-member`: the same for Anthropic employees and its PAC. It counts one employee per filed surname and first name.
- `congress-10-lobbyists-own-contributions-alt`: figure 10's money by firm, cycle and party. It draws only gifts dated while the lobbyist's firm was registered for a network client.

## Direct money per member

`network-money-per-member.png` and `.html` at the top level show the 40 sitting members receiving the most direct money from the network in 2024–26, by giver: $7.8M to 265 sitting members on the record as it stands after the third-quarter update of 2026-11-26. `data/contributions.csv` has one line per contribution the chart draws and `data/member_totals_by_entity.csv` its bar segments; `python3 scripts/alt_network_money.py --data data` writes all of them again. The same chart is in `figures-alt/`.

This chart was the repository's first release, on 2026-09-25. It read $2.2M to 185 sitting members when first published and $2.1M ($2,141,813) to 183 after a revision the same day. The record has been corrected and extended since; figure 01's entry in [`FIGURES.md`](FIGURES.md) states the current counting rule, which includes gifts to a member's single-member joint fundraising committee and leadership PAC. The first release is in this repository's history.

## Caveats

- A person's contribution is their own money, not their employer's. Employer strings are self-reported.
- A PAC's money comes from its members and is given by the PAC.
- Counts follow filing calendars and search depth, not activity. The 2026 cycle is open: its totals reflect the reports counted so far and can change with later filings and amendments.
- A blank means none found in the sources read, not none.

## Corrections

Open an issue naming the `row_id` and the source.
