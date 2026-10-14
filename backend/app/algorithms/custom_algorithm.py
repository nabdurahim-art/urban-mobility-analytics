"""Small custom sorting, grouping, and anomaly-detection algorithms."""

from math import sqrt
from typing import Any, Dict, List, Optional


def _merge(left: List[Dict], right: List[Dict], key: str) -> List[Dict]:
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i][key] >= right[j][key]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result


def merge_sort(data: List[Dict], key: Optional[str] = None, **kwargs) -> List[Dict]:
    """Sort dictionaries descending by key (accepts legacy ``Key=`` too)."""
    key = key or kwargs.pop("Key", None)
    if key is None:
        raise TypeError("merge_sort() requires a key")
    if len(data) <= 1:
        return data.copy()
    mid = len(data) // 2
    return _merge(merge_sort(data[:mid], key), merge_sort(data[mid:], key), key)


def rank_zones_by_revenue(zone_revenue_list: List[Dict]) -> List[Dict]:
    return merge_sort(zone_revenue_list, "total_revenue")


def _partition(arr: List[Dict], low: int, high: int, key: str) -> int:
    pivot_value = arr[high][key]
    i = low - 1
    for j in range(low, high):
        if arr[j][key] >= pivot_value:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]
    arr[i + 1], arr[high] = arr[high], arr[i + 1]
    return i + 1


def _quickselect(arr: List[Dict], low: int, high: int, k: int, key: str) -> None:
    while low < high:
        pivot_index = _partition(arr, low, high, key)
        if pivot_index == k:
            return
        if pivot_index > k:
            high = pivot_index - 1
        else:
            low = pivot_index + 1


def top_k_select(data: List[Dict], k: int, key: Optional[str] = None, **kwargs) -> List[Dict]:
    key = key or kwargs.pop("Key", None)
    if key is None:
        raise TypeError("top_k_select() requires a key")
    if k <= 0:
        return []
    if k >= len(data):
        return merge_sort(data, key)
    selected = [item.copy() for item in data]
    _quickselect(selected, 0, len(selected) - 1, k - 1, key)
    return merge_sort(selected[:k], key)


def top_k_selection(data: List[Dict], k: int, key: str) -> List[Dict]:
    return top_k_select(data, k, key)


def get_top_pickup_hours(hourly_data: List[Dict], top_n: int = 5) -> List[Dict]:
    return top_k_select(hourly_data, top_n, "trip_count")


class CustomHashMap:
    def __init__(self, buckets: int = 16):
        if buckets < 1:
            raise ValueError("buckets must be at least 1")
        self.buckets = [[] for _ in range(buckets)]
        self.size = 0

    def _hash(self, key: Any) -> int:
        value = 0
        for char in str(key):
            value = (value * 31 + ord(char)) % len(self.buckets)
        return value

    def put(self, key: Any, value: Any) -> None:
        bucket = self.buckets[self._hash(key)]
        for entry in bucket:
            if entry["key"] == key:
                entry["value"] = value
                return
        bucket.append({"key": key, "value": value})
        self.size += 1

    def get(self, key: Any) -> Optional[Any]:
        for entry in self.buckets[self._hash(key)]:
            if entry["key"] == key:
                return entry["value"]
        return None

    def contains(self, key: Any) -> bool:
        return any(entry["key"] == key for entry in self.buckets[self._hash(key)])

    def constains(self, key: Any) -> bool:
        """Compatibility alias for the original misspelled method."""
        return self.contains(key)

    def get_all_entries(self) -> List[Dict]:
        return [entry for bucket in self.buckets for entry in bucket]

    def keys(self) -> List[Any]:
        return [entry["key"] for bucket in self.buckets for entry in bucket]


def group_trips_by_key(
    trips: List[Dict], group_key: str, aggregate_key: Optional[str] = None,
    operation: str = "count",
) -> List[Dict]:
    if operation not in ("count", "sum", "avg", "average"):
        raise ValueError("operation must be count, sum, or avg")
    groups = CustomHashMap()
    for trip in trips:
        value = trip.get(group_key)
        group = groups.get(value)
        if group is None:
            group = {group_key: value, "count": 0, "sum": 0.0}
            groups.put(value, group)
        group["count"] += 1
        if aggregate_key is not None and trip.get(aggregate_key) is not None:
            group["sum"] += float(trip[aggregate_key])
    result = groups.get_all_entries()
    for entry in result:
        group = entry["value"]
        if operation == "count":
            group["trip_count"] = group["count"]
        elif operation == "sum":
            group[aggregate_key or "sum"] = group["sum"]
            if aggregate_key and aggregate_key != "sum":
                group.pop("sum", None)
        else:
            group["avg"] = group["sum"] / group["count"] if group["count"] else 0.0
        group.pop("count", None)
        if operation != "sum":
            group.pop("sum", None)
    return [entry["value"] for entry in result]


def calculate_mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def calculate_std_dev(values: List[float], mean: Optional[float] = None) -> float:
    if len(values) < 2:
        return 0.0
    mean = calculate_mean(values) if mean is None else mean
    return sqrt(sum((value - mean) ** 2 for value in values) / (len(values) - 1))


def detect_anomalies(trips: List[Dict], field: str, threshold: float = 3.0) -> List[Dict]:
    values = [float(t[field]) for t in trips if t.get(field) is not None]
    if len(values) < 2:
        return []
    mean = calculate_mean(values)
    std_dev = calculate_std_dev(values, mean)
    if std_dev == 0:
        return []
    anomalies = []
    for trip in trips:
        value = trip.get(field)
        if value is None:
            continue
        z_score = (float(value) - mean) / std_dev
        if abs(z_score) >= threshold:
            anomaly = trip.copy()
            anomaly["z_score"] = z_score
            anomaly["anomaly_field"] = field
            anomalies.append(anomaly)
    return anomalies


def detect_multiple_anomalies(
    trips: List[Dict], fields: List[str], threshold: float = 3.0,
) -> List[Dict]:
    """Return trips that are anomalous in one or more requested fields."""
    by_trip = {}
    for field in fields:
        for anomaly in detect_anomalies(trips, field, threshold):
            identity = anomaly.get("trip_id")
            if identity is None:
                identity = tuple(sorted((key, repr(value)) for key, value in anomaly.items()
                                        if key not in ("z_score", "anomaly_field")))
            result = by_trip.setdefault(identity, anomaly.copy())
            result.setdefault("anomalous_fields", []).append(field)
    return list(by_trip.values())
