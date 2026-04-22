# Project Guidelines

## Project Context

UK May 2026 election graphics for the Daily Mail. Presentation-quality interactive visualisations for election night coverage. Phase 1 covers England local council elections (136 councils) and 6 mayoral elections. Phase 2 covers Scottish Parliament (Holyrood) and Welsh Parliament (Senedd) elections.

The front-end in `mock_up_designs/` is the primary deliverable. Data arrives as raw PA (Press Association) wire JSON files (xmltodict-converted XML) from a CDN, gets normalized at runtime by `data-adapter.js`, and is rendered by D3.js components.

## Tech Stack

- **Rendering**: D3.js v7 (loaded via CDN — no npm/bundler)
- **Language**: Vanilla JavaScript — no frameworks, no modules, no imports. All functions live in global scope.
- **Font**: Inter (Google Fonts), weights 400/500/700
- **Styling**: Plain CSS with custom properties. No preprocessor.
- **Data processing**: Python 3 scripts in `scripts/`
- **Server**: `python3 -m http.server 8080` from `mock_up_designs/`
- **Git**: `https://github.com/oliverpriceMOL/local_elections_2026.git`, branch `main`
- **Standalone repo**: `https://github.com/oliverpriceMOL/election_graphics_mockups_2026.git` (GitHub Pages at `https://oliverpricemol.github.io/election_graphics_mockups_2026/`). Mirror of `mock_up_designs/` — copy changed files there after committing to main repo.

## Two-Repo Structure

The project uses two Git repositories:

1. **Main repo** (`local_elections_2026`) — full project including PA XML data, Python scripts, GeoJSON, and the `mock_up_designs/` front-end. Lives on OneDrive at `~/Library/CloudStorage/OneDrive-SharedLibraries-DMGTCloud/MOL - Data Journalism - Documents/Elections/local_elections_2026/`.

2. **Standalone repo** (`election_graphics_mockups_2026`) — a mirror of `mock_up_designs/` only. Lives at `~/election_graphics_mockups_2026/`. Deployed via GitHub Pages for sharing previews.

### Deployment workflow

```bash
# 1. Make changes in main repo under mock_up_designs/
# 2. Commit and push main repo
cd /path/to/local_elections_2026
git add -A && git commit -m "description" && git push

# 3. Copy changed files to standalone repo
STANDALONE=~/election_graphics_mockups_2026
cp mock_up_designs/js/changed-file.js "$STANDALONE/js/changed-file.js"
# ... repeat for each changed file

# 4. Commit and push standalone repo
cd "$STANDALONE"
git add -A && git commit -m "description" && git push
```

GitHub Pages auto-deploys. The standalone repo contains no Python scripts, XML data, or GeoJSON source files — just the front-end HTML/CSS/JS and pre-built JSON data in `data/`.

## Architecture

Every component is a standalone function: `functionName(container, data, options)`. The container is a DOM element. D3 handles all DOM manipulation and SVG rendering. Components compose by calling each other (e.g. council-card calls hemicycle, change-bar, and badge).

### Component Inventory

| File | Function | Purpose |
|------|----------|---------|
| `party-config.js` | `partyColour(abbr)`, `partyName(abbr)` | Party colours and names. 16 parties: Lab, C, LD, Green, Reform, R, Ind, Your, SNP, Alba, PC, Gwlad, Propel, Abolish, NOC, Other. Notable: NOC `#DEA5B2` (dusty pink), Ratepayers `#2D6A4F` (dark green) |
| `tooltip.js` | `Tooltip.show()`, `Tooltip.hide()`, `Tooltip.position()` | Viewport-aware tooltip singleton. Creates/reuses tooltip elements by ID with smart bounds constraint |
| `data-adapter.js` | `paUrl()`, `normalizeLocalResults()`, `normalizeFPTPResults()`, `normalizeTopUpResults()`, `normalizeLocalNominations()`, `normalizeFPTPNominations()`, `normalizeTopUpNominations()` | Transforms raw PA wire JSON (xmltodict format with `@`-prefixed keys) into the flat shapes D3 components expect. Also provides `paUrl(category, filename)` which routes through CDN in production and local `data/` on localhost |
| `utils.js` | `dedupByRevision()`, `textColourForBg()`, `formatChange()`, `formatPercentageChange()`, `enrichWithNotionals()`, `maxPartySlots()`, `onResize()`, `turnoutBar()`, `nextCleanScale()`, tooltip helpers, etc. | Shared utility functions used across all pages. `turnoutBar(container, {turnout, totalVotes, electorate})` renders black-fill-on-grey progress bar |
| `hemicycle.js` | `hemicycle(container, parties, options)` | Semi-circular parliament seat chart with hover interaction and majority line |
| `badge.js` | `gainHoldBadge(container, result, options)` | Gain/hold/lose pill badge with party colours. Renders both `.badge-full` and `.badge-short` spans for responsive toggle |
| `progress.js` | `progressCounter(container, {declared, total, label})` | Rectangular progress bar with text inside |
| `council-card.js` | `councilResultCard(container, council, options)` | Full or mini council result card (hemicycle + change bars + badge) |
| `change-bar.js` | `changeBarChart(container, changes, options)` | Horizontal diverging bar chart (positive right, negative left) |
| `pa-ons-lookup.js` | `PA_ONS_LOOKUP` global object | Generated PA ID → ONS code mapping. 5 sub-maps: `localCouncils` (paId→LAD25CD), `mayoralAreas` (paId→LAD25CD), `scottishConstituencies` (number→SPC_CD), `scottishRegions` (number→SPR_CD), `welshConstituencies` (number→SENEDD_CD). Regenerate with `python3 scripts/build_pa_ons_lookup.py` |
| `council-lookup.js` | `normaliseName(name)`, `buildCouncilLookup(ladNames, countyNames)` | Fuzzy name matching (legacy fallback). Maps still load this for fallback if `PA_ONS_LOOKUP` misses |
| `election-map.js` | `createMapScaffold()`, tooltip/search/overlay helpers | Shared map scaffold and interaction helpers used by all three map components. SVG `<defs>` includes crosshatch pattern (`id="crosshatch"`) for awaiting areas |
| `england-map.js` | `englandMap(container, results, ladGeo, countyGeo, mayoralResults, options)` | Interactive D3 choropleth map with search, postcode lookup, filter tabs, zoom, tabbed overlay, and awaiting-declaration overlays for nominated-but-no-result areas |
| `party-strip.js` | `partyStrip(container, options)` → wrapped by `partyTotalsStrip()` | Generic horizontal party totals bar with toggle. Core uses `options.toggleLabels` + `options.getData(modeIndex)` callback |
| `scoreboard.js` | `electionScoreboard(container, options)` → wrapped by `partyScoreboard()` | Generic scoreboard table with configurable columns. Core uses `options.columns`, `options.partyRows`, `options.nocRow`. Optional `options.turnout` renders aggregate turnout bar below table |
| `fptp-card.js` | `fptpResultCard(container, result, options)` → aliases `mayoralResultCard()`, `constituencyResultCard()` | Unified FPTP card for mayoral (England) and constituency (Scotland) results. Winner highlight, candidate bars with inside/outside labels, turnout bar, declaration time (always last element) |
| `change-columns.js` | `changeColumnsChart(container, options)` | Shared core for vertical diverging bar charts. Supports single-bar and split (constituency/regional) modes |
| `party-change-columns.js` | `partyChangeColumns(container, results, options)` | England wrapper: aggregates local results → calls `changeColumnsChart`. NOC bar appended in councils view (protected from cull) |
| `list-card.js` | `listResultCard(container, result, options)` | Proportional/regional result card: stacked vote bar, elected member pills, no majority stat |
| `scottish-scoreboard.js` | `scottishScoreboard(container, constResults, regResults)` | Aggregates FPTP/list data → calls `electionScoreboard` with 3 column groups (constituency/regional/total) + aggregate turnout |
| `welsh-scoreboard.js` | `welshScoreboard(container, results)` | Aggregates seats/votes → calls `electionScoreboard` with vote share bars + aggregate turnout |
| `devolved-strip.js` | `devolvedPartyStrip(container, constResults, regResults, options)` | Aggregates Scotland/Wales data → calls `partyStrip` core |
| `devolved-change-columns.js` | `devolvedChangeColumns(container, constResults, regResults, options)` | Aggregates Scotland/Wales data → calls `changeColumnsChart` core |
| `scotland-map.js` | `scotlandMap(container, constResults, regResults, constGeo, regGeo, options)` | Interactive D3 choropleth for Scotland: constituency/region views, search, postcode lookup, zoom, tabbed overlay |
| `wales-map.js` | `walesMap(container, results, constGeo, options)` | Interactive D3 choropleth for Wales: 16 Senedd constituencies, search, postcode lookup, zoom, overlay |

### Data Pipeline

The front-end consumes **raw PA wire JSON** — xmltodict-converted XML with `@`-prefixed attribute keys, string values, and deeply nested wrappers. These files are served from a CDN in production and from local `data/` during development.

```
Production CDN:
  https://scripts.dailymail.co.uk/static/uk_elections/2026/local_elections/{category}/{env}/{file}
  (category = results|nominations, env = test|live)

Local development:
  mock_up_designs/data/*.json  (downloaded copies of CDN files)

paUrl(category, filename) resolves to CDN or local data/ based on hostname.

Front-end pages fetch via Promise.all:
    index.html    → local_results, mayoral_results, local_nominations, mayoral_nominations, lad_map.geojson, counties_map.geojson
    scotland.html → scottish_fptp_results, scottish_topup_results, scottish_fptp_nominations, scottish_topup_nominations, 2 GeoJSONs, scottish_notionals
    wales.html    → welsh_results, welsh_nominations, senedd_constituencies.geojson
        → data-adapter.js normalizers → dedupByRevision() → enrichWithNotionals() (Scotland only) → D3 components render
```

Separately, Python scripts in `scripts/` can convert source PA XML files for testing:
```
PA XML files (nominations/, results/)
    → scripts/convert_xml_to_json.py → output/*.json (pre-processed format, not used by front-end)

Hanretty notional CSVs (data/notionals/consty_notionals.csv, list_notionals.csv)
    → scripts/build_scottish_notionals.py → output/scottish_notionals.json

PA nomination JSONs + GeoJSON + notionals CSVs
    → scripts/build_pa_ons_lookup.py → mock_up_designs/js/pa-ons-lookup.js + output/pa_ons_lookup.json
```

### Raw PA Wire Format vs Normalized Format

The raw PA wire JSON uses xmltodict conventions:
- `@`-prefixed attribute keys: `"@name"`, `"@revision"`, `"@votes"`
- All values are strings: `"@revision": "2"`, `"@votes": "12644"`
- Change values have `+` prefix: `"@change": "+7"`
- Deeply nested: wrapper key → `Election` → `Council`/`Constituency` → data
- Single children not wrapped in arrays (xmltodict quirk)
- Multiple message types per file: `LocalElectionResult` + `LocalStateOfParties`, `FirstPastThePostResult` + `FirstPastThePostRush` + `FirstPastThePostStateOfParties`, `TopUpResult` + `TopUpRush`

`data-adapter.js` normalizes these into the flat shapes components expect:
- Strips `@` prefixes, converts strings to numbers
- Unwraps nested Election/Council/Constituency structure
- Normalizes single-item children into arrays
- Filters out SOP (State of Parties) entries
- Tags each item with `fileType: "result"` or `"rush"`

### Key Data Shapes

**Local result:**
```
{ name, type, revision, winningParty, sittingParty, gainOrHold,
  newCouncil: [{name, seats}], changes: [{name, change}],
  election: {date, paId} }
```

**Mayoral / FPTP result (also Scottish constituencies):**
```
{ name, fileType, revision, winningParty, gainOrHold, sittingParty,
  candidates: [{firstName, surname, elected, party: {abbreviation, votes, percentageShare, percentageShareChange}}],
  majority, percentageTurnout, electorate, declarationTime }
```

**Scottish notional entry** (output/scottish_notionals.json):
```
{ "constituency name": {
    name, number,
    constituency: { SNP: 38.5, Lab: 24.2, ... },   // % share by PA abbreviation
    regional: { SNP: 36.8, Lab: 25.1, ... },
    constituencyTotalVotes, regionalTotalVotes
  }
}
```

`enrichWithNotionals()` computes `percentageShareChange = actual − notional` for each candidate. Always prefers Hanretty notionals over PA-supplied changes for Scottish FPTP results (consistency across all 73 seats).

**GeoJSON properties:** LAD layer uses `LAD25CD`/`LAD25NM`, county layer uses `CTY24CD`/`CTY24NM`, Scottish constituencies use `SPC_CD`/`SPC_NM`, Scottish regions use `SPR_CD`/`SPR_NM`, Welsh constituencies use `SENEDD_CD`/`SENEDD_NM`.

### Deduplication Pattern

Results can have multiple revisions and file types (rush vs result). `dedupByRevision()` always prefers `fileType: "result"` over `"rush"` for the same name, then picks the highest `revision`. Rush messages arrive first with basic winner info but no vote counts; Result messages follow with full candidate vote data. All map components and data consumers use the shared `dedupByRevision()` from utils.js.

## Styling Conventions

- CSS custom properties: `--dm-blue: #004DB3`, `--dm-dark: #1a1a2e`, `--dm-grey: #f4f4f6`, `--dm-border: #e0e0e4`
- No uppercase text anywhere
- Change indicators: green ▲ for gains, red ▼ for losses, grey — for no change
- Responsive breakpoints: 640px (tablet), 480px (mobile)
- Badge component renders dual `.badge-full`/`.badge-short` spans; CSS toggles at 480px
- Text contrast: auto-select white or dark text based on party background colour luminance

## Map Conventions

- Three visual states per area: result → party colour fill, nominated but no result → crosshatch pattern (`url(#crosshatch)`), no election → `#f0f0f2` light grey
- CSS classes: `.map-area--has-result`, `.map-area--awaiting` (pointer cursor), `.map-area` (default)
- Awaiting areas are clickable and searchable — open empty overlay panels with "Awaiting declaration" message
- Result/nomination data matched to GeoJSON via `PA_ONS_LOOKUP` (PA ID → ONS code), with fuzzy name matching as logged fallback. Each map has `resolve*()` functions that check the lookup first.
- Scotland/Wales: all GeoJSON features are backfilled into nomination sets (all constituencies are contested), so areas without test nomination data still show crosshatch and are searchable
- Three filter modes: District (LAD), County, Mayoral — each recolours the map
- **England postcode**: `postcodes.io` general endpoint → `d3.geoContains()` geometric lookup against LAD/county GeoJSON (bypasses stale `admin_district` names for reorganised councils)
- **Scotland postcode**: Scotland-specific `postcodes.io` endpoint first (returns `scottish_parliamentary_constituency` name directly), falls back to general endpoint + `d3.geoContains()` geometric lookup
- **Wales postcode**: `d3.geoContains()` geometric lookup against Senedd GeoJSON
- Overlay always uses tabs as headers (even single results). Tab labels use full council type names.
- `SPECIAL_COUNCIL_NAMES` lookup for official names: Royal Borough of Greenwich, Royal Borough of Kensington and Chelsea, Royal Borough of Kingston upon Thames, City of Westminster
- `SECTION_TITLES` maps council types: Metro → Metropolitan Borough Council, Non-Met → District Council, London → Borough Council, Unitary → Unitary Authority, England → County Council
- Tooltips show short council names (not the special full names)
- Search dropdown uses `z-index: 1000` to draw above map overlay (`100`/`101`) but below tooltip (`9999`)

## Scoreboard / Party Strip / Change Columns Conventions

- NOC (No Overall Control) is filtered from the main sorted party array and shown in its own dedicated row
- NOC row has full styling (no reduced opacity), includes ▲/▼ council change arrows
- Party cell borders use an inner `div` wrapper with `display: flex` (not on `td`)
- Party strip culls low-count parties into "Other" based on container width; NOC is always protected in councils view
- Change columns chart: NOC bar appended at end of councils view (protected from cull into Other)
- Scottish/Welsh scoreboards show aggregate turnout bar below table
- Turnout bar is always the last element in result cards; FPTP card renders declaration time after turnout
- FPTP card order: winner → candidate bars → turnout bar → declaration time
