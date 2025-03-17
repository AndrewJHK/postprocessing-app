import matplotlib.pyplot as plot
import dask.dataframe as dd


class Plotter:
    def __init__(self, csv_path, source, plots_folder_path, plot_type="line", axis_labels=None, plot_channels=None,
                 channel_labels=None, horizontal_lines=None, vertical_lines=None):
        self.csv_path = csv_path
        self.source = source
        self.plots_folder_path = plots_folder_path
        self.plot_type = plot_type
        self.axis_labels = axis_labels or {"x": "X-Axis", "y1": "Y1-Axis", "y2": "Y2-Axis"}
        self.plot_channels = plot_channels or {}
        self.channel_labels = channel_labels or {}
        self.horizontal_lines = horizontal_lines or []  # List of tuples (value, label)
        self.vertical_lines = vertical_lines or []  # List of tuples (value, label)
        self.df = self.load_data()

    def load_data(self):
        """
        Load data from csv
        """
        return dd.read_csv(self.csv_path)

    def plot(self):
        """
        Main  plotting method
        """
        fig, ax1 = plot.subplots()
        ax2 = None

        if isinstance(self.plot_channels, dict) and "y2" in self.plot_channels.values():
            ax2 = ax1.twinx()

        for channel, axis in self.plot_channels.items():
            df_column = self.df[channel].compute()
            x_values = self.df.index.compute()
            label = self.channel_labels.get(channel, channel)  # Look for a custom label

            if axis == "y1":
                ax1.plot(x_values, df_column, label=label)
            elif ax2 is not None and axis == "y2":
                ax2.plot(x_values, df_column, label=label, linestyle='dashed')

        # Setting up the axis labels
        ax1.set_xlabel(self.axis_labels.get("x", "X-Axis"))
        ax1.set_ylabel(self.axis_labels.get("y1", "Y1-Axis"))
        if ax2:
            ax2.set_ylabel(self.axis_labels.get("y2", "Y2-Axis"))

        # Set up the horizontal lines
        for y_value, label in self.horizontal_lines:
            ax1.axhline(y=y_value, color='r', linestyle='--', label=label)

        # Set up the vertical lines
        for x_value, label in self.vertical_lines:
            ax1.axvline(x=x_value, color='b', linestyle='--', label=label)

        # Construct legend
        ax1.legend(loc='upper left')
        if ax2:
            ax2.legend(loc='upper right')

        plot.show()

    def save_plot(self, filename):
        """
        Save plot to file
        """
        path = f"{self.plots_folder_path}/{filename}.png"
        plot.savefig(path)
