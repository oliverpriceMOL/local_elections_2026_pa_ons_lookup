#!/usr/bin/env python3
"""
Build scottish_notionals.json from Hanretty's notional 2021 results on 2026 boundaries.

Source: https://github.com/chrishanretty/sp2026_notionals
Input:  data/notionals/consty_notionals.csv  (constituency FPTP votes)
        data/notionals/list_notionals.csv    (regional list votes)
Output: output/scottish_notionals.json

The JSON maps constituency name → { constituency: {abbr: pctShare, …}, regional: {abbr: pctShare, …} }
so the front-end can compute percentageShareChange = actual - notional.
"""

import csv
import json
import os
import re

# Hanretty CSV column → PA party abbreviation
PARTY_MAP_CONSTY = {
    "Cons": "C",
    "Greens": "Green",
    "Lab": "Lab",
    "LDem": "LD",
    "SNP": "SNP",
    "Other": "Other",
}

PARTY_MAP_LIST = {
    "Cons": "C",
    "Greens": "Green",
    "Lab": "Lab",
    "LDem": "LD",
    "SNP": "SNP",
    "Alba": "Alba",
    "Reform": "Reform",
    "Other": "Other",
}

# Hanretty uses "and" where PA uses "&" — normalise for matching
def normalise_name(name):
    """Normalise constituency name for fuzzy matching."""
    s = name.strip()
    s = re.sub(r"\s+", " ", s)           # collapse whitespace
    s = s.replace(" and ", " & ")         # Hanretty → PA style
    s = s.replace(",", ",")               # keep commas
    return s


def parse_csv(path, party_map):
    """Parse a Hanretty CSV into {name: {abbr: percentageShare}}."""
    result = {}
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_name = row["NAME"]
            name = normalise_name(raw_name)

            # Compute total valid votes (exclude DNV)
            vote_cols = [c for c in party_map]
            total_votes = sum(int(row[c]) for c in vote_cols)

            if total_votes == 0:
                continue

            shares = {}
            for csv_col, pa_abbr in party_map.items():
                votes = int(row[csv_col])
                if votes > 0:
                    pct = round(votes / total_votes * 100, 2)
                    shares[pa_abbr] = pct

            result[name] = {
                "number": int(row["Number"]),
                "shares": shares,
                "totalVotes": total_votes,
            }

    return result


def main():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    consty_path = os.path.join(base, "data", "notionals", "consty_notionals.csv")
    list_path = os.path.join(base, "data", "notionals", "list_notionals.csv")
    out_path = os.path.join(base, "output", "scottish_notionals.json")

    consty = parse_csv(consty_path, PARTY_MAP_CONSTY)
    regional = parse_csv(list_path, PARTY_MAP_LIST)

    # Merge into single dict keyed by name
    all_names = sorted(set(consty.keys()) | set(regional.keys()))
    output = {}
    for name in all_names:
        entry = {"name": name}
        if name in consty:
            entry["constituency"] = consty[name]["shares"]
            entry["constituencyTotalVotes"] = consty[name]["totalVotes"]
            entry["number"] = consty[name]["number"]
        if name in regional:
            entry["regional"] = regional[name]["shares"]
            entry["regionalTotalVotes"] = regional[name]["totalVotes"]
            if "number" not in entry:
                entry["number"] = regional[name]["number"]
        output[name] = entry

    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Wrote {len(output)} constituencies to {out_path}")

    # Sanity check: print Skye
    for k, v in output.items():
        if "Skye" in k:
            print(f"\nSample — {k}:")
            print(json.dumps(v, indent=2))


if __name__ == "__main__":
    main()
