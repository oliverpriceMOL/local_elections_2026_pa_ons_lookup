#!/usr/bin/env python3
"""
Convert PA election XML files (nominations, results, rush, SOP) to JSON.

Outputs separate JSON files per election type into output/ directory.
All revisions are preserved — front-end picks the latest.
"""

import json
import os
import re
import xml.etree.ElementTree as ET
from glob import glob
from pathlib import Path

BASE_DIR = Path(__file__).parent
NOMINATIONS_DIR = BASE_DIR / "nominations"
RESULTS_DIR = BASE_DIR / "results" / "results"
OUTPUT_DIR = BASE_DIR / "output"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def try_numeric(val):
    """Coerce a string to int or float if possible, else return as-is."""
    if val is None:
        return None
    # Handle signed change strings like "+3", "-3"
    try:
        if "." in val:
            return float(val)
        return int(val)
    except (ValueError, TypeError):
        return val


def parse_change(val):
    """Parse '+3' / '-3' / '+9.32' change strings to signed number."""
    if val is None:
        return None
    val = val.strip()
    try:
        if "." in val:
            return float(val)
        return int(val)
    except ValueError:
        return val


def attribs_to_dict(el, numeric_keys=None, change_keys=None):
    """Convert element attributes to dict, coercing numeric/change fields."""
    numeric_keys = numeric_keys or set()
    change_keys = change_keys or set()
    d = {}
    for k, v in el.attrib.items():
        if k in change_keys:
            d[k] = parse_change(v)
        elif k in numeric_keys:
            d[k] = try_numeric(v)
        else:
            d[k] = v
    return d


# Common numeric attribute names across schemas
NUMERIC_ATTRS = {
    "electorate", "turnout", "percentageTurnout", "percentageChangeTurnout",
    "majority", "percentageMajority", "percentageChangeMajority",
    "swing", "votes", "percentageShare", "percentageShareChange",
    "percentageChange", "seatsHeld", "seatsOffered", "unopposedReturns",
    "candidates", "seats", "totalSeats", "totalVotes", "totalCouncils",
    "numberOfResults", "totalNumberOfConstituencies", "totalNumberOfCouncils",
    "seatsWon", "netChangeInSeats", "gains", "losses", "forecastSeats",
    "number", "revision", "partyListRank", "candidatesElected",
}

CHANGE_ATTRS = {
    "change", "changeInControl", "percentageShareChange",
    "percentageChangeTurnout", "percentageChangeMajority", "netChangeInSeats",
}


def parse_xml(filepath):
    """Parse an XML file and return the root element."""
    tree = ET.parse(filepath)
    return tree.getroot()


def extract_revision_from_filename(filename):
    """Extract the revision number from filename like 'xxx_Hackney_2.xml' → 2."""
    m = re.search(r'_(\d+)\.xml$', filename)
    return int(m.group(1)) if m else 1


def extract_area_from_filename(filename, prefix):
    """Extract area name from filename by stripping prefix and _N.xml suffix."""
    name = filename
    if name.startswith(prefix):
        name = name[len(prefix):]
    name = re.sub(r'_\d+\.xml$', '', name)
    return name


# ---------------------------------------------------------------------------
# Parsers for each file type
# ---------------------------------------------------------------------------

def parse_candidate(el):
    """Parse a <Candidate> element."""
    d = attribs_to_dict(el, NUMERIC_ATTRS, CHANGE_ATTRS)
    party_el = el.find("Party")
    if party_el is not None:
        d["party"] = attribs_to_dict(party_el, NUMERIC_ATTRS, CHANGE_ATTRS)
    return d


def parse_party(el):
    """Parse a <Party> element."""
    return attribs_to_dict(el, NUMERIC_ATTRS, CHANGE_ATTRS)


# --- Local Nominations ---

def parse_local_nominations():
    entries = []
    for fp in sorted(glob(str(NOMINATIONS_DIR / "Local_Test_nominations_*.xml"))):
        root = parse_xml(fp)
        election_el = root.find("Election")
        election = attribs_to_dict(election_el, NUMERIC_ATTRS)

        for council_el in election_el.findall("Council"):
            council = attribs_to_dict(council_el, NUMERIC_ATTRS)
            council["parties"] = [parse_party(p) for p in council_el.findall("Party")]
            council["election"] = election
            council["_sourceFile"] = os.path.basename(fp)
            entries.append(council)
    return entries


# --- Local Results ---

def parse_local_results():
    entries = []
    for fp in sorted(glob(str(RESULTS_DIR / "Local_Test_result_*.xml"))):
        root = parse_xml(fp)
        revision = try_numeric(root.get("revision", "1"))
        election_el = root.find("Election")
        election = attribs_to_dict(election_el, NUMERIC_ATTRS)

        for council_el in election_el.findall("Council"):
            council = attribs_to_dict(council_el, NUMERIC_ATTRS, CHANGE_ATTRS)
            council["revision"] = revision

            # ElectedCouncillors
            ec_el = council_el.find("ElectedCouncillors")
            if ec_el is not None:
                council["electedCouncillors"] = [parse_party(p) for p in ec_el.findall("Party")]

            # Changes
            ch_el = council_el.find("Changes")
            if ch_el is not None:
                council["changes"] = [parse_party(p) for p in ch_el.findall("Party")]

            # NewCouncil
            nc_el = council_el.find("NewCouncil")
            if nc_el is not None:
                council["newCouncil"] = [parse_party(p) for p in nc_el.findall("Party")]

            council["election"] = election
            council["_sourceFile"] = os.path.basename(fp)
            entries.append(council)
    return entries


# --- Local SOP ---

def parse_local_sop():
    entries = []
    for fp in sorted(glob(str(RESULTS_DIR / "Local_Test_SOP_*.xml"))):
        root = parse_xml(fp)
        sop = attribs_to_dict(root, NUMERIC_ATTRS, CHANGE_ATTRS)

        election_el = root.find("Election")
        if election_el is not None:
            sop["election"] = attribs_to_dict(election_el, NUMERIC_ATTRS)

        parties_el = root.find("Parties")
        if parties_el is not None:
            sop["parties"] = [parse_party(p) for p in parties_el.findall("Party")]

        councils_el = root.find("CouncilsIncluded")
        if councils_el is not None:
            sop["councilsIncluded"] = [
                attribs_to_dict(c, NUMERIC_ATTRS) for c in councils_el.findall("Council")
            ]

        sop["_sourceFile"] = os.path.basename(fp)
        entries.append(sop)
    return entries


# --- FPTP Results (Scottish FPTP constituencies, Mayoral) ---

def parse_fptp_constituency(const_el):
    """Parse a <Constituency> element from FPTP result/rush."""
    const = attribs_to_dict(const_el, NUMERIC_ATTRS, CHANGE_ATTRS)
    const["candidates"] = [parse_candidate(c) for c in const_el.findall("Candidate")]
    return const


def parse_fptp_result_file(fp):
    """Parse a FirstPastThePostResult or FirstPastThePostRush XML."""
    root = parse_xml(fp)
    tag = root.tag  # FirstPastThePostResult or FirstPastThePostRush
    file_type = "rush" if "Rush" in tag else "result"

    result = attribs_to_dict(root, NUMERIC_ATTRS, CHANGE_ATTRS)
    result["fileType"] = file_type

    election_el = root.find("Election")
    election = attribs_to_dict(election_el, NUMERIC_ATTRS)

    constituencies = []
    for const_el in election_el.findall("Constituency"):
        const = parse_fptp_constituency(const_el)
        const["election"] = election
        const["revision"] = result.get("revision", 1)
        const["fileType"] = file_type
        if "declarationTime" in result:
            const["declarationTime"] = result["declarationTime"]
        # Rush-specific attributes on constituency
        for rush_attr in ["winningPartyAbbreviation", "winningPartyName",
                          "sittingPartyAbbreviation", "sittingPartyName",
                          "paStyleMessageText", "change"]:
            if rush_attr in const_el.attrib:
                const[rush_attr] = const_el.attrib[rush_attr]
        const["_sourceFile"] = os.path.basename(fp)
        constituencies.append(const)

    # Previous election data (if present)
    previous = []
    for prev_el in root.findall("PreviousElection"):
        prev = attribs_to_dict(prev_el, NUMERIC_ATTRS, CHANGE_ATTRS)
        prev["constituencies"] = []
        for const_el in prev_el.findall("Constituency"):
            pc = parse_fptp_constituency(const_el)
            prev["constituencies"].append(pc)
        previous.append(prev)

    return constituencies, previous


# --- TopUp Results (Scottish regional, Welsh) ---

def parse_topup_constituency(const_el):
    """Parse a <Constituency> from TopUp result/rush."""
    const = attribs_to_dict(const_el, NUMERIC_ATTRS, CHANGE_ATTRS)
    const["candidates"] = [parse_candidate(c) for c in const_el.findall("Candidate")]
    const["parties"] = [parse_party(p) for p in const_el.findall("Party")]
    return const


def parse_topup_file(fp):
    """Parse a TopUpResult, TopUpRush, or TopUpNominations XML."""
    root = parse_xml(fp)
    tag = root.tag
    if "Rush" in tag:
        file_type = "rush"
    elif "Nominations" in tag:
        file_type = "nominations"
    else:
        file_type = "result"

    result = attribs_to_dict(root, NUMERIC_ATTRS, CHANGE_ATTRS)
    result["fileType"] = file_type

    election_el = root.find("Election")
    election = attribs_to_dict(election_el, NUMERIC_ATTRS)

    constituencies = []
    for const_el in election_el.findall("Constituency"):
        const = parse_topup_constituency(const_el)
        const["election"] = election
        const["revision"] = result.get("revision", 1)
        const["fileType"] = file_type
        if "declarationTime" in result:
            const["declarationTime"] = result["declarationTime"]
        const["_sourceFile"] = os.path.basename(fp)
        constituencies.append(const)

    # Previous election data
    previous = []
    for prev_el in root.findall("PreviousElection"):
        prev = attribs_to_dict(prev_el, NUMERIC_ATTRS, CHANGE_ATTRS)
        prev["constituencies"] = []
        for const_el in prev_el.findall("Constituency"):
            pc = parse_topup_constituency(const_el)
            prev["constituencies"].append(pc)
        previous.append(prev)

    return constituencies, previous


# --- FPTP Nominations (Scottish FPTP constituencies, Mayoral) ---

def parse_fptp_nomination_file(fp):
    """Parse a FirstPastThePostNominations XML."""
    root = parse_xml(fp)
    result = attribs_to_dict(root, NUMERIC_ATTRS)

    election_el = root.find("Election")
    election = attribs_to_dict(election_el, NUMERIC_ATTRS)

    constituencies = []
    for const_el in election_el.findall("Constituency"):
        const = parse_fptp_constituency(const_el)
        const["election"] = election
        const["revision"] = result.get("revision", 1)
        const["fileType"] = "nominations"
        const["_sourceFile"] = os.path.basename(fp)
        constituencies.append(const)

    # Previous election data (Scottish nominations include these)
    previous = []
    for prev_el in root.findall("PreviousElection"):
        prev = attribs_to_dict(prev_el, NUMERIC_ATTRS, CHANGE_ATTRS)
        prev["constituencies"] = []
        for const_el in prev_el.findall("Constituency"):
            pc = parse_fptp_constituency(const_el)
            prev["constituencies"].append(pc)
        previous.append(prev)

    # Previous notional election (boundary changes)
    for prev_el in root.findall("PreviousNotionalElection"):
        prev = attribs_to_dict(prev_el, NUMERIC_ATTRS, CHANGE_ATTRS)
        prev["notional"] = True
        prev["constituencies"] = []
        for const_el in prev_el.findall("Constituency"):
            pc = parse_fptp_constituency(const_el)
            prev["constituencies"].append(pc)
        previous.append(prev)

    return constituencies, previous


# --- Scottish Parliament SOP ---

def parse_scottish_sop():
    entries = []
    for fp in sorted(glob(str(RESULTS_DIR / "Scottish_Parliament_Test_SOP_*.xml"))):
        root = parse_xml(fp)
        sop = attribs_to_dict(root, NUMERIC_ATTRS, CHANGE_ATTRS)

        election_el = root.find("Election")
        if election_el is not None:
            sop["election"] = attribs_to_dict(election_el, NUMERIC_ATTRS)

        parties_el = root.find("Parties")
        if parties_el is not None:
            sop["parties"] = [parse_party(p) for p in parties_el.findall("Party")]

        consts_el = root.find("ConstituenciesIncluded")
        if consts_el is not None:
            sop["constituenciesIncluded"] = [
                attribs_to_dict(c, NUMERIC_ATTRS) for c in consts_el.findall("Constituency")
            ]

        sop["_sourceFile"] = os.path.basename(fp)
        entries.append(sop)
    return entries


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

def process_all():
    OUTPUT_DIR.mkdir(exist_ok=True)

    # ---- Local Elections ----
    print("Parsing local nominations...")
    local_noms = parse_local_nominations()

    print("Parsing local results...")
    local_results = parse_local_results()

    print("Parsing local SOP...")
    local_sop = parse_local_sop()

    # ---- Mayoral Elections ----
    print("Parsing mayoral nominations...")
    mayoral_noms = []
    for fp in sorted(glob(str(NOMINATIONS_DIR / "Mayoral_Elections_Test_nominations_*.xml"))):
        consts, prev = parse_fptp_nomination_file(fp)
        for c in consts:
            if prev:
                c["previousElections"] = prev
            mayoral_noms.append(c)

    print("Parsing mayoral results + rush...")
    mayoral_results = []
    for fp in sorted(glob(str(RESULTS_DIR / "Mayoral_Elections_Test_result_*.xml")) +
                     glob(str(RESULTS_DIR / "Mayoral_Elections_Test_rush_*.xml"))):
        consts, prev = parse_fptp_result_file(fp)
        for c in consts:
            if prev:
                c["previousElections"] = prev
            mayoral_results.append(c)

    # ---- Scottish Parliament ----
    print("Parsing Scottish FPTP nominations...")
    scottish_fptp_noms = []
    for fp in sorted(glob(str(NOMINATIONS_DIR / "Scottish_Parliament_Test_nominations_*.xml"))):
        # Check if FPTP or TopUp
        root = parse_xml(fp)
        if "FirstPastThePost" in root.tag:
            consts, prev = parse_fptp_nomination_file(fp)
            for c in consts:
                if prev:
                    c["previousElections"] = prev
                scottish_fptp_noms.append(c)

    print("Parsing Scottish TopUp nominations...")
    scottish_topup_noms = []
    for fp in sorted(glob(str(NOMINATIONS_DIR / "Scottish_Parliament_Test_nominations_*.xml"))):
        root = parse_xml(fp)
        if "TopUp" in root.tag:
            consts, prev = parse_topup_file(fp)
            for c in consts:
                if prev:
                    c["previousElections"] = prev
                scottish_topup_noms.append(c)

    print("Parsing Scottish FPTP results + rush...")
    scottish_fptp_results = []
    for fp in sorted(glob(str(RESULTS_DIR / "Scottish_Parliament_Test_result_*.xml")) +
                     glob(str(RESULTS_DIR / "Scottish_Parliament_Test_rush_*.xml"))):
        root = parse_xml(fp)
        if "FirstPastThePost" in root.tag:
            consts, prev = parse_fptp_result_file(fp)
            for c in consts:
                if prev:
                    c["previousElections"] = prev
                scottish_fptp_results.append(c)

    print("Parsing Scottish TopUp results + rush...")
    scottish_topup_results = []
    for fp in sorted(glob(str(RESULTS_DIR / "Scottish_Parliament_Test_result_*.xml")) +
                     glob(str(RESULTS_DIR / "Scottish_Parliament_Test_rush_*.xml"))):
        root = parse_xml(fp)
        if "TopUp" in root.tag:
            consts, prev = parse_topup_file(fp)
            for c in consts:
                if prev:
                    c["previousElections"] = prev
                scottish_topup_results.append(c)

    print("Parsing Scottish SOP...")
    scottish_sop = parse_scottish_sop()

    # ---- Welsh Parliament ----
    print("Parsing Welsh nominations...")
    welsh_noms = []
    for fp in sorted(glob(str(NOMINATIONS_DIR / "Welsh_Parliament_Test_nominations_*.xml"))):
        consts, prev = parse_topup_file(fp)
        for c in consts:
            if prev:
                c["previousElections"] = prev
            welsh_noms.append(c)

    print("Parsing Welsh results + rush...")
    welsh_results = []
    for fp in sorted(glob(str(RESULTS_DIR / "Welsh_Parliament_Test_result_*.xml")) +
                     glob(str(RESULTS_DIR / "Welsh_Parliament_Test_rush_*.xml"))):
        consts, prev = parse_topup_file(fp)
        for c in consts:
            if prev:
                c["previousElections"] = prev
            welsh_results.append(c)

    # ---- Write JSON files ----
    outputs = {
        "local_nominations.json": local_noms,
        "local_results.json": {"results": local_results, "sop": local_sop},
        "mayoral_nominations.json": mayoral_noms,
        "mayoral_results.json": mayoral_results,
        "scottish_fptp_nominations.json": scottish_fptp_noms,
        "scottish_fptp_results.json": {"results": scottish_fptp_results, "sop": scottish_sop},
        "scottish_topup_nominations.json": scottish_topup_noms,
        "scottish_topup_results.json": scottish_topup_results,
        "welsh_nominations.json": welsh_noms,
        "welsh_results.json": welsh_results,
    }

    for filename, data in outputs.items():
        outpath = OUTPUT_DIR / filename
        with open(outpath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        # Count entries for summary
        if isinstance(data, dict):
            counts = {k: len(v) for k, v in data.items()}
            print(f"  → {filename}: {counts}")
        else:
            print(f"  → {filename}: {len(data)} entries")

    print(f"\nDone! JSON files written to {OUTPUT_DIR}/")


if __name__ == "__main__":
    process_all()
