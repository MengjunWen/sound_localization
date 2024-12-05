import os
import csv
import json
import time
import cv2
import numpy as np
from datetime import datetime
import socket
from zeroconf import Zeroconf, ServiceBrowser, ServiceStateChange
import requests
import asyncio
from irobot_edu_sdk.backend.bluetooth import Bluetooth
from irobot_edu_sdk.robots import Root, event


# Video Recording Module
class VideoRecorder:
    def __init__(self, calibration_file):
        self.calibration_file = calibration_file
        self.cap = None
        self.out = None
        self.map1 = None
        self.map2 = None
        self.frame_width = None
        self.frame_height = None
        self.output_filename = None
        self.recording = False

    def start(self):
        # Load calibration data
        with np.load(self.calibration_file) as data:
            mtx = data['mtx']
            dist = data['dist']

        # Initialize video capture
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise Exception("Error: Cannot open the camera.")

        # Get frame dimensions
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Initialize video writer
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_filename = f'recorded_undistorted_{timestamp}.avi'
        self.out = cv2.VideoWriter(self.output_filename, fourcc, 20.0, (self.frame_width, self.frame_height))

        # Precompute undistortion maps
        self.map1, self.map2 = cv2.initUndistortRectifyMap(mtx, dist, None, mtx, (self.frame_width, self.frame_height), cv2.CV_32FC1)
        self.recording = True
        print(f"Video recording started: {self.output_filename}")

    async def capture_frames(self):
        while self.recording and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                break
            # Undistort and write frame
            frame_undistorted = cv2.remap(frame, self.map1, self.map2, cv2.INTER_LINEAR)
            self.out.write(frame_undistorted)
            await asyncio.sleep(0)  # Yield control to the event loop

    def stop(self):
        self.recording = False
        if self.cap:
            self.cap.release()
        if self.out:
            self.out.release()
        cv2.destroyAllWindows()
        print(f"Video recording stopped. File saved: {self.output_filename}")

# Audio Recording Module
class AudioRecorders:
    # Configuration
    MULTICAST_GROUP = '239.0.0.1'
    MULTICAST_PORT = 12345
    SERVICE_TYPE = "_http._tcp.local."
    ESP32_SERVICE_NAME = "ESP32_Audio_Device"
    DOWNLOAD_FOLDER = "./raw_files"

    def __init__(self):
        self.list_of_esp32 = []

    async def discover_devices(self):
        zeroconf = Zeroconf()
        browser = ServiceBrowser(zeroconf, self.SERVICE_TYPE, handlers=[self._on_service_state_change])
        print("Discovering ESP32 devices...")
        await asyncio.sleep(5)  # Wait for devices to be discovered
        zeroconf.close()

    def _on_service_state_change(self, zeroconf, service_type, name, state_change):
        if state_change == ServiceStateChange.Added:
            info = zeroconf.get_service_info(service_type, name)
            if info and self.ESP32_SERVICE_NAME in name:
                ip = socket.inet_ntoa(info.addresses[0])
                if ip not in self.list_of_esp32:
                    self.list_of_esp32.append(ip)
                    print(f"Discovered device: {ip}")

    def start_tcp(self):
        # Start recording on each ESP device
        for ip in self.list_of_esp32:
            url = f"http://{ip}/start"
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    print(f"Started recording on {ip}")
                else:
                    print(f"Failed to start recording on {ip}")
            except requests.RequestException as e:
                print(f"Error connecting to {ip}: {e}")

    def stop_tcp(self):
        # Stop recording on each ESP device
        for ip in self.list_of_esp32:
            url = f"http://{ip}/stop"
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    print(f"Stopped recording on {ip}")
                else:
                    print(f"Failed to stop recording on {ip}")
            except requests.RequestException as e:
                print(f"Error connecting to {ip}: {e}")

    def list_recordings(self, device_ip):
        url = f"http://{device_ip}/list"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return json.loads(response.text)
            else:
                print(f"Failed to retrieve recording list from {device_ip}. Status code: {response.status_code}")
                return None
        except requests.RequestException as e:
            print(f"Error connecting to {device_ip} for listing recordings: {e}")
            return None

    def download_latest_recording(self, device_ip):
        recordings = self.list_recordings(device_ip)
        if not recordings:
            print(f"No recordings found on {device_ip}")
            return
        recordings.sort()
        latest = next((rec for rec in reversed(recordings) if rec.endswith('.bin')), None)
        if latest:
            sanitized_ip = device_ip.replace('.', '')
            download_name = f"{sanitized_ip}_{latest}"
            url = f"http://{device_ip}/{latest}"
            try:
                response = requests.get(url, stream=True)
                if response.status_code == 200:
                    os.makedirs(self.DOWNLOAD_FOLDER, exist_ok=True)
                    file_path = os.path.join(self.DOWNLOAD_FOLDER, download_name)
                    with open(file_path, 'wb') as file:
                        for chunk in response.iter_content(chunk_size=4096):
                            file.write(chunk)
                    print(f"Downloaded {latest} from {device_ip} as {download_name}")
                else:
                    print(f"Failed to download {latest} from {device_ip}. Status code: {response.status_code}")
            except requests.RequestException as e:
                print(f"Error downloading {latest} from {device_ip}: {e}")
        else:
            print(f"No suitable recordings found on {device_ip}")

# Robot Control Module
class RobotController:
    def __init__(self, action_sequence_file):
        self.robot = Root(Bluetooth())
        self.action_sequence_file = action_sequence_file

    def load_actions_from_csv(self):
        actions = []
        with open(self.action_sequence_file, mode='r') as file:
            reader = csv.reader(file)
            for row in reader:
                print(f"Loading row: {row}")
                action_type = row[0]
                if action_type == 'move':
                    distance = int(row[1])
                    if len(row) == 2:
                        actions.append((action_type, distance))
                    elif len(row) == 3:
                        duration = float(row[2])
                        actions.append((action_type, distance, duration))
                    elif len(row) == 4:
                        frequency = int(row[2])
                        duration = float(row[3])
                        actions.append((action_type, distance, frequency, duration))
                elif action_type in ['turn_left', 'turn_right']:
                    degrees = int(row[1])
                    if len(row) == 2:
                        actions.append((action_type, degrees))
                    elif len(row) == 3:
                        duration = float(row[2])
                        actions.append((action_type, degrees, duration))
                    elif len(row) == 4:
                        frequency = int(row[2])
                        duration = float(row[3])
                        actions.append((action_type, degrees, frequency, duration))
                elif action_type == 'wait':
                    duration = float(row[1])
                    actions.append((action_type, duration))
        print(f"Loaded actions: {actions}")
        return actions

    @event(Root.when_play)
    async def perform_actions(self):
        actions = self.load_actions_from_csv()
        print("Event triggered: Performing actions")
        for action in actions:
            print(f"Performing action: {action}")
            if action[0] == 'move':
                await self.robot.move(action[1])
                if len(action) > 2:
                    await self.robot.play_note(action[2], action[3])
            elif action[0] == 'wait':
                if len(action) == 3:
                    await self.robot.play_note(action[2], action[1])
                await self.robot.wait(action[1])
            elif action[0] in ['turn_left', 'turn_right']:
                if action[0] == 'turn_left':
                    await self.robot.turn_left(action[1])
                else:
                    await self.robot.turn_right(action[1])
                if len(action) > 2:
                    await self.robot.play_note(action[2], action[3])

# Main Controller
class MultiDeviceController:
    def __init__(self, calibration_file, action_sequence_file):
        self.video_recorder = VideoRecorder(calibration_file)
        self.audio_recorders = AudioRecorders()
        self.robot_controller = RobotController(action_sequence_file)
        self.timestamps = {}
        self.csv_filename = f"run_{int(time.time())}.csv"

    def log_timestamp(self, event_name):
        timestamp = datetime.now()
        self.timestamps[event_name] = timestamp
        print(f"{event_name}: {timestamp}")

    def save_timestamps_to_csv(self):
        with open(self.csv_filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Event", "Timestamp"])
            for event, timestamp in self.timestamps.items():
                writer.writerow([event, timestamp])
        print(f"Timestamps saved to {self.csv_filename}")

    async def start(self):
        # Start video recording
        self.log_timestamp('video_start')
        self.video_recorder.start()
        video_task = asyncio.create_task(self.video_recorder.capture_frames())

        # Discover ESP devices and start audio recording
        await self.audio_recorders.discover_devices()
        if self.audio_recorders.list_of_esp32:
            self.log_timestamp('audio_start')
            self.audio_recorders.start_tcp()

        # Perform robot actions
        await self.robot_controller.perform_actions()

        # Wait 3 seconds after last robot action
        await asyncio.sleep(3)
        print("Completed waiting 3 seconds after robot actions.")

        # Stop all recordings
        await self.stop()
        await video_task

    async def stop(self):
        # Stop audio recording
        if self.audio_recorders.list_of_esp32:
            self.log_timestamp('audio_stop')
            self.audio_recorders.stop_tcp()

        # Stop video recording
        self.log_timestamp('video_stop')
        self.video_recorder.stop()

        # Save timestamps
        self.save_timestamps_to_csv()

        # Download latest recordings from ESP devices
        for ip in self.audio_recorders.list_of_esp32:
            self.audio_recorders.download_latest_recording(ip)

# Entry Point
if __name__ == "__main__":
    calibration_file = 'path_to_calibration_data.npz'
    action_sequence_file = 'path_to_action_sequence.csv'

    controller = MultiDeviceController(calibration_file, action_sequence_file)
    asyncio.run(controller.start())