# Deployment Guide

## Target Architecture

- Django web service hosted on Render
- Managed Postgres database with PostGIS enabled
- Daily Render cron job for KMD climate sync
- React Native `WebView` loading `https://your-domain.com/map/`

## 1. Push This Project to GitHub

Render deploys from a Git repository. Push this codebase to GitHub first.

## 2. Create a Render Postgres Database

In Render:

1. Create a new PostgreSQL service.
2. Choose a database plan.
3. Copy the internal database URL or external database URL.
4. Make sure PostGIS is enabled on the database.

After the database is ready, connect with `psql` or a database client and run:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
```

## 3. Create the Django Web Service

In Render:

1. Create a new Web Service.
2. Connect your GitHub repo.
3. Choose `Docker` as the runtime.
4. Set the environment variables from `.env.example`.

Minimum required environment variables:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG=false`
- `DJANGO_ALLOWED_HOSTS=your-service.onrender.com,your-domain.com`
- `CSRF_TRUSTED_ORIGINS=https://your-service.onrender.com,https://your-domain.com`
- `CORS_ALLOWED_ORIGINS=https://your-domain.com`
- `DATABASE_URL=...`
- `DATABASE_SSL_REQUIRE=true`
- `DJANGO_TIME_ZONE=Africa/Nairobi`

Health check path:

```text
/api/
```

## 4. Run Migrations

After the first deploy, open the Render shell for the web service and run:

```bash
python manage.py migrate
```

If you want the initial bundled climate file loaded into Postgres:

```bash
python manage.py import_climate --replace
```

## 5. Import Any Base Data You Need

If schools or subcounties need to be imported into PostGIS separately, run the matching import commands after deploy.

## 6. Create the Daily KMD Sync Job

Create a Render Cron Job from the same repository.

Recommended command if KMD provides a public GeoJSON URL:

```bash
python manage.py sync_kmd_weather --url "$KMD_CLIMATE_URL" --replace
```

Recommended command if your workflow uploads a file to the server or mounted storage:

```bash
python manage.py sync_kmd_weather --path /app/data/latest_kmd.geojson --replace
```

Suggested schedule:

```text
0 6 * * *
```

Render schedules are in UTC. Adjust the time to match when KMD releases verified daily data.

## 7. Point React Native WebView to Production

Use your public HTTPS URL in React Native:

```tsx
<WebView source={{ uri: 'https://your-domain.com/map/' }} />
```

## 8. Daily Operating Model

Your production flow should be:

1. KMD publishes or sends the verified daily dataset.
2. Render Cron Job runs `sync_kmd_weather`.
3. The command imports the newest climate points into Postgres.
4. `/map/` and `/api/climate/` read the current database-backed climate records.
5. Your React Native `WebView` shows the newest data automatically.

## 9. Important Production Notes

- Do not use your PC as the host.
- Do not keep secrets in source code.
- Keep `DEBUG=false` in production.
- Always use HTTPS in the mobile app.
- For app store release, your users should only hit the hosted domain.
