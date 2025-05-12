import dask.dataframe as dd
from src.filters import DataFilter

EQUATIONS = {"biliq": "placeholder", "broom_stick": "placeholder"}


def sync_with_wrapper(method):
    def wrapper(self, *args, **kwargs):
        result = method(self, *args, **kwargs)
        self.df_wrapper.update_dataframe(self.df)
        return result

    return wrapper


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
        self.filter_manager = DataFilter()  # Handles filter strategies

    def get_filters(self):
        return self.filter_manager.get_filter_queue()

    def add_filter(self, columns, filter_name, **kwargs):
        """Adds a predefined filter with parameters to be applied later."""
        self.filter_manager.add_filter(columns, filter_name, **kwargs)

    @sync_with_wrapper
    def queue_filters(self):
        """Applies all filters to the DataFrame."""
        self.df = self.filter_manager.queue_filters(self.df)

    @sync_with_wrapper
    def normalize_columns(self, columns):
        """Applies min-max normalization to multiple columns."""
        if isinstance(columns, str):
            columns = [columns]

        for column in columns:
            min_val = self.df[column].min().compute()
            max_val = self.df[column].max().compute()
            self.df[column] = (self.df[column] - min_val) / (max_val - min_val)

    @sync_with_wrapper
    def scale_columns(self, columns, factor):
        """
        Multiplies multiple columns by a given factor.
        """
        if isinstance(columns, str):
            columns = [columns]

        for column in columns:
            self.df[column] = self.df[column] * factor

    @sync_with_wrapper
    def sort_data(self, key, ascending=True):
        """Sorts the dataframe by a specific column."""
        self.df = self.df.sort_values(by=key, ascending=ascending)

    @sync_with_wrapper
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
            self.df = self.df.loc[(self.df.index < start) | (self.df.index > end)]

        if row_condition:
            self.df = self.df[~self.df.map_partitions(lambda df: df.apply(row_condition, axis=1))]

        self.df = self.df.persist()

    @sync_with_wrapper
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

    @sync_with_wrapper
    def flip_column_sign(self, columns):
        """
        Flips the sign of all values in the specified column(s).
        Positive values become negative and vice versa.
        """
        if isinstance(columns, str):
            columns = [columns]

        for column in columns:
            self.df[column] = -self.df[column]

        self.df_wrapper.update_dataframe(self.df)

    def get_processed_data(self):
        """Returns the processed DataFrame."""
        return self.df

    def save_data(self, path):
        """Save the processed DataFrame."""
        dd.to_csv(self.df, path, single_file=True)
