import csv
from datetime import datetime
import os
from collections import namedtuple

DeviceCSVConfig = namedtuple("DeviceCSVConfig", ["name", "origin_id", "fieldnames", "channel_mapping"])

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

        self.devices = {
            100: DeviceCSVConfig("lpb", 100, LPB_FIELDNAMES, LPB_CHANNEL_MAPPING),
            130: DeviceCSVConfig("adv", 130, ADV_FIELDNAMES, ADV_CHANNEL_MAPPING)
        }
        self.last_known = {100: {}, 130: {}}
        self.counters = {100: 0, 130: 0}

    def write_row(self, record, device: DeviceCSVConfig, writer):
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
            "header.counter": self.counters[origin]
        }

        cpu_temp_data = record["data"].get("cpu_temperature")
        if cpu_temp_data:
            self.last_known[origin]["data.cpu_temperature"] = cpu_temp_data.get("value", 0)
        row_data["data.cpu_temperature"] = self.last_known[origin].get("data.cpu_temperature")

        for field_key, channels in record["data"].items():
            if field_key == "cpu_temperature":
                continue

            for channel_key, channel_data in channels.items():
                full_channel_name = f"{field_key}.{channel_key}"
                channel_label = device.channel_mapping.get(full_channel_name)

                if channel_label:
                    raw_column = f"data.{channel_label}.raw"
                    scaled_column = f"data.{channel_label}.scaled"

                    if "raw" in channel_data:
                        self.last_known[origin][raw_column] = channel_data["raw"]
                    if "scaled" in channel_data:
                        self.last_known[origin][scaled_column] = channel_data["scaled"]

                    row_data[raw_column] = self.last_known[origin].get(raw_column)
                    row_data[scaled_column] = self.last_known[origin].get(scaled_column)

        for field in device.fieldnames:
            if field not in row_data:
                row_data[field] = self.last_known[origin].get(field) if self.interpolated else None

        writer.writerow(row_data)
        self.counters[origin] += 1

    def json_to_csv(self):
        sorted_data = sorted(self.json_data, key=self.get_timestamp)
        suffix = "_none_filled" if self.interpolated else "_interpolated"
        file_paths = {
            origin: f"{self.csv_path}{suffix}_{device.name}.csv"
            for origin, device in self.devices.items()
        }

        writers = {}
        files = {}
        try:
            for origin, device in self.devices.items():
                file = open(file_paths[origin], mode='w', newline='')
                writer = csv.DictWriter(file, fieldnames=device.fieldnames)
                writer.writeheader()
                self.last_known[origin] = {field: None for field in device.fieldnames}
                writers[origin] = writer
                files[origin] = file

            for record in sorted_data:
                origin = record["header"].get("origin")
                if origin in self.devices:
                    self.write_row(record, self.devices[origin], writers[origin])

        finally:
            for file in files.values():
                file.close()

        # Remove empty files
        for path in file_paths.values():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    if len(list(csv.reader(f))) <= 1:
                        os.remove(path)
            except FileNotFoundError:
                pass

    @staticmethod
    def get_timestamp(record):
        timestamp_data = record["header"].get("timestamp", {})
        low = timestamp_data.get("low", 0)
        high = timestamp_data.get("high", 0)
        return (high * (2 ** 32)) + low
