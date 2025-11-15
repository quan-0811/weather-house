## Weather Station Data
All (public) weather station location around the world is provided by **Meteostat**[https://meteostat.net/en/]

A JSON file containing all weather stations available at Meteostat, including inventory information and meta data, can be downloaded from this URL: https://bulk.meteostat.net/v2/stations/full.json.gz

Properties:
Each object represents a weather station and has the following properties:

id: Meteostat ID (String)
name: Name in different languages (Object)
country: ISO 3166-1 alpha-2 country code, e.g. CA for Canada (String)
region: ISO 3166-2 state or region code, e.g. TX for Texas (String)
identifiers: Identifiers (Object)
national: National ID (String)
wmo: WMO ID (String)
icao: ICAO ID (String)
iata: IATA ID (String)
location: Geographic location (Object)
latitude: Latitude (Float)
longitude: Longitude (Float)
elevation: Elevation in meters (Integer)
timezone: Time zone (String)
history: Previous locations, identifiers or names (Array)
inventory: Available data by frequency (Object)
hourly: Hourly inventory data (Object)
start: First day (YYYY-MM-DD) of hourly data (String)
end: Last day (YYYY-MM-DD) of hourly data (String)
daily: Daily inventory data (Object)
start: First day (YYYY-MM-DD) of daily data (String)
end: Last day (YYYY-MM-DD) of daily data (String)
monthly: Monthly inventory data (Object)
start: First year (YYYY) of monthly data (String)
end: Last year (YYYY) of monthly data (String)
normals: Climate normals inventory data (Object)
start: First year (YYYY) of climate normals data (String)
end: Last year (YYYY) of climate normals data (String)
