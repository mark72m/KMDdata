from django.test import TestCase
from django.urls import reverse


class ApiEndpointTests(TestCase):
    def test_api_index_exposes_dataset_summary(self):
        response = self.client.get(reverse("api_index"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("datasets", payload)
        self.assertIn("endpoints", payload)
        self.assertGreater(payload["datasets"]["counties"], 0)
        self.assertGreater(payload["datasets"]["schools"], 0)

    def test_counties_list_returns_expected_count(self):
        response = self.client.get(reverse("counties_api"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["count"], 47)
        self.assertEqual(len(payload["results"]), 47)

    def test_schools_endpoint_supports_filters(self):
        response = self.client.get(
            reverse("schools_api"),
            {"county": "Vihiga", "subcounty": "Emuhaya", "limit": 5},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertGreater(payload["count"], 0)
        self.assertLessEqual(len(payload["results"]), 5)
        self.assertEqual(payload["results"][0]["county"], "Vihiga")
        self.assertEqual(payload["results"][0]["sub_county"], "Emuhaya")

    def test_schools_endpoint_can_return_geojson(self):
        response = self.client.get(reverse("schools_api"), {"county": "Vihiga", "format": "geojson", "limit": 2})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["type"], "FeatureCollection")
        self.assertGreater(len(payload["features"]), 0)
        self.assertEqual(payload["features"][0]["geometry"]["type"], "Point")

    def test_climate_endpoint_returns_points(self):
        response = self.client.get(reverse("climate_api"), {"field": "rain", "limit": 3})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertGreater(payload["count"], 0)
        self.assertEqual(len(payload["results"]), 3)

    def test_subcounties_geojson_filter_by_county(self):
        response = self.client.get(reverse("subcounties_api"), {"county": "Vihiga"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["type"], "FeatureCollection")
        self.assertGreater(len(payload["features"]), 0)
