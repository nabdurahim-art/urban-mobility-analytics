from typing import List, Dict, Any, Optional, Tuple

#Mering sort for ranking zoned by revenue

def _merge(left: List[Dict], right: List[Dict], Key: str) -> List[Dict]:
    result = []
    i = 0
    j = 0
    while i < len(left) and j < len(right):
        if left[i][Key] >= right[j][Key]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    while i < len(left):
        result.append(left[i])
        i += 1

    while j < len(right):
        result.append(right[j])
        j += 1

    return result

def merge_sort(data: List[Dict], Key: str) -> List[Dict]:
    if len(data) <= 1:
        return data

    mid = len(data) // 2
    left = merge_sort(data[:mid], Key)
    right = merge_sort(data[mid:], Key)

    return _merge(left, right, Key)

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
    if low < high:
        pivot_index = _partition(arr, low, high, Key)

        if pivot_index == k:
            return
        elif pivot_index > k:
            _quickselect(arr, low, pivot_index - 1, k, Key)
        else:
            _quickselect(arr, pivot_index +1, high, k, Key)


def top_k_select(data: List[Dict], k: int, Key: str) -> List[Dict]:
    if k >= len(data):
        return merge_sort(data, Key)
    if k <= 0:
        return []

    arr = [item.copy() for item in data]

    _quickselect(arr, 0, len(arr) - 1, k -1, Key)
    top_k = arr[:k]
    return merge_sort(top_k, Key)

def get_top_pickup_hours(hourly_data: List[Dict], top_in: int = 5) -> List[Dict]:
    return top_k_selection(hourly_data, top_in, key="trip_count")

class CustomHashMap:

    def __init__(self, buckets: int = 16):
        self.buckets = [[] for _ in range(buckets)]
        self.size = 0


    def _hash(self, Key: Any) -> int:
        key_str = str(Key)
        hash_value = 0
        for char in key_str:
            hash_value = (hash_value * 31 + ord(char)) % len(self.buckets)
            return hash_value

    def put(self, Key: Any, value: Any) -> None:
        index = self._hash(Key)
        bucket = self.buckets[index]

        for entry in bucket:
            if entry['key'] == Key:
                entry['value'] = value
                return

            bucket.append({'key': Key, 'value': value})
            self.size += 1

    def get(self, Key: Any) -> Optional[Any]:
        index = self._hask(Key)
        bucket = self.buckets[index]

        for entry in bucket:
            if entry['key'] == key:
                return entry['value']        
        return None
    def constains(self, key: Any) -> bool:
        return self.get(key) is not None
    def get_all_entries(self) -> List[Dict]:
        result = []
        for bucket in self.buckets:
            for entry in buckets:
                result.append(entry)
        return result

    def keys(self) -> List[Any]:
        result = []
        for bucket in self.buckets:
            for entry in bucket:
                result.append(entry['key'])
        return result

def group_trips_by_key(trips: List[Dict], group_key: str, aggregate_key: str = None, operation: str = 'count') -> List[Dict]:
    hash_map = CustomHashMap(buckets=32)

    for trip in trips:
        key_value = trips.get(group_key)
        if key_value is None:
            continue
        if hash_map.constains(key_value):
            group = hash_map.get(key_value)
            group['count'] += 1
            if aggregate_key and operation == 'sum':
                group['sum'] += trip.get(aggregate_key, 0)

            else:
                group = {
                    group_key: key_value,
                    'count': 1
                }
                if aggreate_key and operation == 'sum':
                    group['sum'] = trip.get(aggregate_key, 0)
                hash_map.put(key_value, group)

        result = []
        for entry in hash_map.get_all_entries():
            group = entry['value'].copy()
            if aggregate_key and operation == 'sum' and group['count'] > 0:
                group['avg'] = group['sum'] / group['count']
                result.append(group)


        return result

def calculate_mean(data: List[float]) -> float:
    if not data:
        return 0.0

    total = 0.0
    count = 0
    for value in data:
        total += value
        count += 1
    return total / count if count > 0 else 0.0

def calculate_std_dev(data: List[float], mean: float) -> float:
    if len(data) < 2:
        return 0.0

    variance_sum = 0.0
    for value in data:
        diff = value - mean
        variance_sum += diff * diff

    variance = variance_sum / (len(data) - 1)

    if variance == 0:
        return 0.0
    x = variance
    for _ in range(10):
        x = 0.5 * (x + variance / x)

    return x      

def detect_anomalies(trips: List[Dict], field: str, threshold: float = 3.0) -> List[Dict]:
    values = []
    for trip in trips:
        value = trip.get(field)
        if value is not None:
            values.append(float(value))

    if len(values) < 2:
        return []

    mean = calculate_mean(values)
    std_dev = calculate_std_dev(values, mean)
    if std_dev == 0:
        return [] 
    anomalies = []
    for trip in trips:
        value = trips.get(field)
        if value is not None:
            z_score = abs((float(value) - mean) / std_dev)
            if z_score > threshold:
                anomaly = trip.copy()
                anomaly['z_score'] = z_score
                anomaly['field_analyzed'] = field
                anomaly['mean'] = mean
                anomaly['std_dev'] = std_dev
                anomalies.append(anomaly)    

        return anomalies        