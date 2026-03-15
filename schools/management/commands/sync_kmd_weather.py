import json
import tempfile
import urllib.request
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Sync daily KMD weather data into ClimateRecord from a local CSV/GeoJSON file or a remote URL."

    def add_arguments(self, parser):
        parser.add_argument("--path", help="Local path to a CSV or GeoJSON file from KMD.")
        parser.add_argument("--url", help="Public URL to a CSV or GeoJSON file from KMD.")
        parser.add_argument(
            "--replace",
            action="store_true",
            help="Replace existing climate rows with the newly synced dataset.",
        )

    def handle(self, *args, **options):
        source_path = options.get("path")
        source_url = options.get("url")

        if not source_path and not source_url:
            raise CommandError("Provide either --path or --url.")

        if source_path and source_url:
            raise CommandError("Use only one source at a time: --path or --url.")

        if source_url:
            with urllib.request.urlopen(source_url) as response:
                if response.status != 200:
                    raise CommandError(f"Failed to download KMD file. HTTP {response.status}")

                payload = response.read()
                suffix = Path(source_url).suffix or ".dat"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                    temp_file.write(payload)
                    source_path = temp_file.name

        source = Path(source_path)
        if not source.exists():
            raise CommandError(f"File not found: {source}")

        if source.suffix.lower() != ".csv":
            try:
                with open(source, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except json.JSONDecodeError as exc:
                raise CommandError(f"Invalid GeoJSON payload: {exc}") from exc

            if data.get("type") != "FeatureCollection":
                raise CommandError("Expected a GeoJSON FeatureCollection from KMD.")

        call_command("import_climate", path=str(source), replace=options["replace"])
        self.stdout.write(self.style.SUCCESS("KMD weather sync complete."))
