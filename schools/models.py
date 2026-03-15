from django.contrib.gis.db import models


class School(models.Model):
    institution_name = models.CharField(max_length=255)
    UIC = models.CharField(max_length=50, null=True, blank=True)
    knec_code = models.CharField(max_length=50, null=True, blank=True)
    region = models.CharField(max_length=100, null=True, blank=True)
    county = models.CharField(max_length=100)
    sub_county = models.CharField(max_length=100, null=True, blank=True)
    division = models.CharField(max_length=100, null=True, blank=True)
    zone = models.CharField(max_length=100, null=True, blank=True)
    location = models.PointField()

    def __str__(self):
        return self.institution_name


class ClimateRecord(models.Model):
    location = models.PointField()
    rain = models.FloatField(null=True, blank=True)
    tmin = models.FloatField(null=True, blank=True)
    tmax = models.FloatField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["location"], name="location_idx", db_tablespace="gist"),
        ]


class SubCounty(models.Model):
    name = models.CharField(max_length=100)
    county_name = models.CharField(max_length=100)
    geom = models.MultiPolygonField(srid=4326)

    def __str__(self):
        return f"{self.name} ({self.county_name})"
