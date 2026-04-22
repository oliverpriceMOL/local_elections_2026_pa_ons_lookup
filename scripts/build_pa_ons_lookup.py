#!/usr/bin/env python3
"""
Build PA ID → ONS code lookup table.

Reads PA nomination JSON files and GeoJSON map files, joins on normalised name,
and outputs:
  - output/pa_ons_lookup.json   (machine-readable, for review)
  - mock_up_designs/js/pa-ons-lookup.js  (global JS object for front-end)

PA identifier fields:
  - England local/county councils: @paId on <Council>  (4-digit)
  - England mayoral: @number on <Constituency>          (1–6)
  - Scottish FPTP: @number on <Constituency>            (1–73)
  - Scottish TopUp: @number on <Constituency>           (101–108)
  - Welsh Senedd: @number on <Constituency>             (1–16)

GeoJSON ONS code fields:
  - LAD:    LAD25CD / LAD25NM
  - County: CTY24CD / CTY24NM
  - Scottish constituency: SPC_CD / SPC_NM
  - Scottish region: SPR_CD / SPR_NM
  - Welsh Senedd: SENEDD_CD / SENEDD_NM
"""

import csv
import json
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(ROOT, "mock_up_designs", "data")
MAP_DIR = os.path.join(ROOT, "mock_up_designs", "map_data")
NOTIONALS_DIR = os.path.join(ROOT, "data", "notionals")
OUTPUT_DIR = os.path.join(ROOT, "output")
JS_DIR = os.path.join(ROOT, "mock_up_designs", "js")


# ── Name normalisation (mirrors council-lookup.js normaliseName) ──

def normalise_name(name):
    """Replicate the JS normaliseName() function exactly."""
    s = name
    s = s.replace("&", "and")
    s = re.sub(r"-", " ", s)
    s = re.sub(r",\s*(City|County)\s+of$", "", s, flags=re.IGNORECASE)
    s = s.replace(".", "")
    s = s.strip().lower()
    return s


# Manual overrides matching council-lookup.js NAME_OVERRIDES
NAME_OVERRIDES = {
    "Hull": "Kingston upon Hull, City of",
    "St Helens": "St. Helens",
    "Newcastle-upon-Tyne": "Newcastle upon Tyne",
    "Kingston-upon-Thames": "Kingston upon Thames",
    "Richmond-upon-Thames": "Richmond upon Thames",
}

# County councils (type="England" in PA results)
COUNTY_COUNCILS = {"Essex", "Hampshire", "Norfolk", "Suffolk", "East Sussex", "West Sussex"}


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def ensure_list(x):
    """Handle the xmltodict single-item quirk."""
    if isinstance(x, list):
        return x
    return [x]


# ── Extract PA areas from nomination files ──

def extract_local_nominations(data):
    """Extract councils: list of {paId, name, type}."""
    areas = []
    for msg in ensure_list(data):
        election = msg["LocalElectionNominations"]["Election"]
        for council in ensure_list(election["Council"]):
            areas.append({
                "paId": council["@paId"],
                "name": council["@name"],
                "type": council.get("@type", ""),
            })
    return areas


def extract_fptp_nominations(data):
    """Extract constituencies: list of {number, name}."""
    areas = []
    for msg in ensure_list(data):
        election = msg["FirstPastThePostNominations"]["Election"]
        for cons in ensure_list(election["Constituency"]):
            areas.append({
                "number": cons["@number"],
                "name": cons["@name"],
            })
    return areas


def extract_topup_nominations(data):
    """Extract regions/constituencies: list of {number, name}."""
    areas = []
    for msg in ensure_list(data):
        election = msg["TopUpNominations"]["Election"]
        for cons in ensure_list(election["Constituency"]):
            areas.append({
                "number": cons["@number"],
                "name": cons["@name"],
            })
    return areas


# ── Extract GeoJSON features ──

def extract_geo_features(geojson, code_field, name_field):
    """Return dict of {normalised_name: {code, name}}."""
    index = {}
    for feat in geojson["features"]:
        props = feat["properties"]
        code = props.get(code_field)
        name = props.get(name_field)
        if code and name:
            index[normalise_name(name)] = {"code": code, "name": name}
    return index


# ── Matching ──

def match_area(pa_name, geo_index):
    """Try to match a PA name against a GeoJSON normalised-name index.
    Returns the ONS code or None."""
    # 1. Check NAME_OVERRIDES first
    if pa_name in NAME_OVERRIDES:
        override = NAME_OVERRIDES[pa_name]
        norm = normalise_name(override)
        if norm in geo_index:
            return geo_index[norm]["code"]

    # 2. Direct normalised match
    norm = normalise_name(pa_name)
    if norm in geo_index:
        return geo_index[norm]["code"]

    return None


def build_lookup():
    """Build the complete PA → ONS lookup."""
    unmatched = []

    # ── Load GeoJSON indices ──
    lad_geo = extract_geo_features(
        load_json(os.path.join(MAP_DIR, "lad_map.geojson")), "LAD25CD", "LAD25NM"
    )
    county_geo = extract_geo_features(
        load_json(os.path.join(MAP_DIR, "counties_map.geojson")), "CTY24CD", "CTY24NM"
    )
    scot_const_geo = extract_geo_features(
        load_json(os.path.join(MAP_DIR, "scottish_constituencies.geojson")), "SPC_CD", "SPC_NM"
    )
    scot_reg_geo = extract_geo_features(
        load_json(os.path.join(MAP_DIR, "scottish_regions.geojson")), "SPR_CD", "SPR_NM"
    )
    wales_geo = extract_geo_features(
        load_json(os.path.join(MAP_DIR, "senedd_constituencies.geojson")), "SENEDD_CD", "SENEDD_NM"
    )

    # ── 1. England local councils (paId → LAD25CD or CTY24CD) ──
    local_noms = extract_local_nominations(load_json(os.path.join(DATA_DIR, "local_nominations.json")))
    local_councils = {}
    for area in local_noms:
        pa_id = area["paId"]
        name = area["name"]
        council_type = area["type"]

        # County councils go to county layer
        if name in COUNTY_COUNCILS or council_type == "England":
            code = match_area(name, county_geo)
            layer = "county"
        else:
            code = match_area(name, lad_geo)
            layer = "lad"

        if code:
            local_councils[pa_id] = {"code": code, "name": name, "layer": layer}
        else:
            unmatched.append(("localCouncils", pa_id, name, council_type))

    # ── 2. England mayoral (number → LAD25CD) ──
    mayoral_noms = extract_fptp_nominations(load_json(os.path.join(DATA_DIR, "mayoral_nominations.json")))
    mayoral_areas = {}
    for area in mayoral_noms:
        num = area["number"]
        name = area["name"]
        code = match_area(name, lad_geo)
        if code:
            mayoral_areas[num] = {"code": code, "name": name}
        else:
            unmatched.append(("mayoralAreas", num, name, ""))

    # ── 3. Scottish FPTP constituencies (number → SPC_CD) ──
    scot_fptp_noms = extract_fptp_nominations(load_json(os.path.join(DATA_DIR, "scottish_fptp_nominations.json")))
    scottish_constituencies = {}
    for area in scot_fptp_noms:
        num = area["number"]
        name = area["name"]
        code = match_area(name, scot_const_geo)
        if code:
            scottish_constituencies[num] = {"code": code, "name": name}
        else:
            unmatched.append(("scottishConstituencies", num, name, ""))

    # Backfill from Hanretty notionals CSV for constituencies missing from test nominations
    notionals_path = os.path.join(NOTIONALS_DIR, "consty_notionals.csv")
    if os.path.exists(notionals_path):
        with open(notionals_path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                num = row["Number"]
                if num not in scottish_constituencies:
                    name = row["NAME"]
                    code = match_area(name, scot_const_geo)
                    if code:
                        scottish_constituencies[num] = {"code": code, "name": name}
                        print(f"  Backfilled from notionals: {num} → {name} → {code}")
                    else:
                        unmatched.append(("scottishConstituencies (notionals)", num, name, ""))

    # ── 4. Scottish TopUp regions (number → SPR_CD) ──
    scot_topup_noms = extract_topup_nominations(load_json(os.path.join(DATA_DIR, "scottish_topup_nominations.json")))
    scottish_regions = {}
    for area in scot_topup_noms:
        num = area["number"]
        name = area["name"]
        code = match_area(name, scot_reg_geo)
        if code:
            scottish_regions[num] = {"code": code, "name": name}
        else:
            unmatched.append(("scottishRegions", num, name, ""))

    # Backfill Scottish regions from notionals if any are missing
    reg_notionals_path = os.path.join(NOTIONALS_DIR, "list_notionals.csv")
    if os.path.exists(reg_notionals_path):
        with open(reg_notionals_path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                num = row["Number"]
                if num not in scottish_regions:
                    name = row["NAME"]
                    code = match_area(name, scot_reg_geo)
                    if code:
                        scottish_regions[num] = {"code": code, "name": name}
                        print(f"  Backfilled region from notionals: {num} → {name} → {code}")

    # ── 5. Welsh Senedd (number → SENEDD_CD) ──
    welsh_noms = extract_topup_nominations(load_json(os.path.join(DATA_DIR, "welsh_nominations.json")))
    welsh_constituencies = {}
    for area in welsh_noms:
        num = area["number"]
        name = area["name"]
        code = match_area(name, wales_geo)
        if code:
            welsh_constituencies[num] = {"code": code, "name": name}
        else:
            unmatched.append(("welshConstituencies", num, name, ""))

    return {
        "localCouncils": local_councils,
        "mayoralAreas": mayoral_areas,
        "scottishConstituencies": scottish_constituencies,
        "scottishRegions": scottish_regions,
        "welshConstituencies": welsh_constituencies,
    }, unmatched


def write_json(lookup, path):
    """Write the full lookup (with names for review) to JSON."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(lookup, f, indent=2, ensure_ascii=False)
    print(f"  Written: {path}")


def write_js(lookup, path):
    """Write a minimal JS file with code-only lookup objects."""
    lines = [
        "/**",
        " * PA ID → ONS code lookup table",
        " * Generated by scripts/build_pa_ons_lookup.py — do not edit manually",
        " */",
        "var PA_ONS_LOOKUP = {",
    ]

    sections = [
        ("localCouncils", "paId → LAD25CD or CTY24CD"),
        ("mayoralAreas", "number → LAD25CD"),
        ("scottishConstituencies", "number → SPC_CD"),
        ("scottishRegions", "number → SPR_CD"),
        ("welshConstituencies", "number → SENEDD_CD"),
    ]

    for i, (key, comment) in enumerate(sections):
        entries = lookup[key]
        # Build code-only map: { "id": "ONS_CODE", ... }
        code_map = {}
        for pa_key, val in sorted(entries.items(), key=lambda x: int(x[0]) if x[0].isdigit() else x[0]):
            code_map[pa_key] = val["code"]

        trailing_comma = "," if i < len(sections) - 1 else ""
        lines.append(f"  // {comment}")
        lines.append(f"  {key}: {{")
        for j, (k, v) in enumerate(code_map.items()):
            entry_comma = "," if j < len(code_map) - 1 else ""
            # Add name as inline comment for readability
            name = entries[k]["name"]
            lines.append(f'    "{k}": "{v}"{entry_comma}  // {name}')
        lines.append(f"  }}{trailing_comma}")

    lines.append("};")
    lines.append("")

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  Written: {path}")


def main():
    print("Building PA → ONS lookup table...")
    print()

    lookup, unmatched = build_lookup()

    # Summary
    for key in lookup:
        print(f"  {key}: {len(lookup[key])} matched")

    print()

    if unmatched:
        print(f"  WARNING: {len(unmatched)} unmatched areas:")
        for section, pa_id, name, extra in unmatched:
            print(f"    [{section}] id={pa_id}, name={name}" + (f", type={extra}" if extra else ""))
        print()

    # Write outputs
    json_path = os.path.join(OUTPUT_DIR, "pa_ons_lookup.json")
    js_path = os.path.join(JS_DIR, "pa-ons-lookup.js")

    write_json(lookup, json_path)
    write_js(lookup, js_path)

    print()
    if unmatched:
        print(f"Done with {len(unmatched)} warnings — review unmatched entries above.")
        sys.exit(1)
    else:
        print("Done — all areas matched successfully.")


if __name__ == "__main__":
    main()
