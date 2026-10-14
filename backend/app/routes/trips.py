from flask import Blueprint, request, jsonify, current_app
from app.services.trip_service import get_filtered_trips

trips_bp = Blueprint("trips", __name__)


def _parse_float(value: str | None, name: str) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        raise ValueError(f"Parameter '{name}' must be a number. Got: '{value}'")


def _parse_int(value: str | None, name: str, default: int) -> int:
    if value is None:
        return default
    try:
        result = int(value)
        if result < 1:
            raise ValueError()
        return result
    except ValueError:
        raise ValueError(f"Parameter '{name}' must be a positive integer. Got: '{value}'")


@trips_bp.route("/trips", methods=["GET"])
def list_trips():
    try:
        start_date   = request.args.get("start_date")
        end_date     = request.args.get("end_date")
        pickup_zone  = request.args.get("pickup_zone")
        dropoff_zone = request.args.get("dropoff_zone")

        min_fare     = _parse_float(request.args.get("min_fare"),     "min_fare")
        max_fare     = _parse_float(request.args.get("max_fare"),     "max_fare")
        min_distance = _parse_float(request.args.get("min_distance"), "min_distance")

        default_limit = current_app.config["DEFAULT_PAGE_SIZE"]
        max_limit     = current_app.config["MAX_PAGE_SIZE"]
        page          = _parse_int(request.args.get("page"),  "page",  default=1)
        limit         = _parse_int(request.args.get("limit"), "limit", default=default_limit)
        limit         = min(limit, max_limit)

        if min_fare is not None and max_fare is not None and min_fare > max_fare:
            return jsonify({"error": "min_fare cannot be greater than max_fare"}), 400

    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    try:
        result = get_filtered_trips(
            start_date   = start_date,
            end_date     = end_date,
            pickup_zone  = pickup_zone,
            dropoff_zone = dropoff_zone,
            min_fare     = min_fare,
            max_fare     = max_fare,
            min_distance = min_distance,
            page         = page,
            limit        = limit,
        )
        return jsonify(result), 200

    except Exception as e:
        current_app.logger.error(f"[/api/trips] {e}", exc_info=True)
        return jsonify({"error": "An internal server error occurred."}), 500