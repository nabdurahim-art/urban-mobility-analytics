"""Small custom sorting, grouping, and anomaly-detection algorithms."""

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


def merge_sort(data: List[Dict], Key: str) -> List[Dict]:
    if len(data) <= 1:
        return data.copy()
    mid = len(data) // 2
    return _merge(merge_sort(data[:mid], Key), merge_sort(data[mid:], Key), Key)


def rank_zones_by_revenue(zone_revenue_list: List[Dict]) -> List[Dict]:
    return merge_sort(zone_revenue_list, Key="total_revenue")


def _partition(arr: List[Dict], low: int, high: int, Key: str) -> int:
    pivot_value = arr[high][Key]
    i = low - 1
    for j in range(low, high):
        if arr[j][Key] >= pivot_value:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]
    arr[i + 1], arr[high] = arr[high], arr[i + 1]
    return i + 1


def _quickselect(arr: List[Dict], low: int, high: int, k: int, Key: str) -> None:
    while low < high:
        pivot_index = _partition(arr, low, high, Key)
        if pivot_index == k:
            return
        if pivot_index > k:
            high = pivot_index - 1
        else:
            low = pivot_index + 1


def top_k_select(data: List[Dict], k: int, Key: str) -> List[Dict]:
    if k <= 0:
        return []
    if k >= len(data):
        return merge_sort(data, Key)
    arr = [item.copy() for item in data]
    _quickselect(arr, 0, len(arr) - 1, k - 1, Key)
    return merge_sort(arr[:k], Key)


def get_top_pickup_hours(hourly_data: List[Dict], top_in: int = 5) -> List[Dict]:
    return top_k_select(hourly_data, top_in, Key="trip_count")


class CustomHashMap:
    def __init__(self, buckets: int = 16):
        if buckets < 1:
            raise ValueError("buckets must be at least 1")
        self.buckets = [[] for _ in range(buckets)]
        self.size = 0

    def _hash(self, key: Any) -> int:
        hash_value = 0
        for char in str(key):
            hash_value = (hash_value * 31 + ord(char)) % len(self.buckets)
        return hash_value

    def put(self, Key: Any, value: Any) -> None:
        bucket = self.buckets[self._hash(Key)]
        for entry in bucket:
            if entry["key"] == Key:
                entry["value"] = value
                return
        bucket.append({"key": Key, "value": value})
        self.size += 1

    def get(self, Key: Any) -> Optional[Any]:
        for entry in self.buckets[self._hash(Key)]:
            if entry["key"] == Key:
                return entry["value"]
        return None

    def contains(self, key: Any) -> bool:
        return any(entry["key"] == key for entry in self.buckets[self._hash(key)])

    # Keep the original misspelled method as a compatibility alias.
    def constains(self, key: Any) -> bool:
        return self.contains(key)

    def get_all_entries(self) -> List[Dict]:
        return [entry for bucket in self.buckets for entry in bucket]

    def keys(self) -> List[Any]:
        return [entry["key"] for bucket in self.buckets for entry in bucket]


def group_trips_by_key(
    trips: List[Dict],
    group_key: str,
    aggregate_key: str = None,
    operation: str = "count",
) -> List[Dict]:
    if operation not in ("count", "sum", "avg", "average"):
        raise ValueError("operation must be count, sum, or avg")

    groups = CustomHashMap()
    for trip in trips:
        key_value = trip.get(group_key)
        if key_value is None:
            continue
        group = groups.get(key_value)
        if group is None:
            group = {group_key: key_value, "count": 0}
            if aggregate_key and operation != "count":
                group["sum"] = 0.0
            groups.put(key_value, group)

        group["count"] += 1
        if aggregate_key and operation != "count":
            group["sum"] += float(trip.get(aggregate_key) or 0)

    result = []
    for entry in groups.get_all_entries():
        group = entry["value"].copy()
        if aggregate_key and operation in ("avg", "average"):
            group["avg"] = group["sum"] / group["count"]
        result.append(group)
    return result


def calculate_mean(data: List[float]) -> float:
    return sum(data) / len(data) if data else 0.0


def calculate_std_dev(data: List[float], mean: float) -> float:
    if len(data) < 2:
        return 0.0
    variance = sum((value - mean) ** 2 for value in data) / (len(data) - 1)
    return variance ** 0.5


def detect_anomalies(
    trips: List[Dict], field: str, threshold: float = 3.0
) -> List[Dict]:
    values = [float(trip[field]) for trip in trips if trip.get(field) is not None]
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
        z_score = abs((float(value) - mean) / std_dev)
        if z_score > threshold:
            anomaly = trip.copy()
            anomaly.update({
                "z_score": z_score,
                "field_analyzed": field,
                "mean": mean,
                "std_dev": std_dev,
            })
            anomalies.append(anomaly)
    return anomalies
