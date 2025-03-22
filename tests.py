from src.json_parser import JSONParser
from src.plotter import Plotter
from src.data_processing import DataFrameWrapper
from src.data_processing import DataProcessor
import numpy as np
import pywt


def plotter_test():
    dataframes = {
        "db1": df1,
        "db2": df2
    }

    config = {
        "plot_settings": {
            "title": "Rocket Telemetry",
            "type": "line",
            "precise_grid": False,
            "convert_epoch": "seconds",
            "offset": -30000,
            "x_axis_label": "Time (ms)",
            "y_axis_labels": {
                "y1": "Pressure",
                "y2": "Thrust"
            },
            "horizontal_lines": {
                "max_temp": {
                    "place": 85,
                    "label": "Max Safe Temp",
                    "color": "red"
                }
            },
            "vertical_lines": {
                "engine_start": {
                    "place": 100,
                    "label": "Engine Start",
                    "color": "green"
                }
            }
        },
        "databases": {
            "db1": {
                "channels": {
                    "data.CHAMBER_PRES.scaled": {
                        "label": "Chamber_pressure",
                        "color": "orange",
                        "alpha": 1,
                        "y_axis": "y1",
                        "x_column": "header.timestamp_epoch"
                    },
                    "data.FUEL.scaled": {
                        "label": "FUEL_pressure",
                        "color": "red",
                        "alpha": 1,
                        "y_axis": "y1",
                        "x_column": "header.timestamp_epoch"
                    }
                }
            },
            "db2": {
                "channels": {
                    "data.TM1.scaled": {
                        "label": "Thrust",
                        "color": "blue",
                        "alpha": 1,
                        "y_axis": "y2",
                        "x_column": "header.timestamp_epoch"
                    }
                }
            }
        }
    }
    plotter = Plotter(config_dict=config, dataframe_map=dataframes, plots_folder_path="plots")
    plotter.plot()

'''
def wavelet_test():
    df = df3.get_dataframe()
    print(df.columns)
    # Example signal (Replace this with your actual data)
    timestamp_epoch = df['header.timestamp_epoch'].compute()
    N20_PRES = df['data.IFM.scaled'].compute()  # Simulated signal with noise

    # Parameters
    wavelet_name = 'coif5'  # Same as MATLAB's wavelet
    level = 10  # Decomposition level

    # Perform Discrete Wavelet Transform
    c = pywt.wavedec(N20_PRES, wavelet_name, level=level)
    # Extract detail coefficients at the last level
    if level < len(c):  # Ensure level exists
        d = c[level]
    else:
        d = c[-1]

        # Compute noise threshold using median absolute deviation
    sigma = np.median(np.abs(d)) / 0.6745
    threshold = sigma * np.sqrt(2 * np.log(len(N20_PRES)))

    # Apply soft thresholding
    c_thresh = [pywt.threshold(ci, threshold, mode='soft') for ci in c]

    # Reconstruct the denoised signal
    denoised_N20_PRES = pywt.waverec(c_thresh, wavelet_name)

    # Ensure the length of the output matches the input (due to padding)
    denoised_N20_PRES = denoised_N20_PRES[:len(N20_PRES)]

    # Print and visualize
    import matplotlib.pyplot as plt

    plt.figure(figsize=(10, 5))
    plt.plot(timestamp_epoch, N20_PRES, label="Noisy Signal", alpha=0.5)
    plt.plot(timestamp_epoch, denoised_N20_PRES, label="Denoised Signal", linewidth=2)
    plt.legend()
    plt.title("Wavelet Denoising using Coif5 Wavelet")
    plt.show()


def filtering_test():
    xd = df3.get_dataframe()
    print(xd.columns)
    df3_test = DataFrameWrapper(
        csv_path="tests/adv_07_03_2025_fixed.csv"
    )
    processor_filtered = DataProcessor(df3)
    processor_filtered.add_filter("data.ETM-16.scaled", "wavelet_transform", wavelet_name='coif5', level=10,
                                  threshold_mode='soft')
    processor_filtered.queue_filters()
    dataframes = {
        "db1": df3,
        "db2": df3_test
    }
    config = {
        "plot_settings": {
            "title": "Rocket Telemetry",
            "type": "line",
            "precise_grid": False,
            "x_axis_label": "Time (s)",
            "y_axis_labels": {
                "y1": "Pressure",
                "y2": "Thrust"
            },
            "horizontal_lines": {
                "max_temp": {
                    "place": 3,
                    "label": "Max Safe Temp",
                    "color": "red"
                }
            },
            "vertical_lines": {
                "engine_start": {
                    "place": 100,
                    "label": "Engine Start",
                    "color": "green"
                }
            }
        },
        "databases": {
            "db1": {
                "channels": {
                    "data.ETM-16.scaled": {
                        "label": "Denoised pressure",
                        "color": "orange",
                        "alpha": 1,
                        "y_axis": "y1",
                        "x_column": "header.timestamp_epoch"
                    },
                }
            },
            "db2": {
                "channels": {
                    "data.ETM-16.scaled": {
                        "label": "Noised pressure",
                        "color": "blue",
                        "alpha": 0.5,
                        "y_axis": "y1",
                        "x_column": "header.timestamp_epoch"
                    }
                }
            }
        }
    }

    plotter = Plotter(config_dict=config, dataframe_map=dataframes, plots_folder_path="plots")
    plotter.plot()
'''

if __name__ == '__main__':
    df1 = DataFrameWrapper(
        csv_path="tests/denoised_adv_16_03_2025.csv"
    )
    df2 = DataFrameWrapper(
        csv_path="tests/lpb_16_03_2025_interpolated_lpb.csv",
    )
    '''
    df3 = DataFrameWrapper(
        csv_path="tests/adv_07_03_2025_fixed.csv"
    )
    '''
    plotter_test()
    # wavelet_test()
    # filtering_test()
