import json
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
filepath = os.path.join(script_dir, 'lad_map.geojson')

with open(filepath) as f:
    data = json.load(f)

print("Total features:", len(data['features']))

surrey_old = [
    'Elmbridge', 'Epsom and Ewell', 'Mole Valley',
    'Reigate and Banstead', 'Tandridge',
    'Guildford', 'Runnymede', 'Spelthorne',
    'Surrey Heath', 'Waverley', 'Woking'
]

found_old = []
found_surrey = []

for feat in data['features']:
    p = feat['properties']
    name = p.get('LAD25NM', '')
    if name in surrey_old:
        found_old.append(name)
    if 'surrey' in name.lower():
        found_surrey.append(p.get('LAD25CD', '') + "  " + name)

print("\nOld Surrey districts still present:")
if found_old:
    for n in found_old:
        print("  " + n)
else:
    print("  None")

print("\nSurrey-related features:")
if found_surrey:
    for s in found_surrey:
        print("  " + s)
else:
    print("  None")

# Check FID gaps
fids = sorted([f.get('id', f['properties'].get('FID')) for f in data['features']])
print("\nFID range:", fids[0], "to", fids[-1])
all_fids = set(fids)
expected = set(range(fids[0], fids[-1] + 1))
missing = expected - all_fids
if missing:
    print("Missing FIDs:", sorted(missing))
else:
    print("No FID gaps")

print("\nProperty fields:", list(data['features'][0]['properties'].keys()))
