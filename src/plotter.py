import matplotlib.pyplot as plot
import dask.dataframe as dd
import os
import matplotlib.ticker as ticker


class DataFrameWrapper:
    def __init__(self, csv_path, plot_columns, x_column="index"):
        self.csv_path = csv_path
        self.plot_columns = plot_columns
        self.x_column = x_column
        self.df = dd.read_csv(csv_path)

    def get_data(self):
        return self.df


class Plotter:
    def __init__(self, dataframes, plot_name, plots_folder_path, plot_type="line", axis_labels=None,
                 channel_labels=None,
                 horizontal_lines=None, vertical_lines=None, line_colors=None):
        self.dataframes = dataframes if isinstance(dataframes, list) else [dataframes]
        self.plot_name = plot_name
        self.plots_folder_path = plots_folder_path
        self.plot_type = plot_type
        self.axis_labels = axis_labels or {"x": "X-Axis", "y1": "Y1-Axis", "y2": "Y2-Axis"}
        self.channel_labels = channel_labels or {}  # Dictionary mapping channel names to the labels
        self.horizontal_lines = horizontal_lines or []  # List of tuples (value, label, color)
        self.vertical_lines = vertical_lines or []  # List of tuples (value, label, color)
        self.line_colors = line_colors or {}  # Dictionary mapping channel names to colors

        os.makedirs(self.plots_folder_path, exist_ok=True)

    def plot(self):
        fig, ax1 = plot.subplots(figsize=(10, 7))
        ax2 = None

        twin_axes = any("y2" in df.plot_columns.values() for df in self.dataframes)
        if twin_axes:
            ax2 = ax1.twinx()

        legend_handles = []

        for df_wrapper in self.dataframes:
            df = df_wrapper.get_data()
            if df_wrapper.x_column in df.columns:
                x_values = df[df_wrapper.x_column].compute()
                x_values = (x_values - x_values.min()) / 1000
            else:
                x_values = df.index.compute()

            for channel, axis in df_wrapper.plot_columns.items():
                if channel in df.columns:
                    df_column = df[channel].compute()
                    label = self.channel_labels.get(f"{df_wrapper.csv_path}_{channel}",
                                                    f"{channel} ({df_wrapper.csv_path})")  # Pobranie etykiety legendy
                    color = self.line_colors.get(channel, None)  # Pobranie koloru, jeśli podano

                    if axis == "y1":
                        if self.plot_type == "line":
                            handle, = ax1.plot(x_values, df_column, label=label, color=color)
                        elif self.plot_type == "scatter":
                            handle, = ax1.plot(x_values, df_column, label=label, color=color)
                    elif ax2 is not None and axis == "y2":
                        if self.plot_type == "line":
                            handle, = ax2.plot(x_values, df_column, label=label, color=color)
                        elif self.plot_type == "scatter":
                            handle, = ax2.plot(x_values, df_column, label=label, color=color)
                    legend_handles.append(handle)

        # Axis labels
        ax1.set_xlabel(self.axis_labels.get("x", "X-Axis"))
        ax1.set_ylabel(self.axis_labels.get("y1", "Y1-Axis"))
        if ax2:
            ax2.set_ylabel(self.axis_labels.get("y2", "Y2-Axis"))

        # Horizontal lines
        for y_value, label, color in self.horizontal_lines:
            handle = ax1.axhline(y=y_value, color=color, linestyle='--', label=label)
            legend_handles.append(handle)

        # Vertical lines
        for x_value, label, color in self.vertical_lines:
            handle = ax1.axvline(x=x_value, color=color, linestyle='--', label=label)
            legend_handles.append(handle)
        # Grid setup
        ax1.xaxis.set_major_locator(ticker.AutoLocator())
        ax1.xaxis.set_minor_locator(ticker.AutoMinorLocator())
        ax1.yaxis.set_major_locator(ticker.AutoLocator())
        ax1.yaxis.set_minor_locator(ticker.AutoMinorLocator())

        ax1.grid(True, which='both', linestyle='--', linewidth=0.5)
        if ax2:
            ax2.xaxis.set_major_locator(ticker.AutoLocator())
            ax2.xaxis.set_minor_locator(ticker.AutoMinorLocator())
            ax2.yaxis.set_major_locator(ticker.AutoLocator())
            ax2.yaxis.set_minor_locator(ticker.AutoMinorLocator())
            ax2.grid(True, which='both', linestyle='-', linewidth=1)

        # Legend setup
        plot.subplots_adjust(bottom=0.2)
        plot.legend(handles=legend_handles, bbox_to_anchor=(0.5, 0.02), loc="lower center",
                    bbox_transform=fig.transFigure, fancybox=True, shadow=True, ncol=3)
        # Put the fig manager on top
        mgr = plot.get_current_fig_manager()
        if hasattr(mgr, 'toolbar'):
            mgr.toolbar.pack(side='top', fill='x')

        plot.title(f"{self.plot_name}")
        self.save_plot("wykres_z_cipska")
        plot.show()

    def save_plot(self, filename):
        path = f"{self.plots_folder_path}/{filename}.png"
        plot.savefig(path)
