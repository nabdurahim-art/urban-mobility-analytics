# NYC Taxi Mobility Explorer

A full-stack analytics app for the NYC TLC Yellow Taxi dataset. A Python ETL pipeline cleans the raw data and loads it into a normalized SQLite database, a Flask REST API serves it, and a browser dashboard (HTML, CSS, JavaScript, Leaflet, Chart.js) lets you explore urban mobility patterns.

## Links

| Item | Link |
|---|---|
| Video walkthrough (5 min) | [FILL: link] |
| Team participation sheet | [FILL: link] |
| Technical report (PDF) | `docs/technical_report.pdf` |
| GitHub repository | [FILL: link] |

## Team: Urban Mobility Team

| Member | Area | Main files |
|---|---|---|
| Batsinda Keynes Benoit | Data cleaning / ETL | `backend/etl.py`, `backend/config.py` |
| Batsinde Ange Liana | Database | `backend/schema.sql`, `backend/indexes.sql`, `backend/export_dump.py` |
| Nshmiyimana Abdurahim | API and custom algorithm | `backend/app.py`, `backend/algorithms.py`, `backend/test_algorithms.py` |
| Mucyo Joel | Frontend | `frontend/index.html`, `frontend/style.css`, `frontend/app.js` |

## Table of contents

1. [Prerequisites](#prerequisites)
2. [Installation and setup](#installation-and-setup)
3. [Verify it works](#verify-it-works)
4. [Project structure](#project-structure)
5. [Data pipeline](#data-pipeline)
6. [Database design](#database-design)
7. [Custom algorithm](#custom-algorithm-top-k-busiest-zones-and-routes)
8. [API reference](#api-reference)
9. [Dashboard](#dashboard)
10. [Known limitations](#known-limitations)
11. [Configuration](#configuration)
12. [Troubleshooting](#troubleshooting)

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- A modern web browser (Chrome, Firefox, Edge or Safari) with internet access, because the dashboard loads Leaflet, Chart.js, map tiles and fonts from CDNs
- Roughly 4 GB of free RAM for a full month of trips (use `--limit` for a smaller test run)
- No database server is needed: SQLite ships with Python

## Installation and setup

Run every command from the project root (the folder containing `backend/` and `frontend/`).

### 1. Get the code and install dependencies

```bash
cd nyc-mobility
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Add the three TLC data files to `data/`

| File | Notes |
|---|---|
| `data/yellow_tripdata_<year>-<month>.parquet` | Trip records. Any month works, and several months can be placed together. |
| `data/taxi_zone_lookup.csv` | Zone ID to borough and service zone. |
| `data/taxi_zones.geojson` | Zone polygons, with a `LocationID` property. |

The raw data files are git-ignored, so each person downloads them from the TLC. If you only have the TLC shapefile, convert it once with `ogr2ogr -f GeoJSON data/taxi_zones.geojson taxi_zones.shp` (or QGIS: Export, Save Features As, GeoJSON). A GeoJSON in the original EPSG:2263 projection is detected and reprojected to WGS84 automatically.

### 3. Run the ETL pipeline and build the database

```bash
python backend/etl.py
```

This cleans the data, creates the engineered features, writes the exclusion log and builds `data/mobility.db`. It can take several minutes for millions of rows. For a quick test run on a subset:

```bash
python backend/etl.py --limit 500000
```

### 4. Start the backend and the dashboard

```bash
python backend/app.py
```

Open **http://localhost:5000** in your browser. Flask serves both the API and the dashboard, so there is nothing else to launch.

> **Do not open `frontend/index.html` by double-clicking it.** The page calls `/api/...` on its own address, so from a `file://` address it cannot reach the backend. If you want to serve the frontend from another static server (for example VS Code Live Server), open it with `?api=http://localhost:5000` added to the address.

## Verify it works

In a second terminal, with the server running:

```bash
python backend/test_algorithms.py                        # prints: all algorithm tests passed
curl http://localhost:5000/api/meta                      # date range, trip count, boroughs
curl "http://localhost:5000/api/top?kind=zone&k=5"       # top 5 pickup zones from the custom algorithm
```

Then open the dashboard: the KPI strip, map and charts should fill within a few seconds. On a full month the Top-K panel is slower than the others (see [Known limitations](#known-limitations)).

## Project structure

```
nyc-mobility/
├── backend/
│   ├── app.py               # Flask REST API and static file server
│   ├── algorithms.py        # Hand-written HashCounter, MinHeap and top_k
│   ├── config.py            # Paths and cleaning thresholds (environment-overridable)
│   ├── etl.py               # Ingest, clean, normalise, engineer features, load database
│   ├── export_dump.py       # Exports the database dump for submission
│   ├── schema.sql           # Normalized relational schema
│   ├── indexes.sql          # Indexes, created after the bulk load
│   └── test_algorithms.py   # Checks the algorithms against Python built-ins
├── frontend/
│   ├── index.html           # Dashboard layout
│   ├── style.css            # Styling (responsive layout)
│   └── app.js               # API calls, filters, map and chart rendering
├── data/                    # Raw inputs and generated mobility.db (git-ignored)
├── docs/                    # build_report.py, VIDEO_SCRIPT.md, TEAM_SHEET_CONTENT.md, figures
├── logs/                    # excluded_records.csv (generated by the ETL)
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

## Data pipeline

1. **Integration.** Trips are joined to `taxi_zone_lookup.csv` (borough, zone, service zone) and to the `taxi_zones` polygons through `LocationID`. Lookup tables are created for vendor, rate code and payment type.
2. **Cleaning.** Each row is tagged with the first rule it breaks, so every exclusion has exactly one reason:

| Reason | Rule |
|---|---|
| `missing_critical` | Null timestamp, zone, distance, fare or total |
| `duplicate` | Same vendor, timestamps, zones, distance and fare as an earlier row |
| `unknown_zone` | Zone not in the lookup, or Unknown / Outside NYC (264, 265) |
| `bad_timestamp` | Dropoff not after pickup |
| `out_of_period` | Pickup outside the month(s) holding at least 5% of the rows |
| `duration_too_long` / `duration_too_short` | Over 6 hours / under 30 seconds |
| `bad_distance` | 0 or less, or over 100 miles |
| `bad_fare` | Fare 0 or less or over $500, or total 0 or less |
| `negative_charge` | Negative tip, tolls, extra or MTA tax |
| `bad_passengers` | 0 or more than 6 passengers (nulls are kept as NULL, not imputed) |
| `speed_outlier` | Average speed over 80 mph |

3. **Normalisation.** Timestamps become `YYYY-MM-DD HH:MM:SS`, money is rounded to cents, and unknown vendor, rate and payment codes map to explicit "Unknown" rows in their lookup tables.
4. **Transparency log.** Every excluded row is written to `logs/excluded_records.csv`. Per-reason counts are stored in the `cleaning_summary` table, a sample of rows in `excluded_records`, and the counts are shown in the dashboard sidebar.

### Engineered features

| Feature | Formula | Why it matters |
|---|---|---|
| `speed_mph` | distance ÷ duration | Congestion proxy by hour and zone, and the best outlier detector |
| `fare_per_mile` | fare_amount ÷ distance | Pricing efficiency; exposes short-trip minimums and airport flat fares |
| `tip_pct` | tip ÷ fare × 100, card payments only | Generosity by place and time. Cash tips are never recorded, so cash is NULL, not 0 |
| `pickup_hour`, `pickup_dow`, `is_weekend`, `time_bucket` | From the pickup timestamp | Temporal context for rush-hour and weekend analysis |

## Database design

The lookup data is normalized: `borough`, `service_zone`, `zone` (with GeoJSON geometry), `vendor`, `rate_code` and `payment_type` are dimension tables, and `trip` is the fact table with foreign keys to all of them. `cleaning_summary` and `excluded_records` hold the transparency log.

**Indexes:** `pickup_ts`, `(pickup_date, pickup_hour)`, `(pu_zone_id, pickup_date)`, `do_zone_id`, `trip_distance`, `fare_amount`, `(pickup_dow, pickup_hour)` and `zone(borough_id)`. They are built after the bulk insert, which is much faster than indexing while loading.

**Database dump for submission:**

```bash
python backend/export_dump.py            # schema, lookup tables and 1,000 sample trips -> docs/mobility_dump.sql
python backend/export_dump.py --full     # every row (can be several GB for a full month)
```

The schema alone is in `backend/schema.sql`.

## Custom algorithm: Top-K busiest zones and routes

`backend/algorithms.py` implements the following without `heapq`, `Counter`, `sorted` or pandas:

- **HashCounter:** a separate-chaining hash table with multiplicative hashing that resizes at a load factor of 0.75.
- **MinHeap:** an array-based binary heap with manual `sift_up` and `sift_down`.
- **top_k:** keeps a size-K min-heap, where a key replaces the root only if it beats the current K-th best. The K survivors are popped and manually reversed into descending order.

```
counter ← empty hash table
for each (pickup, dropoff) row streamed from the database:
    counter.increment(key)                   # key = zone id, or pickup*1000 + dropoff
heap ← empty min-heap
for each (key, count) in counter:
    if size(heap) < K:                       push (count, key)
    else if (count, key) beats root(heap):   replace root, sift down
pop heap into an array (ascending), read it backwards → top K
```

**Complexity** (n = rows scanned, m = distinct keys, K = result size): time O(n + m log K), space O(m + K).

SQL `GROUP BY ... ORDER BY` would be faster. We used the manual version because the assignment requires one, and the endpoint reports `rows_scanned` and `elapsed_ms` so the cost can be discussed. Run `python backend/test_algorithms.py` to verify correctness.

## API reference

All endpoints accept the same filters: `date_from`, `date_to`, `hour_from`, `hour_to`, `day_type` (`weekday` or `weekend`), `borough`, `pu_zone`, `payment_type`, `min_distance`, `max_distance`, `min_fare`, `max_fare`.

| Endpoint | Returns |
|---|---|
| `GET /api/meta` | Date range, trip count, boroughs |
| `GET /api/summary` | Trips, average fare, distance, duration, speed and tip %, revenue |
| `GET /api/hourly` | Trips, speed and fare per hour of day |
| `GET /api/heatmap` | Trips by day of week and hour |
| `GET /api/zones` | Per-zone pickups, dropoffs, average fare and speed |
| `GET /api/geojson` | Zone polygons |
| `GET /api/tips` | Average tip % by borough and time bucket |
| `GET /api/top?kind=zone\|route&k=10` | Top-K via the custom algorithm |
| `GET /api/trips?sort=&order=&page=&page_size=` | Paginated, sortable trip rows |
| `GET /api/cleaning` | Exclusion counts per rule |

All SQL is parameterised and sort columns are whitelisted.

## Dashboard

The filters (date, hour, weekday or weekend, borough, distance, fare) drive every panel:

- KPI strip
- Zone choropleth map, switchable between pickups, dropoffs, average fare and average speed
- Hourly demand against speed
- Tipping by time of day and borough
- Weekly demand heatmap
- Top-K zones or routes (custom algorithm)
- Sortable, paginated trip explorer

Clicking a zone on the map filters everything to pickups from that zone.

## Known limitations

- **Top-K speed.** `/api/top` streams every matching trip through the Python hash table, so on a full month it is slower than a SQL `GROUP BY`. This is a deliberate trade-off.
- **Stored derived columns.** `pickup_date`, `pickup_hour`, `time_bucket`, `is_weekend`, speed and fare per mile are stored in `trip` for faster filtering. This is deliberate denormalisation; the lookup data is fully normalized.
- **`time_bucket` ignores weekends.** A Sunday 8 am is labelled `morning_rush`. `is_weekend` is stored separately for filtering.
- **Cash tips are not recorded** by the TLC, so `tip_pct` is only computed for credit-card trips.
- The dashboard needs internet access for Leaflet, Chart.js, map tiles and fonts.
- SQLite is used for zero-setup reproducibility. A production version would use PostgreSQL with PostGIS.

## Configuration

Optional environment variables: `DATA_DIR`, `LOG_DIR`, `DB_PATH`, `PORT`. Cleaning thresholds are in `backend/config.py`.

## Troubleshooting

| Problem | Fix |
|---|---|
| "Database not found" | Run `python backend/etl.py` first. |
| `Missing .../taxi_zone_lookup.csv` or "No yellow_tripdata*.parquet" | Put the three data files in `data/` (see step 2). |
| Empty map | `data/taxi_zones*.geojson` was missing when the ETL ran. Add it and re-run the ETL. |
| Dashboard shows "Couldn't load data" | Open it at http://localhost:5000, not as a file, and make sure the backend is running. |
| Out of memory in the ETL | Use `--limit 1000000`, or run on a machine with more RAM. |
| Blank charts or map | The dashboard loads libraries and tiles from CDNs, so check your internet connection. |
| `ModuleNotFoundError` | Activate the virtual environment and run `pip install -r requirements.txt`. |

## AI usage statement

[FILL: one honest paragraph written by the team: which tools were used, for which tasks, and which parts of the code are your own work. Keep it consistent with your CodeVibe report.]
