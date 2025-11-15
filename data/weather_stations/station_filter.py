import json

# Read the full.json file
with open('full.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Filter stations from the US
us_stations = [station for station in data if station.get('country') == 'US']

# Save to full_us.json
with open('full_us.json', 'w', encoding='utf-8') as f:
    json.dump(us_stations, f, indent=2, ensure_ascii=False)

print(f"Filtered {len(us_stations)} US stations from {len(data)} total stations")