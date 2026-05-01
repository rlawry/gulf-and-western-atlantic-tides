import requests
import json
from datetime import datetime, timedelta

# Get current date and end date (1 month later)
current_date = datetime.now()
end_date = current_date + timedelta(days=30)

begin_str = current_date.strftime('%Y%m%d')
end_str = end_date.strftime('%Y%m%d')

# Fetch all stations
stations_url = "https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations.json"
response = requests.get(stations_url)
stations_data = response.json()
stations = stations_data['stations']

# Filter stations between High Island, TX (-94.37°W) and Bar Harbor, ME (-68.20°W)
LON_MIN = -94.40   # just west of High Island
LON_MAX = -68.15   # just east of Bar Harbor
filtered_stations = []
for station in stations:
    try:
        lat = float(station['lat'])
        lng = float(station['lng'])
        if 25 <= lat <= 47 and LON_MIN <= lng <= LON_MAX:
            filtered_stations.append(station)
    except (ValueError, KeyError):
        continue

# Sort by longitude (west to east, 0-360 convention) and fill gaps
def lon360(st):
    lng = float(st['lng'])
    return lng + 360 if lng < 0 else lng

filtered_stations.sort(key=lon360)

# Greedy gap-filling: keep a station only if it is at least min_spacing_deg
# away from the most recently kept station
min_spacing_deg = 0.1
selected_stations = []
last_lon = -999.0
for st in filtered_stations:
    l = lon360(st)
    if l - last_lon >= min_spacing_deg:
        selected_stations.append(st)
        last_lon = l

print(f"Selected {len(selected_stations)} candidate stations")

# Gather tide data
tide_data = []
for i, station in enumerate(selected_stations):
    station_id = station['id']
    name = station['name']
    lat = station['lat']
    lng = station['lng']

    predictions_url = f"https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?begin_date={begin_str}&end_date={end_str}&station={station_id}&product=predictions&datum=MLLW&units=english&time_zone=lst_ldt&application=web_services&format=json"
    pred_response = requests.get(predictions_url)
    if pred_response.status_code == 200:
        pred_data = pred_response.json()
        predictions = pred_data.get('predictions', [])
        if predictions:
            tide_data.append({
                'name': name,
                'latitude': lat,
                'longitude': lng,
                'predictions': predictions
            })
            print(f"[{i+1}/{len(selected_stations)}] OK  {name} ({lng})")
        else:
            print(f"[{i+1}/{len(selected_stations)}] no data  {name}")
    else:
        print(f"[{i+1}/{len(selected_stations)}] HTTP {pred_response.status_code}  {name}")

# Save to JSON file
with open('tides.json', 'w') as f:
    json.dump(tide_data, f, indent=4)

print(f"Done. {len(tide_data)} stations saved to tides.json")