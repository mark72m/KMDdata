import json

from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand

from schools.models import ClimateRecord


class Command(BaseCommand):
    help = "Import climate points from GeoJSON into PostGIS"

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            default=str(settings.BASE_DIR / "schools" / "static" / "data" / "climate_all.geojson"),
            help="Path to a climate GeoJSON file.",
        )
        parser.add_argument(
            "--replace",
            action="store_true",
            help="Delete existing climate rows before importing the new file.",
        )

    def handle(self, *args, **options):
        file_path = options["path"]

        with open(file_path, "r", encoding="utf-8") as f:
            geo = json.load(f)

        if options["replace"]:
            deleted_count, _ = ClimateRecord.objects.all().delete()
            self.stdout.write(f"Deleted {deleted_count} existing climate rows.")

        objects = []
        for feature in geo.get("features", []):
            props = feature.get("properties", {})
            coords = feature.get("geometry", {}).get("coordinates", [])
            if len(coords) < 2:
                continue

            objects.append(
                ClimateRecord(
                    location=Point(coords[0], coords[1], srid=4326),
                    tmin=props.get("Tmin"),
                    tmax=props.get("Tmax"),
                    rain=props.get("Rain"),
                )
            )

        ClimateRecord.objects.bulk_create(objects, batch_size=1000)
        from schools.views import get_climate_points

        get_climate_points.cache_clear()
        self.stdout.write(self.style.SUCCESS(f"Imported {len(objects)} climate points."))
