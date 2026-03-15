import geopandas as gpd
import numpy as np
from scipy.interpolate import griddata
import json


counties_file = "schools/static/data/counties.geojson"
climate_file = "schools/static/data/climate_all.geojson"


output_file = "schools/static/data/climate_surface.json"


counties = gpd.read_file(counties_file)


points = gpd.read_file(climate_file)


if "lon" in points.columns:
    lons = points["lon"].values
    lats = points["lat"].values
elif "Lon" in points.columns:
    lons = points["Lon"].values
    lats = points["Lat"].values
else:
    raise ValueError("No longitude/latitude columns found in climate points")

if "Tmax" in points.columns:
    temps = points["Tmax"].values
else:
    raise ValueError("Tmax column not found")

if "Rain" in points.columns:
    rains = points["Rain"].values
else:
    raise ValueError("Rain column not found")


lon_min, lon_max = 33.5, 42.0
lat_min, lat_max = -5.0, 5.0

grid_lon = np.linspace(lon_min, lon_max, 200)
grid_lat = np.linspace(lat_min, lat_max, 200)

grid_lon, grid_lat = np.meshgrid(grid_lon, grid_lat)


temp_surface = griddata(
    (lons, lats),
    temps,
    (grid_lon, grid_lat),
    method='cubic'
)


rain_surface = griddata(
    (lons, lats),
    rains,
    (grid_lon, grid_lat),
    method='cubic'
)


surface_data = []

rows, cols = grid_lon.shape

for i in range(rows):
    for j in range(cols):
        t = temp_surface[i, j]
        r = rain_surface[i, j]
        if np.isnan(t) or np.isnan(r):
            continue
        surface_data.append({
            "lat": float(grid_lat[i, j]),
            "lon": float(grid_lon[i, j]),
            "temp": float(t),
            "rain": float(r)
        })


with open(output_file, "w") as f:
    json.dump(surface_data, f)

print(f"Climate surface JSON saved to {output_file}")