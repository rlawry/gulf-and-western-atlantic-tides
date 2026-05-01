import json
from skyfield.api import load
from datetime import datetime
import math

# Load tide data
with open('tides.json', 'r') as f:
    tide_data = json.load(f)

# Assume all stations have same time points, take from first
times = [p['t'] for p in tide_data[0]['predictions']]

# Load skyfield
ts = load.timescale()
eph = load('de421.bsp')

moon_positions = []

for time_str in times:
    # Parse time, assuming format '2026-05-01 00:00'
    dt = datetime.fromisoformat(time_str.replace(' ', 'T'))
    t = ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)

    earth = eph['earth']
    moon = eph['moon']
    sun = eph['sun']

    # Geocentric apparent moon position
    astrometric = earth.at(t).observe(moon).apparent()
    ra, dec, distance = astrometric.radec()

    # Sub-lunar longitude: longitude where moon is on the meridian
    # ra.hours and t.gast are both in sidereal hours
    sublon_hours = ra.hours - t.gast
    sublon_deg = (sublon_hours * 15.0) % 360.0

    # Normalize mains to [0, 360)
    if sublon_deg < 0:
        sublon_deg += 360.0

    # Phase
    sun_obs = earth.at(t).observe(sun).apparent()
    moon_obs2 = earth.at(t).observe(moon).apparent()
    phase_angle = moon_obs2.separation_from(sun_obs)
    illuminated = (1 - math.cos(phase_angle.radians)) / 2

    # Waxing: moon's ecliptic longitude is 0-180° ahead of sun's
    _, moon_ecl_lon, _ = moon_obs2.ecliptic_latlon()
    _, sun_ecl_lon, _ = sun_obs.ecliptic_latlon()
    diff = (moon_ecl_lon.degrees - sun_ecl_lon.degrees) % 360
    waxing = bool(diff < 180)

    moon_positions.append({
        'time': time_str,
        'sublunar_longitude': sublon_deg,
        'phase': illuminated,
        'waxing': waxing
    })

# Save to JSON
with open('moon.json', 'w') as f:
    json.dump(moon_positions, f, indent=4)

print("Moon positions saved to moon.json")