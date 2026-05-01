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

# Filter stations in the region: Gulf of Mexico around Florida to Maine
# Approximate bounds: lat 25-45, lon -95 to -65
filtered_stations = []
for station in stations:
    try:
        lat = float(station['lat'])
        lng = float(station['lng'])
        if 25 <= lat <= 45 and -95 <= lng <= -65:
            filtered_stations.append(station)
    except (ValueError, KeyError):
        continue

# Reduce density: sort by latitude and select every 5th station
filtered_stations.sort(key=lambda x: float(x['lat']))
selected_stations = filtered_stations[::5]

# Gather tide data
tide_data = []
for station in selected_stations:
    station_id = station['id']
    name = station['name']
    lat = station['lat']
    lng = station['lng']
    
    predictions_url = f"https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?begin_date={begin_str}&end_date={end_str}&station={station_id}&product=predictions&datum=MLLW&units=english&time_zone=lst_ldt&application=web_services&format=json"
    pred_response = requests.get(predictions_url)
    if pred_response.status_code == 200:
        pred_data = pred_response.json()
        predictions = pred_data.get('predictions', [])
        tide_data.append({
            'name': name,
            'latitude': lat,
            'longitude': lng,
            'predictions': predictions
        })
    else:
        print(f"Failed to fetch data for station {station_id}")

# Save to JSON file
with open('tides.json', 'w') as f:
    json.dump(tide_data, f, indent=4)

print("Tide data gathered and saved to tides.json")