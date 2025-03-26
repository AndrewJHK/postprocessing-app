import numpy as np
from collections import deque
import pywt


class FilterStrategy:
    def apply(self, series, **kwargs):
        raise NotImplementedError("Each filter must implement the apply method.")


class RemoveNegativesFilter(FilterStrategy):
    def apply(self, series, **kwargs):
        return series.where(series >= 0, 0)


class RemovePositivesFilter(FilterStrategy):
    def apply(self, series, **kwargs):
        return series.where(series <= 0, 0)


class RollingMeanFilter(FilterStrategy):
    def apply(self, series, window_size=3, **kwargs):
        return series.rolling(window=window_size, min_periods=1).mean()


class RollingMedianFilter(FilterStrategy):
    def apply(self, series, window_size=3, **kwargs):
        return series.rolling(window=window_size, min_periods=1).median()


class ThresholdFilter(FilterStrategy):
    def apply(self, series, threshold=100, **kwargs):
        return series.where(series < threshold, threshold)


class WaveletTransformFilter(FilterStrategy):
    def apply(self, series, wavelet_name='db4', level=2, threshold_mode='soft', **kwargs):
        c = pywt.wavedec(series, wavelet_name, level=level)
        d = c[level] if level < len(c) else c[-1]
        sigma = np.median(np.abs(d)) / 0.6745
        threshold = sigma * np.sqrt(2 * np.log(len(series)))
        c_thresh = [pywt.threshold(ci, threshold, mode=threshold_mode) for ci in c]
        denoised_series = pywt.waverec(c_thresh, wavelet_name)
        return denoised_series[:len(series)]


class DataFilter:
    def __init__(self):
        self.filters = {}
        self.strategy_map = {
            "remove_negatives": RemoveNegativesFilter(),
            "remove_positives": RemovePositivesFilter(),
            "rolling_mean": RollingMeanFilter(),
            "rolling_median": RollingMedianFilter(),
            "threshold": ThresholdFilter(),
            "wavelet_transform": WaveletTransformFilter()
        }

    def get_filter_queue(self):
        return self.filters

    def add_filter(self, columns, filter_name, **kwargs):
        if isinstance(columns, str):
            columns = [columns]
        for column in columns:
            if column not in self.filters:
                self.filters[column] = deque()
            strategy = self.strategy_map.get(filter_name)
            if not strategy:
                raise ValueError(f"Filter '{filter_name}' not recognized.")
            self.filters[column].append((strategy, kwargs))

    def queue_filters(self, df):
        for column, queue in self.filters.items():
            if column in df.columns:
                for strategy, params in queue:
                    df[column] = df[column].map_partitions(lambda s: strategy.apply(s, **params))
        return df
