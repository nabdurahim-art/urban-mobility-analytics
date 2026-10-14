"""HTTP endpoints used by the dashboard."""

from datetime import date, datetime
from decimal import Decimal

from flask import Blueprint, jsonify, request
from psycopg import Error as PsycopgError

from app.algorithms.custom_algorithm import rank_zones_by_revenue
from app.db.connection import get_connection


api = Blueprint("api", __name__, url_prefix="/api")


def _json_value(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _json_rows(rows):
    return [{key: _json_value(value) for key, value in row.items()} for row in rows]


def _query(sql, params=()):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()


def _database_error(error):
    return jsonify({"error": "Database query failed", "detail": str(error)}), 503


@api.get("/analytics/hourly-demand")
def hourly_demand():
    try:
        rows = _query(
            "SELECT pickup_hour, COUNT(*) AS trip_count FROM trips "
            "WHERE pickup_hour IS NOT NULL GROUP BY pickup_hour ORDER BY pickup_hour"
        )
        return jsonify({"data": _json_rows(rows)})
    except PsycopgError as error:
        return _database_error(error)


@api.get("/analytics/revenue-by-zone")
def revenue_by_zone():
    try:
        rows = _query(
            "SELECT z.zone_name, b.borough_name, SUM(t.total_amount) AS total_revenue "
            "FROM trips t JOIN taxi_zones z ON z.location_id = t.pickup_location_id "
            "JOIN boroughs b ON b.borough_id = z.borough_id "
            "GROUP BY z.zone_name, b.borough_name ORDER BY total_revenue DESC"
        )
        return jsonify({"data": _json_rows(rows)})
    except PsycopgError as error:
        return _database_error(error)


@api.get("/analytics/average-fare-per-mile")
def average_fare_per_mile():
    try:
        rows = _query(
            "SELECT CASE "
            "WHEN trip_distance < 2 THEN '0–2 mi' "
            "WHEN trip_distance < 5 THEN '2–5 mi' "
            "WHEN trip_distance < 10 THEN '5–10 mi' "
            "ELSE '10+ mi' END AS distance_bucket, "
            "AVG(fare_amount) AS avg_fare, "
            "AVG(fare_per_mile) AS avg_fare_per_mile, COUNT(*) AS trip_count "
            "FROM trips WHERE fare_per_mile IS NOT NULL AND trip_distance > 0 "
            "GROUP BY distance_bucket ORDER BY MIN(trip_distance)"
        )
        return jsonify({"data": _json_rows(rows)})
    except PsycopgError as error:
        return _database_error(error)


@api.get("/analytics/top-revenue-zones")
def top_revenue_zones():
    try:
        limit = min(max(int(request.args.get("n", 10)), 1), 100)
        rows = _query(
            "SELECT z.zone_name, b.borough_name, SUM(t.total_amount) AS total_revenue "
            "FROM trips t JOIN taxi_zones z ON z.location_id = t.pickup_location_id "
            "JOIN boroughs b ON b.borough_id = z.borough_id "
            "GROUP BY z.zone_name, b.borough_name",
        )
        ranked = rank_zones_by_revenue(rows)[:limit]
        return jsonify({"data": _json_rows(ranked)})
    except ValueError:
        return jsonify({"error": "n must be an integer"}), 400
    except PsycopgError as error:
        return _database_error(error)


@api.get("/zones")
def zones():
    try:
        rows = _query(
            "SELECT z.location_id, z.zone_name, b.borough_name "
            "FROM taxi_zones z JOIN boroughs b ON b.borough_id = z.borough_id "
            "ORDER BY b.borough_name, z.zone_name"
        )
        return jsonify({"data": _json_rows(rows)})
    except PsycopgError as error:
        return _database_error(error)


@api.get("/trips")
def trips():
    try:
        page = max(int(request.args.get("page", 1)), 1)
        page_size = min(max(int(request.args.get("limit", 50)), 1), 500)
        conditions = []
        params = []

        for name, operator in (("start_date", ">="), ("end_date", "<=")):
            value = request.args.get(name)
            if value:
                parsed = datetime.fromisoformat(value)
                conditions.append(f"t.pickup_datetime {operator} %s")
                params.append(parsed)
        for name, column, operator in (
            ("min_fare", "t.fare_amount", ">="),
            ("max_fare", "t.fare_amount", "<="),
            ("min_distance", "t.trip_distance", ">="),
        ):
            value = request.args.get(name)
            if value:
                conditions.append(f"{column} {operator} %s")
                params.append(float(value))

        pickup_zone = request.args.get("pickup_zone")
        if pickup_zone:
            conditions.append("b.borough_name = %s")
            params.append(pickup_zone)

        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        joins = (
            " FROM trips t "
            "JOIN taxi_zones pz ON pz.location_id = t.pickup_location_id "
            "JOIN boroughs b ON b.borough_id = pz.borough_id "
            "JOIN taxi_zones dz ON dz.location_id = t.dropoff_location_id"
        )
        count_rows = _query("SELECT COUNT(*) AS total_count" + joins + where, params)
        total_count = count_rows[0]["total_count"]
        data = _query(
            "SELECT t.trip_id, t.pickup_datetime, pz.zone_name AS pickup_zone, "
            "dz.zone_name AS dropoff_zone, b.borough_name AS pickup_borough, "
            "t.trip_distance, t.fare_amount, t.total_amount, "
            "t.trip_duration_minutes, t.avg_speed_mph, t.passenger_count"
            + joins + where
            + " ORDER BY t.pickup_datetime DESC LIMIT %s OFFSET %s",
            params + [page_size, (page - 1) * page_size],
        )
        return jsonify({
            "data": _json_rows(data),
            "page": page,
            "limit": page_size,
            "total_count": total_count,
            "total_pages": max((total_count + page_size - 1) // page_size, 1),
        })
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid pagination, date, or numeric filter"}), 400
    except PsycopgError as error:
        return _database_error(error)
