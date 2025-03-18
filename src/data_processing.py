import dask.dataframe as dd


class DataProcessor:
    def __init__(self, csv_paths):
        self.csv_paths = csv_paths if isinstance(csv_paths, list) else [csv_paths]
        self.dataframes = self.load_data()

    def load_data(self):
        dataframes = {}
        for path in self.csv_paths:
            dataframes["path"] = dd.read_csv(path)
        return dataframes

    def get_loaded_dataframes(self):
        return self.dataframes

    def adjust_data(self, dataframes, action):
        # something like this
        for name, df in dataframes:
            df = eval(action)
            self.dataframes[name] = df
            pass

    def filter_data(self, dataframe, filter_type, filter_presets):
        # logic behind data filtration
        pass
