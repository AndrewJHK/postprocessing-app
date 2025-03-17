import csv
from datetime import datetime
import os

LPB_CHANNEL_MAPPING = {
    "adc1.chan0": "TM2",
    "adc1.chan1": "PT2",
    "adc1.chan2": "PT1",
    "adc1.chan3": "TM1",
    "adc2.chan0": "PT5",
    "adc2.chan1": "PT6",
    "adc2.chan2": "PT4",
    "adc2.chan3": "PT3"
}
ADV_CHANNEL_MAPPING = {
    "usb4716.chan0": "N20_PRES",
    "usb4716.chan1": "CHAMBER_PRES",
    "usb4716.chan2": "N20",
    "usb4716.chan3": "FUEL",
    "usb4716.chan4": "CH4",
    "usb4716.chan5": "CH5",
    "usb4716.chan6": "CH6",
    "usb4716.chan7": "CH7",
    "usb4716.chan8": "CH8",
    "usb4716.chan9": "CH9",
    "usb4716.chan10": "CH10",
    "usb4716.chan11": "CH11",
    "usb4716.chan12": "CH12",
    "usb4716.chan13": "CH13",
    "usb4716.chan14": "CH14",
    "usb4716.chan15": "CH15"
}
LPB_FIELDNAMES = [
    "header.origin", "header.timestamp_epoch", "header.timestamp_human", "header.counter",
    "data.TM1.raw", "data.TM1.scaled", "data.TM2.raw", "data.TM2.scaled",
    "data.PT1.raw", "data.PT1.scaled", "data.PT2.raw", "data.PT2.scaled",
    "data.PT3.raw", "data.PT3.scaled", "data.PT4.raw", "data.PT4.scaled",
    "data.PT5.raw", "data.PT5.scaled", "data.PT6.raw", "data.PT6.scaled",
    "data.cpu_temperature"
]
ADV_FIELDNAMES = [
    "header.origin", "header.timestamp_epoch", "header.timestamp_human", "header.counter",
    "data.N20_PRES.scaled", "data.CHAMBER_PRES.scaled",
    "data.N20.scaled", "data.FUEL.scaled",
    "data.CH4.scaled", "data.CH5.scaled",
    "data.CH6.scaled", "data.CH7.scaled",
    "data.CH8.scaled", "data.CH9.scaled",
    "data.CH10.scaled", "data.CH11.scaled",
    "data.CH12.scaled", "data.CH13.scaled",
    "data.CH14.scaled", "data.CH15.scaled",
    "data.cpu_temperature"
]


class JSONParser:
    def __init__(self, json_data, csv_path, interpolated):
        self.json_data = json_data
        self.csv_path = csv_path
        self.interpolated = interpolated
        self.last_known_values_adv = {}
        self.last_known_values_lpb = {}
        self.adv_counter = 0
        self.lpb_counter = 0

    def write_row(self, record, last_known_values, writer, counter, fieldnames, channel_mapping, ):
        origin = record["header"].get("origin", 0)
        timestamp_data = record["header"].get("timestamp", {})
        low = timestamp_data.get("low", 0)
        high = timestamp_data.get("high", 0)
        timestamp_epoch_milliseconds = (high * (2 ** 32)) + low
        seconds = timestamp_epoch_milliseconds // 1000
        milliseconds = timestamp_epoch_milliseconds % 1000
        try:
            base_timestamp = datetime.fromtimestamp(seconds)
            timestamp_human = f"{base_timestamp.strftime('%Y-%m-%d %H:%M:%S')}.{milliseconds}"

        except (OSError, ValueError):
            timestamp_human = "1970-01-01 00:00:00.000"
        row_data = {
            "header.origin": origin,
            "header.timestamp_epoch": timestamp_epoch_milliseconds,
            "header.timestamp_human": timestamp_human,
            "header.counter": counter
        }
        cpu_temp_data = record["data"].get("cpu_temperature")
        if cpu_temp_data:
            last_known_values["data.cpu_temperature"] = cpu_temp_data.get("value", 0)
        row_data["data.cpu_temperature"] = last_known_values["data.cpu_temperature"]

        for field_key, channels in record["data"].items():
            if field_key == "cpu_temperature":
                continue

            for channel_key, channel_data in channels.items():
                full_channel_name = f"{field_key}.{channel_key}"
                channel_label = channel_mapping.get(full_channel_name)

                if channel_label:
                    raw_column = f"data.{channel_label}.raw"
                    scaled_column = f"data.{channel_label}.scaled"

                    if "raw" in channel_data:
                        last_known_values[raw_column] = channel_data["raw"]
                    if "scaled" in channel_data:
                        last_known_values[scaled_column] = channel_data["scaled"]

                    row_data[raw_column] = last_known_values[raw_column]
                    row_data[scaled_column] = last_known_values[scaled_column]

        for field in fieldnames:
            if field not in row_data:
                row_data[field] = last_known_values[field] if self.interpolated else None

        writer.writerow(row_data)
        counter += 1

    def initialize_writer(self, data_csv, fieldnames, last_known_values):
        writer = csv.DictWriter(data_csv, fieldnames=fieldnames)
        writer.writeheader()
        last_known_values = {field: None for field in fieldnames}
        return writer

    def json_to_csv(self):

        sorted_data = sorted(self.json_data, key=self.get_timestamp)
        lpb_csv_path = None
        adv_csv_path = None
        match self.interpolated:
            case True:
                lpb_csv_path = f"{self.csv_path}_none_filled_lpb.csv"
                adv_csv_path = f"{self.csv_path}_none_filled_adv.csv"
            case False:
                lpb_csv_path = f"{self.csv_path}_interpolated_lpb.csv"
                adv_csv_path = f"{self.csv_path}_interpolated_adv.csv"

        with (
            open(lpb_csv_path, mode='w', newline='') as lpb_csv,
            open(adv_csv_path, mode='w', newline='') as adv_csv
        ):
            # LPB initialization
            writer_lpb = self.initialize_writer(lpb_csv, LPB_FIELDNAMES, self.last_known_values_lpb)
            # ADV initialization
            writer_adv = self.initialize_writer(adv_csv, LPB_FIELDNAMES, self.last_known_values_lpb)

            for record in sorted_data:
                match record["header"].get("origin"):
                    case 100:
                        self.write_row(record, self.last_known_values_lpb, writer_lpb, self.lpb_counter, LPB_FIELDNAMES,
                                       LPB_CHANNEL_MAPPING)
                    case 130:
                        self.write_row(record, self.last_known_values_adv, writer_adv, self.adv_counter, ADV_FIELDNAMES,
                                       ADV_CHANNEL_MAPPING)
                    case _:
                        continue

        for file_path in [lpb_csv_path, adv_csv_path]:
            deletion = False
            try:
                with open(file_path, 'r', encoding='utf-8') as csv_file:
                    reader = csv.reader(csv_file)
                    rows = list(reader)
                    if len(rows) <= 1:
                        deletion = True
                if deletion:
                    os.remove(file_path)
            except FileNotFoundError:
                pass

    @staticmethod
    def get_timestamp(record):
        timestamp_data = record["header"].get("timestamp", {})
        low = timestamp_data.get("low", 0)
        high = timestamp_data.get("high", 0)
        return (high * (2 ** 32)) + low
