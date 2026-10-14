from app.db.connection import get_connection


def get_filtered_trips(
    start_date:   str | None,
    end_date:     str | None,
    pickup_zone:  str | None,
    dropoff_zone: str | None,
    min_fare:     float | None,
    max_fare:     float | None,
    min_distance: float | None,
    page:         int,
    limit:        int,
) -> dict:

    conditions: list[str] = []
    params:     list      = []

    if start_date:
        conditions.append("t.pickup_datetime >= %s")
        params.append(start_date)

    if end_date:
        conditions.append("t.pickup_datetime <= %s")
        params.append(end_date)

    if pickup_zone:
        conditions.append("pu_zone.zone_name LIKE %s")
        params.append(f"%{pickup_zone}%")

    if dropoff_zone:
        conditions.append("do_zone.zone_name LIKE %s")
        params.append(f"%{dropoff_zone}%")

    if min_fare is not None:
        conditions.append("t.fare_amount >= %s")
        params.append(min_fare)

    if max_fare is not None:
        conditions.append("t.fare_amount <= %s")
        params.append(max_fare)

    if min_distance is not None:
        conditions.append("t.trip_distance >= %s")
        params.append(min_distance)

    where_sql = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    base_from = f"""
        FROM trips t
        LEFT JOIN taxi_zones pu_zone ON t.pickup_location_id  = pu_zone.location_id
        LEFT JOIN taxi_zones do_zone ON t.dropoff_location_id = do_zone.location_id
        LEFT JOIN boroughs pu_b      ON pu_zone.borough_id    = pu_b.borough_id
        LEFT JOIN boroughs do_b      ON do_zone.borough_id    = do_b.borough_id
        {where_sql}
    """

    count_sql = "SELECT COUNT(*) AS total " + base_from
    offset    = (page - 1) * limit

    data_sql = f"""
        SELECT
            t.trip_id,
            t.pickup_datetime,
            t.dropoff_datetime,
            t.trip_distance,
            t.fare_amount,
            t.total_amount,
            t.tip_amount,
            t.passenger_count,
            t.fare_per_mile,
            t.trip_duration_minutes,
            t.avg_speed_mph,
            t.pickup_hour,
            t.is_weekend,
            pu_zone.zone_name AS pickup_zone,
            do_zone.zone_name AS dropoff_zone,
            pu_b.borough_name AS pickup_borough,
            do_b.borough_name AS dropoff_borough
        {base_from}
        ORDER BY t.pickup_datetime DESC
        LIMIT %s OFFSET %s
    """

    conn = get_connection()
    try:
        count_cur = conn.cursor()
        count_cur.execute(count_sql, params)
        total_count = count_cur.fetchone()["total"]
        count_cur.close()

        data_cur = conn.cursor()
        data_cur.execute(data_sql, params + [limit, offset])
        rows = data_cur.fetchall()
        data_cur.close()
    finally:
        conn.close()

    total_pages = max(1, -(-total_count // limit))

    data = []
    for row in rows:
        row = dict(row)
        if row.get("pickup_datetime"):
            row["pickup_datetime"] = row["pickup_datetime"].strftime("%Y-%m-%d %H:%M:%S")
        if row.get("dropoff_datetime"):
            row["dropoff_datetime"] = row["dropoff_datetime"].strftime("%Y-%m-%d %H:%M:%S")
        for field in ("trip_distance", "fare_amount", "total_amount", "tip_amount",
                      "fare_per_mile", "trip_duration_minutes", "avg_speed_mph"):
            if row.get(field) is not None:
                row[field] = float(row[field])
        data.append(row)

    return {
        "data":        data,
        "page":        page,
        "limit":       limit,
        "total_count": total_count,
        "total_pages": total_pages,
    }