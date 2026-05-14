import math
from typing import Dict, Any

class StreamingStatisticsEngine:
    """
    Computes statistical metrics (mean, variance, max, min) in a single pass 
    using Welford's online algorithm to maintain O(1) memory usage regardless of dataset size.
    """
    def __init__(self):
        self.count = 0
        self._mean = 0.0
        self._m2 = 0.0
        self.min_val = float('inf')
        self.max_val = float('-inf')
        
        # Simple bucketting for histogram estimation (O(1) memory)
        self.buckets = {
            "0-128": 0,
            "129-512": 0,
            "513-1024": 0,
            "1025-4096": 0,
            "4097+": 0
        }

    def update(self, value: float):
        self.count += 1
        delta = value - self._mean
        self._mean += delta / self.count
        delta2 = value - self._mean
        self._m2 += delta * delta2

        if value < self.min_val:
            self.min_val = value
        if value > self.max_val:
            self.max_val = value

        self._update_histogram(value)

    def _update_histogram(self, value: float):
        if value <= 128:
            self.buckets["0-128"] += 1
        elif value <= 512:
            self.buckets["129-512"] += 1
        elif value <= 1024:
            self.buckets["513-1024"] += 1
        elif value <= 4096:
            self.buckets["1025-4096"] += 1
        else:
            self.buckets["4097+"] += 1

    @property
    def mean(self) -> float:
        return self._mean if self.count > 0 else 0.0

    @property
    def variance(self) -> float:
        return self._m2 / self.count if self.count > 1 else 0.0

    @property
    def std_dev(self) -> float:
        return math.sqrt(self.variance)

    def get_report(self) -> Dict[str, Any]:
        return {
            "count": self.count,
            "mean": round(self.mean, 2),
            "std_dev": round(self.std_dev, 2),
            "min": self.min_val if self.count > 0 else 0,
            "max": self.max_val if self.count > 0 else 0,
            "histogram": self.buckets
        }
