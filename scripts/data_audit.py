import json
from collections import Counter

with open("output/local_results.json") as f:
    data = json.load(f)

results = data["results"] if isinstance(data, dict) else data

parties = set()
seat_counts = []
for r in results:
    nc = r.get("newCouncil", [])
    total = sum(p["seats"] for p in nc)
    seat_counts.append((r["name"], total, r.get("type", "?")))
    for p in nc:
        parties.add(p["name"])

seat_counts.sort(key=lambda x: x[1])
print("=== SEAT COUNT RANGE ===")
for name, seats, ctype in seat_counts[:5]:
    print(f"  {name}: {seats} ({ctype})")
print("  ...")
for name, seats, ctype in seat_counts[-5:]:
    print(f"  {name}: {seats} ({ctype})")
print(f"\nMin: {seat_counts[0][1]}, Max: {seat_counts[-1][1]}")
print(f"Median: {seat_counts[len(seat_counts)//2][1]}")

print(f"\n=== ALL PARTY ABBREVIATIONS ({len(parties)}) ===")
for p in sorted(parties):
    print(f"  {p}")

goh = set()
for r in results:
    goh.add(r.get("gainOrHold", ""))
print("\n=== gainOrHold VALUES ===")
for g in sorted(goh):
    print(f'  "{g}"')

wp = set()
for r in results:
    wp.add(r.get("winningParty", ""))
print("\n=== winningParty VALUES ===")
for w in sorted(wp):
    print(f'  "{w}"')

types = Counter(r.get("type", "?") for r in results)
print("\n=== COUNCIL TYPES ===")
for t, c in types.most_common():
    print(f"  {t}: {c}")

unique = set(r["name"] for r in results)
print(f"\nUnique councils: {len(unique)}")
print(f"Total entries: {len(results)}")
