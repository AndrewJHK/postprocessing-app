import csv
from datetime import datetime
import os
from collections import namedtuple

DeviceCSVConfig = namedtuple("DeviceCSVConfig", ["name", "origin_id", "fieldnames", "channel_mapping"])

DEVICE_NAME_MAPPING = {
    100: "lpb",
    130: "adv_usb",
    131: "adv_pcie",
    200: "comp"
}
CHANNEL_LABEL_MAPPINGS = {
    130: {
        "usb4716.chan0.scaled": "N2O",
        "usb4716.chan1.scaled": "CHAMBER_PRES",
        "usb4716.chan2.scaled": "N2O_PRES",
        "usb4716.chan3.scaled": "FUEL"
    },
    100: {
        "adc1.chan0.scaled": "TM2.scaled",
        "adc1.chan0.raw": "TM2.raw",
        "adc1.chan1.scaled": "PT2.scaled",
        "adc1.chan1.raw": "PT2.raw",
        "adc1.chan2.scaled": "PT1.scaled",
        "adc1.chan2.raw": "PT1.raw",
        "adc1.chan3.scaled": "TM1.scaled",
        "adc1.chan3.raw": "TM1.raw",
        "adc2.chan0.scaled": "PT5,scaled",
        "adc2.chan0.raw": "PT5,raw",
        "adc2.chan1.scaled": "PT6.scaled",
        "adc2.chan1.raw": "PT6.raw",
        "adc2.chan2.scaled": "PT4.scaled",
        "adc2.chan2.raw": "PT4.raw",
        "adc2.chan3.scaled": "PT3.scaled",
        "adc2.chan3.raw": "PT3.raw"

    }
}


class JSONParser:
    def __init__(self, json_data, csv_path, interpolated):
        self.json_data = json_data
        self.csv_path = csv_path
        self.interpolated = interpolated
        self.fields_per_origin = {}
        self.last_known = {}
        self.counters = {}
        self.devices = {}

        self._extract_all_origins()
        self._initialize_devices()

    def _extract_all_origins(self):
        for record in self.json_data:
            origin = record.get("header", {}).get("origin")
            if origin is None:
                continue
            if origin not in self.fields_per_origin:
                self.fields_per_origin[origin] = set()
            flat = self.flatten_dict(record.get("data", {}))
            for full_key in flat:
                mapped_key = self.map_key(origin, full_key)
                self.fields_per_origin[origin].add(f"data.{mapped_key}")

    def _initialize_devices(self):
        for origin, fields in self.fields_per_origin.items():
            field_list = ["header.origin", "header.timestamp_epoch", "header.timestamp_human",
                          "header.counter"] + sorted(list(fields)) + ["data.cpu_temperature"]
            dev_name = DEVICE_NAME_MAPPING.get(origin, f"dev_{origin}")
            self.devices[origin] = DeviceCSVConfig(dev_name, origin, field_list, CHANNEL_LABEL_MAPPINGS.get(origin, {}))
            self.last_known[origin] = {}
            self.counters[origin] = 0

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

        cpu_temp = record.get("data", {}).get("cpu_temperature", {}).get("value")
        if cpu_temp is not None:
            self.last_known[origin]["data.cpu_temperature"] = cpu_temp
        row_data["data.cpu_temperature"] = self.last_known[origin].get("data.cpu_temperature")

        flattened = self.flatten_dict(record.get("data", {}))
        for field_key, value in flattened.items():
            mapped_key = self.map_key(origin, field_key)
            full_key = f"data.{mapped_key}"
            self.last_known[origin][full_key] = value
            row_data[full_key] = value

        for field in device.fieldnames:
            if field not in row_data:
                row_data[field] = self.last_known[origin].get(field) if self.interpolated else None

        non_header_keys = [k for k in row_data if not k.startswith("header") and k != "data.cpu_temperature"]
        if all(row_data.get(k) is None for k in non_header_keys):
            return

        writer.writerow(row_data)
        self.counters[origin] += 1

    def json_to_csv(self):
        sorted_data = sorted(self.json_data, key=self.get_timestamp)
        suffix = "_interpolated" if self.interpolated else "_none_filled"
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

        for key, path in list(file_paths.items()):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    reader = list(csv.reader(f))
                if len(reader) <= 1:
                    os.remove(path)
                    del file_paths[key]
                else:
                    # Drop empty columns
                    headers = reader[0]
                    transposed = list(zip(*reader[1:]))
                    non_empty_cols = [i for i, col in enumerate(transposed) if
                                      any(cell.strip() != '' for cell in col)]
                    cleaned = [[headers[i] for i in non_empty_cols]] + [
                        [row[i] for i in non_empty_cols] for row in reader[1:]
                    ]
                    with open(path, 'w', newline='', encoding='utf-8') as f_out:
                        writer = csv.writer(f_out)
                        writer.writerows(cleaned)
            except FileNotFoundError:
                pass
        return list(file_paths.values())

    def flatten_dict(self, d, parent_key='', sep='.'):
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self.flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    @staticmethod
    def map_key(origin, key):
        mapping = CHANNEL_LABEL_MAPPINGS.get(origin, {})
        return mapping.get(key, key)

    @staticmethod
    def get_timestamp(record):
        timestamp_data = record["header"].get("timestamp", {})
        low = timestamp_data.get("low", 0)
        high = timestamp_data.get("high", 0)
        return (high * (2 ** 32)) + low
