import csv
import json
from pathlib import Path

from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand

from schools.models import ClimateRecord


LAT_KEYS = ("lat", "latitude", "y")
LON_KEYS = ("lon", "lng", "long", "longitude", "x")
RAIN_KEYS = ("rain", "rainfall", "precipitation")
TMIN_KEYS = ("tmin", "min_temp", "minimum_temperature")
TMAX_KEYS = ("tmax", "max_temp", "maximum_temperature")


def first_value(row, keys):
    normalized = {str(key).strip().lower(): value for key, value in row.items()}
    for key in keys:
        value = normalized.get(key)
        if value not in (None, ""):
            return value
    return None


def parse_float(value):
    if value in (None, ""):
        return None
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def load_geojson_records(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        geo = json.load(f)

    records = []
    for feature in geo.get("features", []):
        props = feature.get("properties", {})
        coords = feature.get("geometry", {}).get("coordinates", [])
        if len(coords) < 2:
            continue

        lon = parse_float(coords[0])
        lat = parse_float(coords[1])
        if lat is None or lon is None:
            continue

        records.append(
            ClimateRecord(
                location=Point(lon, lat, srid=4326),
                tmin=parse_float(props.get("Tmin")),
                tmax=parse_float(props.get("Tmax")),
                rain=parse_float(props.get("Rain")),
            )
        )
    return records


def load_csv_records(file_path):
    records = []
    with open(file_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            lat = parse_float(first_value(row, LAT_KEYS))
            lon = parse_float(first_value(row, LON_KEYS))
            if lat is None or lon is None:
                continue

            records.append(
                ClimateRecord(
                    location=Point(lon, lat, srid=4326),
                    tmin=parse_float(first_value(row, TMIN_KEYS)),
                    tmax=parse_float(first_value(row, TMAX_KEYS)),
                    rain=parse_float(first_value(row, RAIN_KEYS)),
                )
            )
    return records


class Command(BaseCommand):
    help = "Import climate points from GeoJSON or CSV into PostGIS"

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            default=str(settings.BASE_DIR / "schools" / "static" / "data" / "climate_all.geojson"),
            help="Path to a climate GeoJSON or CSV file.",
        )
        parser.add_argument(
            "--replace",
            action="store_true",
            help="Delete existing climate rows before importing the new file.",
        )

    def handle(self, *args, **options):
        file_path = options["path"]
        suffix = Path(file_path).suffix.lower()

        if options["replace"]:
            deleted_count, _ = ClimateRecord.objects.all().delete()
            self.stdout.write(f"Deleted {deleted_count} existing climate rows.")

        if suffix == ".csv":
            objects = load_csv_records(file_path)
        else:
            objects = load_geojson_records(file_path)

        ClimateRecord.objects.bulk_create(objects, batch_size=1000)
        from schools.views import get_climate_points

        get_climate_points.cache_clear()
        self.stdout.write(self.style.SUCCESS(f"Imported {len(objects)} climate points from {suffix or 'input file'}."))
