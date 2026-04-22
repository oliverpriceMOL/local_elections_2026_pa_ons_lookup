# UK Local Elections 2026 — Daily Mail Graphics

Interactive election night visualisations for the UK May 2026 elections, built for Daily Mail presentation.

## Status

| Phase | Coverage | Status |
|-------|----------|--------|
| Phase 1 | England — 136 local councils + 6 mayoral elections | ✅ Complete |
| Phase 2 | Scotland (Holyrood) / Wales (Senedd) | ✅ Complete |

## Two-Repo Structure

| Repo | Purpose | Location | URL |
|------|---------|----------|-----|
| **Main** (`local_elections_2026`) | Full project: PA XML data, Python scripts, GeoJSON, front-end | OneDrive (this repo) | [GitHub](https://github.com/oliverpriceMOL/local_elections_2026) |
| **Standalone** (`election_graphics_mockups_2026`) | Mirror of `mock_up_designs/` only — for GitHub Pages previews | `~/election_graphics_mockups_2026/` | [GitHub Pages](https://oliverpricemol.github.io/election_graphics_mockups_2026/) |

The standalone repo contains no Python scripts, XML data, or GeoJSON source files — just the front-end HTML/CSS/JS and pre-built JSON data in `data/`.

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

# 4. Commit and push standalone repo (GitHub Pages auto-deploys)
cd "$STANDALONE"
git add -A && git commit -m "description" && git push
```

## Quick Start

```bash
# 1. Set up Python environment (for data conversion)
python3 -m venv .venv
source .venv/bin/activate

# 2. Convert PA XML data to JSON
python3 scripts/convert_xml_to_json.py

# 3. Build Scottish notionals (Hanretty 2021 on 2026 boundaries)
python3 scripts/build_scottish_notionals.py

# 4. Serve the front-end
cd mock_up_designs
python3 -m http.server 8080
# Open http://localhost:8080
```

## Directory Structure

```
├── .github/
│   └── copilot-instructions.md   # Copilot workspace context (comprehensive)
├── mock_up_designs/               # Front-end (primary deliverable)
│   ├── index.html                 # England — local councils + mayoral
│   ├── scotland.html              # Scotland — Holyrood constituencies + regions
│   ├── wales.html                 # Wales — Senedd constituencies
│   ├── css/
│   │   └── styles.css             # All styles, responsive breakpoints at 640/480px
│   ├── data/                      # Pre-built JSON data (fetched by front-end)
│   │   ├── local_results.json
│   │   ├── local_nominations.json
│   │   ├── mayoral_results.json
│   │   ├── mayoral_nominations.json
│   │   ├── scottish_fptp_results.json
│   │   ├── scottish_fptp_nominations.json
│   │   ├── scottish_topup_results.json
│   │   ├── scottish_topup_nominations.json
│   │   ├── scottish_notionals.json
│   │   ├── welsh_results.json
│   │   └── welsh_nominations.json
│   ├── js/
│   │   ├── party-config.js        # Party colours & names (16 parties)
│   │   ├── tooltip.js             # Viewport-aware tooltip singleton
│   │   ├── utils.js               # Shared utilities (dedup, contrast, turnoutBar, etc.)
│   │   ├── hemicycle.js           # Semi-circular seat chart with hover
│   │   ├── badge.js               # Gain/hold pill badge (responsive text)
│   │   ├── progress.js            # Progress bar counter
│   │   ├── council-card.js        # Council result card (full & mini)
│   │   ├── change-bar.js          # Horizontal ±change bar chart
│   │   ├── council-lookup.js      # Fuzzy name matching (results ↔ GeoJSON)
│   │   ├── election-map.js        # Shared map scaffold & interaction helpers
│   │   ├── england-map.js         # Interactive D3 choropleth (England)
│   │   ├── scotland-map.js        # Interactive D3 choropleth (Scotland)
│   │   ├── wales-map.js           # Interactive D3 choropleth (Wales)
│   │   ├── party-strip.js         # Generic party totals strip (core + England wrapper)
│   │   ├── scoreboard.js          # Generic scoreboard table (core + England wrapper)
│   │   ├── fptp-card.js           # Unified FPTP card (mayoral + constituency)
│   │   ├── list-card.js           # Proportional/regional result card
│   │   ├── change-columns.js      # Shared vertical diverging bar chart core
│   │   ├── party-change-columns.js # England seat/council change columns
│   │   ├── scottish-scoreboard.js  # Scotland scoreboard wrapper
│   │   ├── welsh-scoreboard.js    # Wales scoreboard wrapper
│   │   ├── devolved-strip.js      # Scotland/Wales party strip wrapper
│   │   └── devolved-change-columns.js # Scotland/Wales change columns wrapper
│   ├── map_data/
│   │   ├── lad_map.geojson        # Local Authority District boundaries (LAD25CD/LAD25NM)
│   │   ├── counties_map.geojson   # County council boundaries (CTY24NM)
│   │   ├── scottish_constituencies.geojson
│   │   ├── scottish_regions.geojson
│   │   └── senedd_constituencies.geojson
│   └── tests/                     # Visual test pages
│       ├── badges.html
│       ├── council-cards.html
│       ├── hemicycle.html
│       ├── mayoral-cards.html
│       └── scoreboard.html
├── nominations/                   # PA XML nomination files (~140 councils)
├── results/
│   └── results/                   # PA XML result files (~250 files)
├── pa_elections_schemas/          # PA XSD schemas (18 files)
├── scripts/
│   ├── convert_xml_to_json.py     # XML → JSON converter (main pipeline)
│   ├── build_scottish_notionals.py # Hanretty CSV → scottish_notionals.json
│   ├── check_lad.py               # GeoJSON LAD boundary validator
│   ├── data_audit.py              # Result completeness & consistency audit
│   └── merge_surrey.ipynb         # Surrey boundary change processing
├── data/
│   └── notionals/
│       ├── consty_notionals.csv   # Hanretty 2021 constituency notionals (73 seats)
│       └── list_notionals.csv     # Hanretty 2021 regional list notionals
└── output/                        # Converted JSON files (11 files)
```

## Data Flow

```
PA XML files (nominations/, results/results/)
    │
    ▼
scripts/convert_xml_to_json.py
    │  Parses XML, coerces types, extracts revisions
    ▼
output/*.json → copied to mock_up_designs/data/
    │
    ▼
data/notionals/*.csv → scripts/build_scottish_notionals.py
    │  Converts Hanretty 2021 notional results to JSON
    ▼
output/scottish_notionals.json → copied to mock_up_designs/data/
    │
    ▼
HTML pages — Promise.all fetch:
    index.html    → results + nominations + 2 GeoJSONs
    scotland.html → results + nominations + 2 GeoJSONs + notionals
    wales.html    → results + nominations + 1 GeoJSON
    │  dedupByRevision() → enrichWithNotionals() (Scotland)
    ▼
D3.js components render interactive graphics
```

## Tech Stack

- **D3.js v7** — loaded via CDN, all visualisation and DOM manipulation
- **Vanilla JavaScript** — no frameworks, no modules, no build system. All functions in global scope.
- **Inter** — Google Fonts, weights 400/500/700
- **CSS custom properties** — `--dm-blue: #004DB3`, `--dm-dark: #1a1a2e`, `--dm-grey: #f4f4f6`
- **Python 3** — data conversion scripts
- **postcodes.io API** — postcode → local authority resolution on the map

## Component Architecture

Every component follows the pattern: `functionName(container, data, options)` where `container` is a DOM element. D3 handles all rendering. Components compose — e.g. council-card calls hemicycle, change-bar, and badge internally.

### Key Components

**England Map** (`england-map.js`) — Interactive D3 choropleth with:
- Three filter modes: District (LAD), County, Mayoral
- Three visual states: result (party colour), awaiting declaration (crosshatch pattern), no election (light grey)
- Search by council name or postcode (postcodes.io API)
- Zoom controls (+/−/reset)
- Hover tooltips with gain/hold badges
- Click → fullscreen tabbed overlay showing council/mayoral cards
- Awaiting-declaration areas searchable and clickable (empty overlay panels)
- Special council name lookup (Royal Boroughs, City of Westminster)

**Scotland Map** (`scotland-map.js`) — Interactive D3 choropleth with constituency/region toggle, search, postcode lookup, zoom, tabbed overlay with notional attribution footer, three visual states for awaiting areas.

**Wales Map** (`wales-map.js`) — Interactive D3 choropleth for 16 Senedd constituencies with search, postcode lookup, zoom, overlay, three visual states for awaiting areas.

**Hemicycle** (`hemicycle.js`) — Semi-circular parliament seat chart with convex-hull hover detection and optional majority line.

**Party Strip** (`party-strip.js`) — Generic core with `partyTotalsStrip()` (England) and `devolvedPartyStrip()` (Scotland/Wales) wrappers. Responsive column culling. NOC protected from cull in councils view.

**Scoreboard** (`scoreboard.js`) — Generic core with `partyScoreboard()` (England), `scottishScoreboard()`, and `welshScoreboard()` wrappers. Configurable columns, NOC dedicated row. Scotland/Wales show aggregate turnout bar below table.

**Change Columns** (`change-columns.js`) — Shared vertical diverging bar chart core. `partyChangeColumns()` (England) toggles councillors/councils views with NOC bar in councils view. `devolvedChangeColumns()` (Scotland/Wales) supports total/split (constituency+region) views.

**FPTP Card** (`fptp-card.js`) — Unified card for mayoral (England) and constituency (Scotland) FPTP results. Winner highlight, candidate vote bars with inside/outside label positioning, vote share change indicators, turnout bar, declaration time. Order: winner → candidate bars → turnout bar → declaration time.

**List Card** (`list-card.js`) — Proportional/regional result card with stacked vote bar, elected member pills with party grouping, vote share change indicators, turnout bar at bottom. No majority stat (proportional elections).

## Party Colours

16 parties defined in `party-config.js`. Notable:
- **NOC** (No Overall Control): `#DEA5B2` (dusty pink)
- **Ratepayers**: `#2D6A4F` (dark green)

## PA XML Data Format

Election results arrive as XML files from the Press Association. Key council types: `Metro`, `Non-Met`, `London`, `Unitary`, `England` (county councils). Each result carries a `revision` number — later revisions supersede earlier ones.

The conversion script (`scripts/convert_xml_to_json.py`) handles:
- Local council nominations and results
- Mayoral elections (FPTP format)
- Scottish Parliament (FPTP + regional top-up)
- Welsh Parliament (constituency results)

See `pa_elections_schemas/` for the full XSD schema definitions.

## Known Limitations

**Council↔GeoJSON matching**: The map currently matches PA result/nomination names to GeoJSON feature names using fuzzy string normalisation (`council-lookup.js`). For the final production version, this should be replaced with a hardcoded lookup table mapping PA council IDs (`paId`) to ONS/GSS codes (`LAD25CD`, `SPC_CD`, `SENEDD_CD` etc.) for reliable matching.

## Git

- **Main repo**: `https://github.com/oliverpriceMOL/local_elections_2026.git` — branch `main`
- **Standalone repo**: `https://github.com/oliverpriceMOL/election_graphics_mockups_2026.git` — branch `main`, GitHub Pages at `https://oliverpricemol.github.io/election_graphics_mockups_2026/`
