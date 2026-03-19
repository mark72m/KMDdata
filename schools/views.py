import json
from functools import lru_cache

from django.conf import settings
from django.db import DatabaseError, OperationalError
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .models import ClimateRecord, School, SubCounty


KENYA_BOUNDS = {
    "min_lat": -5.2,
    "max_lat": 5.5,
    "min_lon": 33.5,
    "max_lon": 42.5,
}


def map_view(request):
    return render(request, "map.html")


def region_view(request):
    region_name = request.GET.get("region", "").lower()
    return render(request, "region.html", {"region_name": region_name})


def healthz(request):
    return JsonResponse({"status": "ok"})


def parse_int(value, default, minimum=None, maximum=None):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default

    if minimum is not None:
        parsed = max(minimum, parsed)
    if maximum is not None:
        parsed = min(maximum, parsed)
    return parsed


def point_within_kenya(lat, lon):
    try:
        lat = float(lat)
        lon = float(lon)
    except (TypeError, ValueError):
        return False

    return (
        KENYA_BOUNDS["min_lat"] <= lat <= KENYA_BOUNDS["max_lat"]
        and KENYA_BOUNDS["min_lon"] <= lon <= KENYA_BOUNDS["max_lon"]
    )


def normalize_school_point(lat, lon):
    try:
        lat = float(lat)
        lon = float(lon)
    except (TypeError, ValueError):
        return None

    if point_within_kenya(lat, lon):
        return lat, lon

    if point_within_kenya(lon, lat):
        return lon, lat

    return None


def value_matches(actual, expected):
    return (actual or "").strip().lower() == (expected or "").strip().lower()


def matches_bbox(lat, lon, bbox):
    if not bbox:
        return True
    min_lon, min_lat, max_lon, max_lat = bbox
    return min_lat <= lat <= max_lat and min_lon <= lon <= max_lon


def parse_bbox(request):
    bbox = request.GET.get("bbox")
    if not bbox:
        return None

    try:
        min_lon, min_lat, max_lon, max_lat = [float(part.strip()) for part in bbox.split(",")]
    except (TypeError, ValueError):
        return None

    if min_lon > max_lon or min_lat > max_lat:
        return None

    return [min_lon, min_lat, max_lon, max_lat]


def school_payload(name, county, sub_county, lat, lon, **extra):
    return {
        "name": name,
        "UIC": extra.get("UIC"),
        "knec_code": extra.get("knec_code"),
        "region": extra.get("region"),
        "county": county,
        "sub_county": sub_county,
        "division": extra.get("division"),
        "zone": extra.get("zone"),
        "lat": lat,
        "lon": lon,
    }


@lru_cache(maxsize=1)
def load_school_json():
    with open(settings.BASE_DIR / "schools.json", "r", encoding="utf-8") as f:
        raw = json.load(f)

    data = []
    for item in raw:
        coords = normalize_school_point(item.get("lat"), item.get("lon"))
        if not coords:
            continue

        lat, lon = coords
        data.append(
            school_payload(
                name=item.get("name"),
                county=item.get("county"),
                sub_county=item.get("sub_county"),
                lat=lat,
                lon=lon,
                UIC=item.get("UIC"),
                knec_code=item.get("knec_code"),
                region=item.get("region"),
                division=item.get("division"),
                zone=item.get("zone"),
            )
        )
    return data


@lru_cache(maxsize=1)
def load_school_db():
    data = []
    for school in School.objects.all():
        if not school.location:
            continue

        coords = normalize_school_point(school.location.y, school.location.x)
        if not coords:
            continue

        lat, lon = coords
        data.append(
            school_payload(
                name=school.institution_name,
                county=school.county,
                sub_county=school.sub_county,
                lat=lat,
                lon=lon,
                UIC=school.UIC,
                knec_code=school.knec_code,
                region=school.region,
                division=school.division,
                zone=school.zone,
            )
        )
    return data


def get_school_data():
    try:
        db_data = load_school_db()
        if db_data:
            return db_data
    except (OperationalError, DatabaseError):
        pass

    try:
        return load_school_json()
    except Exception:
        return []


@lru_cache(maxsize=4)
def load_geojson_data(filename):
    with open(settings.BASE_DIR / "schools" / "static" / "data" / filename, "r", encoding="utf-8") as f:
        return json.load(f)


def get_counties_geojson():
    return load_geojson_data("counties.geojson")


def get_subcounties_geojson():
    try:
        data = {"type": "FeatureCollection", "features": []}
        for subcounty in SubCounty.objects.all():
            data["features"].append(
                {
                    "type": "Feature",
                    "properties": {
                        "name": subcounty.name,
                        "county": subcounty.county_name,
                    },
                    "geometry": json.loads(subcounty.geom.geojson),
                }
            )
        return data
    except (OperationalError, DatabaseError):
        return load_geojson_data("subcounties.geojson")


@lru_cache(maxsize=1)
def get_climate_points():
    try:
        if ClimateRecord.objects.exists():
            points = []
            for record in ClimateRecord.objects.all().iterator():
                lat = record.location.y
                lon = record.location.x
                if not point_within_kenya(lat, lon):
                    continue
                points.append(
                    {
                        "lon": lon,
                        "lat": lat,
                        "rain": record.rain,
                        "tmin": record.tmin,
                        "tmax": record.tmax,
                    }
                )
            if points:
                return points
    except (OperationalError, DatabaseError):
        pass

    geo = load_geojson_data("climate_all.geojson")

    points = []
    for feature in geo["features"]:
        props = feature.get("properties", {})
        coords = feature.get("geometry", {}).get("coordinates", [])
        if len(coords) < 2:
            continue

        lon = coords[0]
        lat = coords[1]
        if not point_within_kenya(lat, lon):
            continue

        points.append(
            {
                "lon": lon,
                "lat": lat,
                "rain": props.get("Rain"),
                "tmin": props.get("Tmin"),
                "tmax": props.get("Tmax"),
            }
        )
    return points


@lru_cache(maxsize=1)
def get_climate_metadata():
    metadata_path = settings.BASE_DIR / "schools" / "static" / "data" / "climate_metadata.json"
    if metadata_path.exists():
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            pass

    return {
        "source": "bundled_climate_file",
        "updated_at_utc": None,
        "record_count": len(get_climate_points()),
    }


def to_geojson_features(records, property_keys):
    features = []
    for record in records:
        properties = {key: record.get(key) for key in property_keys}
        features.append(
            {
                "type": "Feature",
                "properties": properties,
                "geometry": {
                    "type": "Point",
                    "coordinates": [record["lon"], record["lat"]],
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}


def apply_school_filters(data, request):
    county = request.GET.get("county")
    subcounty = request.GET.get("subcounty")
    query = request.GET.get("q", "").strip().lower()
    bbox = parse_bbox(request)

    filtered = []
    for item in data:
        if county and not value_matches(item.get("county"), county):
            continue
        if subcounty and not value_matches(item.get("sub_county"), subcounty):
            continue
        if query:
            haystack = " ".join(
                str(item.get(key) or "")
                for key in ("name", "county", "sub_county", "region", "division", "zone")
            ).lower()
            if query not in haystack:
                continue
        if not matches_bbox(item["lat"], item["lon"], bbox):
            continue
        filtered.append(item)
    return filtered


def apply_climate_filters(data, request):
    bbox = parse_bbox(request)
    field = request.GET.get("field")

    filtered = []
    for item in data:
        if field and item.get(field) is None:
            continue
        if not matches_bbox(item["lat"], item["lon"], bbox):
            continue
        filtered.append(item)
    return filtered


def schools_data(request):
    return JsonResponse(get_school_data(), safe=False)


def climate_surface(request):
    return JsonResponse(get_climate_points(), safe=False)


def climate_metadata(request):
    return JsonResponse(get_climate_metadata())


def api_index(request):
    data = {
        "service": "kenya_map_api",
        "datasets": {
            "counties": len(get_counties_geojson().get("features", [])),
            "subcounties": len(get_subcounties_geojson().get("features", [])),
            "schools": len(get_school_data()),
            "climate_points": len(get_climate_points()),
        },
        "endpoints": {
            "counties_list": "/api/counties/",
            "counties_geojson": "/api/counties/geojson/",
            "subcounties_list": "/api/subcounties/list/",
            "subcounties_geojson": "/api/subcounties/",
            "schools": "/api/schools/?county=Nairobi%20City&subcounty=Kibra&bbox=36.7,-1.5,37.1,-1.1&format=geojson",
            "climate": "/api/climate/?field=rain&bbox=36.7,-1.5,37.1,-1.1&format=geojson",
        },
    }
    return JsonResponse(data)


def counties_api(request):
    geojson = get_counties_geojson()
    counties = []
    for feature in geojson.get("features", []):
        props = feature.get("properties", {})
        counties.append(
            {
                "name": props.get("adm1_name") or props.get("COUNTY") or props.get("name"),
                "code": props.get("adm1_pcode"),
                "country": props.get("adm0_name"),
            }
        )
    counties.sort(key=lambda item: (item["name"] or "").lower())
    return JsonResponse({"count": len(counties), "results": counties})


def counties_geojson_api(request):
    return JsonResponse(get_counties_geojson())


def subcounties_list_api(request):
    county = request.GET.get("county")
    geojson = get_subcounties_geojson()
    results = []

    for feature in geojson.get("features", []):
        props = feature.get("properties", {})
        item = {
            "name": props.get("name") or props.get("adm2_name"),
            "county": props.get("county") or props.get("adm1_name"),
            "code": props.get("adm2_pcode"),
        }
        if county and not value_matches(item["county"], county):
            continue
        results.append(item)

    results.sort(key=lambda item: ((item["county"] or "").lower(), (item["name"] or "").lower()))
    return JsonResponse({"count": len(results), "results": results})


def subcounties_api(request):
    county = request.GET.get("county")
    geojson = get_subcounties_geojson()
    if not county:
        return JsonResponse(geojson)

    filtered = []
    for feature in geojson.get("features", []):
        props = feature.get("properties", {})
        feature_county = props.get("county") or props.get("adm1_name")
        if value_matches(feature_county, county):
            filtered.append(feature)

    return JsonResponse({"type": "FeatureCollection", "features": filtered})


@csrf_exempt
def schools_api(request):
    data = apply_school_filters(get_school_data(), request)
    limit = parse_int(request.GET.get("limit"), default=len(data), minimum=1, maximum=50000)
    data = data[:limit]

    response_format = request.GET.get("format", "json").lower()
    if response_format == "geojson":
        return JsonResponse(
            to_geojson_features(
                data,
                ["name", "UIC", "knec_code", "region", "county", "sub_county", "division", "zone"],
            )
        )

    return JsonResponse({"count": len(data), "results": data})


def climate_api(request):
    data = apply_climate_filters(get_climate_points(), request)
    limit = parse_int(request.GET.get("limit"), default=len(data), minimum=1, maximum=100000)
    data = data[:limit]

    response_format = request.GET.get("format", "json").lower()
    if response_format == "geojson":
        return JsonResponse(to_geojson_features(data, ["rain", "tmin", "tmax"]))

    return JsonResponse({"count": len(data), "results": data})
