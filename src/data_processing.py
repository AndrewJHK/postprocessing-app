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

    def update_dataframe(self, dataframe):
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

    def sort_data(self, key, ascending=True):
        """"Sort the dataframe by a concrete column and in provided direction"""
        self.df = self.df.sort_values(by=key, ascending=ascending)

    def drop_data(self, columns=None, row_range=None, row_condition=None):
        """
        Drops specified columns and/or rows based on range or condition.

        :param columns: List of column names to drop.
        :param row_range: Tuple (start, end) to drop rows within index range.
        :param row_condition: A lambda condition to apply to rows.
        """
        if columns:
            self.df = self.df.drop(columns=columns, axis=1, errors='ignore')

        if row_range:
            start, end = row_range
            self.df = self.df[(self.df.index < start) | (self.df.index > end)]

        if row_condition:
            self.df = self.df[~self.df.map_partitions(lambda df: df.apply(row_condition, axis=1))]

        self.df_wrapper.update_dataframe(self.df)

    def scale_index_by_equation(self, equation_func, start_idx=None, end_idx=None):
        """
        Scales the DataFrame index based on a time-dependent function.

        :param equation_func: a function that accepts index and returns scale factor
        :param start_idx: optional starting index for applying the scale
        :param end_idx: optional ending index for applying the scale
        """

        def apply_func(partition):
            idx = partition.index
            if start_idx is not None:
                partition = partition.loc[(idx >= start_idx)]
            if end_idx is not None:
                partition = partition.loc[(idx <= end_idx)]
            scale_factors = equation_func(idx)
            partition.index = idx * scale_factors
            return partition

        self.df = self.df.map_partitions(apply_func)
        self.df_wrapper.update_dataframe(self.df)

    def find_index_where_max(self, column_to_max, condition_column):
        """
        Finds the index and value in column_to_max where condition_column has its maximum.
        Can be used to determine the exact moment of ignition, so it then can be mapped as the time 0
        :param column_to_max: column to return the value from
        :param condition_column: column to check for maximum value
        :return: (index, value)
        """
        max_row = self.df[self.df[condition_column] == self.df[condition_column].max()]
        result = max_row[[column_to_max]].compute()
        index = result.index[0]
        if column_to_max:
            value = result[column_to_max].iloc[0]
            return index, value
        return index

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
        """
        Function used to add a predefined filter to the filter queue
        :param columns: Columns to filter
        :param filter_name: Type of filter to use
        :param kwargs: Parameters to pass to the specific filter
        :return:
        """
        if isinstance(columns, str):
            columns = [columns]

        for column in columns:
            if column not in self.filters:
                self.filters[column] = deque()
            self.filters[column].append((filter_name, kwargs))

    def queue_filters(self, df):
        """
        Run the queue of filters
        :param df: Dataframe to run the filters on
        :return:
        """
        for column, filter_queue in self.filters.items():
            if column in df.columns:
                for filter_name, params in filter_queue:
                    # This is so fucking cool actually
                    df[column] = df[column].map_partitions(lambda s: self._apply_filter(s, filter_name, **params))
        return df

    def _apply_filter(self, series, filter_name, **kwargs):
        """
        Apply the predetermined filter with parameters on specified data
        :param series: Data to filter
        :param filter_name: Type of filter
        :param kwargs: Parameters to pass to the specific filter
        :return:
        """
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
        """Applies a rolling median filter."""
        return series.rolling(window=window_size, min_periods=1).median()

    @staticmethod
    def threshold_filter(series, threshold=100):
        """Filters out values above a certain threshold."""
        return series.where(series < threshold, threshold)

    @staticmethod
    def wavelet_transform(series, wavelet_name, level, threshold_mode):
        """
        Applies selected wavelet transform
        :param series: Data to filter
        :param wavelet_name: Type of wavelet transform
        :param level: Level of smoothing out the data the higher, the smoother
        :param threshold_mode: Mode of thresholding 'soft' smooths out, 'hard' keeps the details
        :return:
        """
        c = pywt.wavedec(series, wavelet_name, level=level)
        if level < len(c):
            d = c[level]
        else:
            d = c[-1]

        sigma = np.median(np.abs(d)) / 0.6745
        threshold = sigma * np.sqrt(2 * np.log(len(series)))

        c_thresh = [pywt.threshold(ci, threshold, mode=threshold_mode) for ci in c]

        denoised_series = pywt.waverec(c_thresh, wavelet_name)

        denoised_series = denoised_series[:len(series)]

        return denoised_series
