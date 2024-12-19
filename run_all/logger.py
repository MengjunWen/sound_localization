import os
import csv
from datetime import datetime

class Logger:
    def __init__(self, output_directory):
        self.output_directory = output_directory
        self.timestamps = {}  # 修改为字典而不是列表

    def log_timestamp(self, event_name):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f') 
        self.timestamps[event_name] = timestamp
        print(f"Logged event: {event_name}, at: {timestamp}")

    def save_timestamps_to_csv(self):
        csv_filename = os.path.join(self.output_directory, "timestamps.csv")
        with open(csv_filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Event", "Timestamp"])
            for event, timestamp in self.timestamps.items():
                writer.writerow([event, timestamp])
        print(f"Timestamps saved to {csv_filename}")
