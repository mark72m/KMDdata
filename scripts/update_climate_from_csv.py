import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


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


def build_feature(row):
    lat = parse_float(first_value(row, LAT_KEYS))
    lon = parse_float(first_value(row, LON_KEYS))
    if lat is None or lon is None:
        return None

    return {
        "type": "Feature",
        "properties": {
            "Rain": parse_float(first_value(row, RAIN_KEYS)),
            "Tmin": parse_float(first_value(row, TMIN_KEYS)),
            "Tmax": parse_float(first_value(row, TMAX_KEYS)),
        },
        "geometry": {
            "type": "Point",
            "coordinates": [lon, lat],
        },
    }


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: python scripts/update_climate_from_csv.py <csv_path> [output_geojson_path] [source_name]"
        )
        raise SystemExit(1)

    project_root = Path(__file__).resolve().parents[1]
    csv_path = Path(sys.argv[1]).resolve()
    output_path = (
        Path(sys.argv[2]).resolve()
        if len(sys.argv) > 2
        else project_root / "schools" / "static" / "data" / "climate_all.geojson"
    )
    source_name = sys.argv[3] if len(sys.argv) > 3 else "manual_csv_update"
    metadata_path = project_root / "schools" / "static" / "data" / "climate_metadata.json"

    if not csv_path.exists():
        print(f"CSV file not found: {csv_path}")
        raise SystemExit(1)

    features = []
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            feature = build_feature(row)
            if feature:
                features.append(feature)

    payload = {
        "type": "FeatureCollection",
        "features": features,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, separators=(",", ":"))

    metadata = {
        "source": source_name,
        "input_file": str(csv_path),
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "record_count": len(features),
    }
    with open(metadata_path, "w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)

    print(f"Wrote {len(features)} climate points to {output_path}")
    print(f"Wrote climate metadata to {metadata_path}")


if __name__ == "__main__":
    main()
