import dask.dataframe as dd
from collections import deque
import pywt
import numpy as np

EQUATIONS = {"biliq": "placeholder", "broom_stick": "placeholder"}


class DataFrameWrapper:
    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.df = dd.read_csv(csv_path)

    def get_dataframe(self):
        return self.df

    def get_csv_path(self):
        return self.csv_path

    def update_dataframe(self,dataframe):
        self.df = dataframe


class DataProcessor:
    def __init__(self, df_wrapper):
        """Initializes processor with a DataFrameWrapper instance."""
        self.df_wrapper = df_wrapper
        self.df = df_wrapper.get_dataframe()
        self.filters = DataFilter()  # Filters are handled separately

    def add_filter(self, columns, filter_name, **kwargs):
        """Adds a predefined filter with parameters to be applied later."""
        self.filters.add_filter(columns, filter_name, **kwargs)

    def queue_filters(self):
        """Applies all filters to the DataFrame."""
        self.df = self.filters.queue_filters(self.df)
        self.df_wrapper.update_dataframe(self.df)

    def normalize_columns(self, columns):
        """Applies min-max normalization to multiple columns."""
        if isinstance(columns, str):
            columns = [columns]

        for column in columns:
            min_val = self.df[column].min().compute()
            max_val = self.df[column].max().compute()
            self.df[column] = (self.df[column] - min_val) / (max_val - min_val)

    def scale_columns(self, columns, factor):
        """
        Multiplies multiple columns by a given factor.
        """
        if isinstance(columns, str):
            columns = [columns]

        for column in columns:
            self.df[column] = self.df[column] * factor

    def scale_columns_by_equation(self, columns, equation_type, params):
        """
        Applies a whole equation to specific columns, with proper params
        """
        match EQUATIONS[equation_type]:
            case "biliq":
                # biliq equation filled with params
                pass
            case "broom_stick":
                # broomstick equation filled with params
                pass
            case _:
                pass

    def sort_data(self, key, ascending=True):

        self.df = self.df.sort_values(by=key, ascending=ascending)

    def get_processed_data(self):
        """Returns the processed DataFrame."""
        return self.df

    def save_data(self, path):
        """Save the processed DataFrame."""
        dd.to_csv(self.df, path)



class DataFilter:
    def __init__(self):
        self.filters = {}
        self.filter_methods = {
            "remove_negatives": self.remove_negatives,
            "remove_positives": self.remove_positives,
            "rolling_mean": self.rolling_mean,
            "rolling_median": self.rolling_median,
            "threshold": self.threshold_filter,
            "wavelet_transform": self.wavelet_transform
        }

    def add_filter(self, columns, filter_name, **kwargs):
        if isinstance(columns, str):
            columns = [columns]

        for column in columns:
            if column not in self.filters:
                self.filters[column] = deque()
            self.filters[column].append((filter_name, kwargs))

    def queue_filters(self, df):
        for column, filter_queue in self.filters.items():
            if column in df.columns:
                for filter_name, params in filter_queue:
                    # This is so fucking cool actually
                    df[column] = df[column].map_partitions(lambda s: self._apply_filter(s, filter_name, **params))
        return df

    def _apply_filter(self, series, filter_name, **kwargs):
        if filter_name in self.filter_methods:
            return self.filter_methods[filter_name](series, **kwargs)
        else:
            raise ValueError(f"Filter '{filter_name}' not found.")

    @staticmethod
    def remove_negatives(series):
        """Removes negative values from a column."""
        return series.where(series >= 0, 0)

    @staticmethod
    def remove_positives(series):
        """Removes negative values from a column."""
        return series.where(series <= 0, 0)

    @staticmethod
    def rolling_mean(series, window_size=3):
        """Applies a rolling mean filter."""
        return series.rolling(window=window_size, min_periods=1).mean()

    @staticmethod
    def rolling_median(series, window_size=3):
        """Applies a rolling mean filter."""
        return series.rolling(window=window_size, min_periods=1).median()

    @staticmethod
    def threshold_filter(series, threshold=100):
        """Filters out values above a certain threshold."""
        return series.where(series < threshold, threshold)

    @staticmethod
    def wavelet_transform(series, wavelet_name, level, threshold_mode):
        # Perform Discrete Wavelet Transform
        c = pywt.wavedec(series, wavelet_name, level=level)
        # Extract detail coefficients at the last level
        if level < len(c):  # Ensure level exists
            d = c[level]
        else:
            d = c[-1]

        # Compute noise threshold using median absolute deviation
        sigma = np.median(np.abs(d)) / 0.6745
        threshold = sigma * np.sqrt(2 * np.log(len(series)))

        # Apply thresholding
        c_thresh = [pywt.threshold(ci, threshold, mode=threshold_mode) for ci in c]

        # Reconstruct the denoised signal
        denoised_series = pywt.waverec(c_thresh, wavelet_name)

        # Ensure the length of the output matches the input (due to padding)
        denoised_series = denoised_series[:len(series)]

        return denoised_series
