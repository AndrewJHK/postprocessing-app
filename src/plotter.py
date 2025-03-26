import matplotlib.pyplot as plot
import os
import matplotlib.ticker as ticker


class Plotter:
    def __init__(self, config_dict, dataframe_map, plots_folder_path):
        self.config = config_dict
        self.dataframes = dataframe_map  # mapping: {"db1": DataFrameWrapper, ...}
        self.plot_name = config_dict["plot_settings"].get("title", "Plot")
        self.plot_type = config_dict["plot_settings"].get("type", "line")
        self.precise_grid = config_dict["plot_settings"].get("precise_grid", False)
        self.convert_epoch = config_dict["plot_settings"].get("convert_epoch", None)
        self.plots_folder_path = plots_folder_path
        self.offset = config_dict["plot_settings"].get("offset", 0)

        self.axis_labels = {
            "x": config_dict["plot_settings"].get("x_axis_label", "X-Axis"),
            "y1": config_dict["plot_settings"].get("y_axis_labels", {}).get("y1", "Y1-Axis"),
            "y2": config_dict["plot_settings"].get("y_axis_labels", {}).get("y2", "Y2-Axis")
        }

        self.horizontal_lines = config_dict["plot_settings"].get("horizontal_lines", {})
        self.vertical_lines = config_dict["plot_settings"].get("vertical_lines", {})

        os.makedirs(self.plots_folder_path, exist_ok=True)

    def plot(self):
        fig, ax1 = plot.subplots(figsize=(10, 7))
        ax2 = None

        # Check if any channel is assigned to y2
        has_y2 = any(
            ch.get("y_axis") == "y2"
            for db in self.config["databases"].values()
            for ch in db["channels"].values()
        )
        if has_y2:
            ax2 = ax1.twinx()

        legend_handles = []

        for db_key, db_config in self.config["databases"].items():
            df_wrapper = self.dataframes[db_key]
            df = df_wrapper.get_dataframe()

            for channel, ch_conf in db_config["channels"].items():
                x_column = ch_conf.get("x_column", "index")
                y_axis = ch_conf.get("y_axis", "y1")
                label = ch_conf.get("label", channel)
                color = ch_conf.get("color", None)
                alpha = ch_conf.get("alpha", 1.0)

                if x_column in df.columns:
                    match self.convert_epoch:
                        case "seconds":
                            x_values = df[x_column].compute()
                            x_values = (x_values - x_values.min()+self.offset) / 1000
                        case "miliseconds":
                            x_values = df[x_column].compute()
                            x_values = x_values - x_values.min() + self.offset
                        case _:
                            x_values = df[x_column].compute() + self.offset

                else:
                    x_values = df.index.compute() + self.offset

                if channel in df.columns:
                    y_values = df[channel].compute()

                    if y_axis == "y1":
                        if self.plot_type == "line":
                            handle, = ax1.plot(x_values, y_values, label=label, color=color, alpha=alpha)
                        else:
                            handle, = ax1.scatter(x_values, y_values, label=label, color=color, alpha=alpha)
                    elif ax2:
                        if self.plot_type == "line":
                            handle, = ax2.plot(x_values, y_values, label=label, color=color, alpha=alpha)
                        else:
                            handle, = ax2.scatter(x_values, y_values, label=label, color=color, alpha=alpha)
                    legend_handles.append(handle)

        # Axis labels
        ax1.set_xlabel(self.axis_labels.get("x", "X-Axis"))
        ax1.set_ylabel(self.axis_labels.get("y1", "Y1-Axis"))
        if ax2:
            ax2.set_ylabel(self.axis_labels.get("y2", "Y2-Axis"))

        # Draw horizontal lines
        for line in self.horizontal_lines.values():
            y = line.get("place")
            label = line.get("label")
            color = line.get("color", "black")
            axis = line.get("axis", "y1")
            if axis == "y1":
                handle = ax1.axhline(y=y, color=color, linestyle='--', label=label)
            else:
                handle = ax2.axhline(y=y, color=color, linestyle='--', label=label)
            legend_handles.append(handle)

        # Draw vertical lines
        for line in self.vertical_lines.values():
            x = line.get("place")
            label = line.get("label")
            color = line.get("color", "black")
            axis = line.get("axis", "y1")
            if axis == "y1":
                handle = ax1.axvline(x=x, color=color, linestyle='--', label=label)
            else:
                handle = ax2.axvline(x=x, color=color, linestyle='--', label=label)
            legend_handles.append(handle)

        # Grid setup
        if self.precise_grid:
            ax1.xaxis.set_major_locator(ticker.AutoLocator())
            ax1.xaxis.set_minor_locator(ticker.AutoMinorLocator())
            ax1.yaxis.set_major_locator(ticker.AutoLocator())
            ax1.yaxis.set_minor_locator(ticker.AutoMinorLocator())

        ax1.grid(True, which='both', linestyle='--', linewidth=0.5)
        if ax2:
            if self.precise_grid:
                ax2.yaxis.set_major_locator(ticker.AutoLocator())
                ax2.yaxis.set_minor_locator(ticker.AutoMinorLocator())
            ax2.grid(True, which='both', linestyle='--', linewidth=0.5)

        # Legend and layout
        plot.subplots_adjust(bottom=0.2)
        plot.legend(handles=legend_handles, bbox_to_anchor=(0.5, 0.02), loc="lower center",
                    bbox_transform=fig.transFigure, fancybox=True, shadow=True, ncol=3)

        # Toolbar on top
        mgr = plot.get_current_fig_manager()
        if hasattr(mgr, 'toolbar'):
            mgr.toolbar.pack(side='top', fill='x')

        plot.title(self.plot_name)
        self.save_plot(self.plot_name)
        plot.show()

    def save_plot(self, filename):
        path = os.path.join(self.plots_folder_path, f"{filename}.png")
        plot.savefig(path)
