import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
import geopandas as gpd
from shapely.geometry import Point


class Command(BaseCommand):
    help = "Precompute county for climate points"

    def handle(self, *args, **kwargs):

        climate_path = os.path.join(
            settings.BASE_DIR,
            "schools/static/data/climate_all.geojson"
        )

        counties_path = os.path.join(
            settings.BASE_DIR,
            "schools/static/data/counties.geojson"
        )

        output_path = os.path.join(
            settings.BASE_DIR,
            "schools/static/data/climate_processed.json"
        )

        self.stdout.write("Loading climate data...")
        with open(climate_path) as f:
            climate = json.load(f)

        self.stdout.write("Loading counties...")
        counties = gpd.read_file(counties_path)

        points = []

        for feature in climate["features"]:

            prop = feature.get("properties", {})
            lat = prop.get("lat")
            lon = prop.get("lon")

            if lat is None or lon is None:
                continue

            point = Point(lon, lat)
            county_name = None

            for _, county in counties.iterrows():
                if county.geometry.contains(point):
                    county_name = county.get("COUNTY") or county.get("name")
                    break

            points.append({
                "lat": lat,
                "lon": lon,
                "tmin": prop.get("Tmin"),
                "tmax": prop.get("Tmax"),
                "rain": prop.get("Rain"),
                "county": county_name
            })

        self.stdout.write(f"Saving {len(points)} processed points...")

        with open(output_path, "w") as f:
            json.dump(points, f)

        self.stdout.write(self.style.SUCCESS("Climate preprocessing complete!"))