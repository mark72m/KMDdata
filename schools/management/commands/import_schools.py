import pandas as pd
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from schools.models import School


class Command(BaseCommand):
    help = "Import schools from Excel into database"

    def handle(self, *args, **kwargs):

        excel_file = "schools.xlsx"

        
        df = pd.read_excel(excel_file)

        print("Excel Columns Found:")
        print(df.columns.tolist())

      
        df = df.rename(columns={
            "Name of the Institution": "institution_name",
            "UIC": "UIC",
            "KNEC Code": "knec_code",
            "Region": "region",
            "County": "county",
            "Sub-County": "sub_county",
            "Division": "division",
            "Zone": "zone",
            "latitude": "latitude",
            "longitude": "longitude"
        })

        imported = 0
        skipped = 0

        for index, row in df.iterrows():

            try:
                lat = row["latitude"]
                lon = row["longitude"]
            except:
                skipped += 1
                continue

            if pd.isna(lat) or pd.isna(lon):
                skipped += 1
                continue

            # Skip duplicates
            if School.objects.filter(UIC=row.get("UIC")).exists():
                skipped += 1
                continue

            school = School.objects.create(
                institution_name=row.get("institution_name", ""),
                UIC=row.get("UIC", ""),
                knec_code=row.get("knec_code", ""),
                region=row.get("region", ""),
                county=row.get("county", ""),
                sub_county=row.get("sub_county", ""),
                division=row.get("division", ""),
                zone=row.get("zone", ""),
                location=Point(lon, lat)
            )

            imported += 1

        self.stdout.write(
            self.style.SUCCESS(
                f" Import complete | Imported: {imported} | Skipped: {skipped}"
            )
        )