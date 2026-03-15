# Climate Update Workflow

Use this workflow whenever you receive a new climate CSV from KMD or from your backup source.

## Main Rule

- If KMD sends the file, use source name: `KMD`
- If KMD does not send the file and you use the backup provider, use source name: `ERA5-Land`

## Step 1: Put the CSV in the Project

Place the new CSV in `climate_data/`.

Example:

```text
climate_data/20260310_to_20260317_fcst.csv
```

## Step 2: Update the Map Climate File

Run this from the folder that contains `manage.py`.

Example for KMD:

```bash
python scripts/update_climate_from_csv.py climate_data/20260310_to_20260317_fcst.csv schools/static/data/climate_all.geojson KMD
```

Example for backup data:

```bash
python scripts/update_climate_from_csv.py climate_data/20260310_to_20260317_fcst.csv schools/static/data/climate_all.geojson ERA5-Land
```

This updates:

- `schools/static/data/climate_all.geojson`
- `schools/static/data/climate_metadata.json`

## Step 3: Push the Update

```bash
git add schools/static/data/climate_all.geojson schools/static/data/climate_metadata.json
git commit -m "Update climate data"
git push origin main
```

## Step 4: Verify the Hosted Map

Open:

```text
https://kmddata.onrender.com/map/?v=latest
```

Check:

- climate buttons still work
- the map status bar shows the correct climate source
- the climate layer appears inside Kenya

## What the Map Reads

The hosted map uses:

- `schools/static/data/climate_all.geojson` for climate points
- `schools/static/data/climate_metadata.json` for source labeling

## Important

- Do not call backup data `KMD`
- Always label the true source
- If you update the file but do not push, the hosted map will not change
