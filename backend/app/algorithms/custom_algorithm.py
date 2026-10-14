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

        