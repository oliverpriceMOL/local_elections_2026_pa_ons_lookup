---
description: "Brainstorm visualisation designs for Phase 2: Welsh Senedd and Scottish Holyrood election graphics"
agent: "agent"
---

# Phase 2 Brainstorm: Welsh Senedd & Scottish Holyrood Elections

## Your task

Brainstorm interactive visualisation ideas for the Welsh Senedd and Scottish Holyrood election pages, following the same Daily Mail presentation style as the Phase 1 England local elections. Propose concrete component designs, layouts, and interaction patterns.

## Context: what we've already built (Phase 1 — England)

Phase 1 covers 136 English local council elections + 6 mayoral elections. The front-end lives in `mock_up_designs/` and uses D3.js v7 (CDN), vanilla JS (no frameworks), DM Sans font, and CSS custom properties. See [copilot-instructions.md](.github/copilot-instructions.md) for full architecture details.

**Existing components we can reuse or adapt:**
- **Hemicycle** — semi-circular parliament seat chart with hover + majority line
- **Gain/hold badge** — pill badge with party colours (responsive full/short text)
- **Change bar chart** — horizontal ±diverging bars per party
- **Council card** — full result card (hemicycle + change bars + badge)
- **Mayoral card** — winner highlight, candidate vote bars, stats row
- **Interactive choropleth map** — D3 SVG with search, postcode lookup, filter tabs, zoom, tabbed overlay
- **Party strip** — horizontal party totals with councillors/councils toggle
- **Scoreboard** — national summary table with change arrows
- **Progress counter** — rectangular fill bar with "X/Y declared" text

**Styling conventions:** `--dm-blue: #004DB3`, `--dm-dark: #1a1a2e`, no uppercase, green ▲ gains / red ▼ losses / grey — no change, responsive at 640px and 480px breakpoints.

## Scottish Parliament (Holyrood) — election system

**73 constituency seats** (FPTP — one winner per constituency):
```
Data shape: { name, number, electorate, turnout, percentageTurnout,
  winningParty, gainOrHold, sittingParty, majority, swing, swingTo, swingFrom,
  candidates: [{firstName, surname, elected, party: {abbreviation, votes, percentageShare}}] }
```

**56 regional seats** (party list / top-up — 7 seats per region, 8 regions):
```
Data shape: { name, number, electorate, turnout, percentageTurnout,
  winningParty, majority,
  candidates: [{firstName, surname, elected, partyListRank, party: {abbreviation}}],
  parties: [{abbreviation, name, votes, percentageShare}] }
```
- Multiple candidates elected per region (up to 7)
- Each party submits a ranked list; `partyListRank` indicates position
- `parties` array has vote totals per party at region level

**Total: 129 MSPs** (73 constituency + 56 regional)

**Key parties:** SNP, Lab, C, LD, Green, Reform, Alba, Ind

## Welsh Parliament (Senedd) — election system

**NEW SYSTEM FOR 2026**: Wales has changed from 60 to **96 Senedd Members** using a **closed-list proportional system** across 16 constituencies (6 members each). No FPTP component — it's entirely list-based.

```
Data shape: { name, number, electorate, turnout, percentageTurnout,
  winningParty, majority,
  candidates: [{firstName, surname, elected, partyListRank, party: {abbreviation}}],
  parties: [{abbreviation, name, votes, percentageShare}] }
```
- 16 constituencies, 6 seats each = 96 total
- Multiple elected candidates per constituency
- Parties ranked by vote share; seats allocated proportionally

**Key parties:** Lab, C, PC (Plaid Cymru), LD, Green, Reform, Gwlad, Propel, Abolish

## What to brainstorm

### 1. Maps
- Scotland and Wales each need their own D3 choropleth maps
- Scotland has TWO layers: 73 constituencies (FPTP) + 8 regions (top-up). How to show both?
- Wales has 16 larger constituencies (list PR). Different from England's hundreds of tiny LADs.
- How should filter tabs work? Scotland: Constituency / Region? What interactions on click?

### 2. Constituency/Region result cards
- FPTP constituency cards (Scotland): similar to mayoral cards? Candidate bars + winner highlight?
- Regional/list cards: multiple winners from different parties. How to visualise 6-7 elected members from a region?
- Should we show the party list rankings? The vote shares per party?

### 3. Overall parliament composition
- The hemicycle component already exists — perfect for showing the full 129-seat (Scotland) or 96-seat (Wales) parliament
- How to show how the parliament is built up from constituencies + regions (Scotland)?
- A "live filling" hemicycle as results come in?

### 4. Scoreboard / national summary
- Scotland: separate totals for constituency seats vs regional seats, plus combined?
- Wales: 16 constituencies, all list-based — one summary table?
- How to show swing data (Scotland FPTP has swing fields)?

### 5. Party strip adaptation
- Different party sets for Scotland (SNP, Alba) and Wales (PC, Gwlad, Propel)
- Toggle between constituency/regional/total views?

### 6. Page layout
- Separate pages for Scotland and Wales, or tabs on one page?
- How does the map + results + scoreboard + hemicycle all fit together?
- Mobile layout considerations?

### 7. New component ideas
- Anything we don't have yet that these election systems need?
- Sankey diagram showing how list votes → seats?
- Regional breakdown showing how top-up seats correct proportionality?
- Comparison with 2021 results?

## Output format

For each idea, provide:
1. **Component name** — what to call it
2. **Sketch** — describe the visual layout (dimensions, colours, elements)
3. **Data requirements** — which fields from the data shapes above it needs
4. **Interaction** — hover, click, toggle behaviours
5. **Reuse** — which existing Phase 1 components it builds on (if any)
6. **Complexity** — low / medium / high effort estimate
