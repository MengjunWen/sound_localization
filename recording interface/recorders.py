import socket
from zeroconf import Zeroconf, ServiceBrowser, ServiceListener, ServiceStateChange
import time
import requests
import json
import asyncio
import wave
import os

class Recorders:
    # Multicast UDP sender configuration
    MULTICAST_GROUP = '239.0.0.1'
    MULTICAST_PORT = 12345
    SERVICE_TYPE = "_http._tcp.local."
    ESP32_SERVICE_NAME = "ESP32_Audio_Device"
    DOWNLOAD_FOLDER = "./raw_files"
    OUTPUT_FOLDER = "./wav_files"
    SAMPLE_FREQUENCY = 44100

    esp32_ip = None
    
    # Function to discover mDNS services
    def __init__(self, multicast_group=MULTICAST_GROUP, multicast_port=MULTICAST_PORT):
        self.MULTICAST_GROUP = multicast_group
        self.MULTICAST_PORT = multicast_port

    def start(self):
        self.__send_multicast_packet("START_RECORDING")

    def stop(self):
        self.__send_multicast_packet("STOP_RECORDING")
    
    async def find(self, name = ESP32_SERVICE_NAME):
        self.ESP32_SERVICE_NAME = name
        zeroconf = Zeroconf()
        listener = ServiceBrowser(zeroconf, self.SERVICE_TYPE, handlers=[self.__on_service_state_change])

        # print("Searckhing for ESP32 device on the network...")
        for _ in range(10):  # Retry for up to 10 seconds to find the device
            if self.esp32_ip:
                break
            await asyncio.sleep(1)
        
        zeroconf.close()

    def list_recordings(self, device_ip = esp32_ip):

        url = f"http://{device_ip}/list"
        response = requests.get(url)

        if response.status_code == 200:
            recordings = json.loads(response.text)
            return recordings
        else:
            print(f"Failed to retrieve recording list. Status code: {response.status_code}")
            return None

    def download_latest_recording(self, device_ip = esp32_ip):
        recordings = self.list_recordings(device_ip)
        recordings.sort()
        latest = None
        if recordings:
            for i in range(len(recordings)):
                if recordings[-i].endswith('.wav'):
                    latest = recordings[-i]
        else:
            return None

        self.__download_recording(latest, device_ip)
        self.__convert_text_to_wav(os.path.join(self.DOWNLOAD_FOLDER, latest), os.path.join(self.OUTPUT_FOLDER, latest), 1, 2, self.SAMPLE_FREQUENCY)
        
    def erase(self):
        self.__send_multicast_packet("ERASE_SD")

    def __send_multicast_packet(self, message):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)  # TTL=2 for local network
        try:
            # Send the message to the multicast group
            sock.sendto(message.encode(), (self.MULTICAST_GROUP, self.MULTICAST_PORT))
            print(f"Sent: {message} to {self.MULTICAST_GROUP}:{self.MULTICAST_PORT}")
        finally:
            sock.close()

    def __on_service_state_change(self, zeroconf, service_type, name, state_change):
        
        if state_change is ServiceStateChange.Added:
            info = zeroconf.get_service_info(service_type, name)
            if info and self.ESP32_SERVICE_NAME in name:
                self.esp32_ip = socket.inet_ntoa(info.addresses[0])
                print(f"Discovered ESP32 device at IP address: {self.esp32_ip}")

    def __convert_text_to_wav(self, input_file, output_file, channels, sampwidth, framerate):
        # Prepare to read the text file and collect data
        data = []
        with open(input_file, 'r') as file:
            for line in file:
                if line.strip():  # Ensure the line has content
                    # Convert the line to an integer and pack it into binary format
                    # Adjust the format '<h' as per your data range and endianess
                    # also add AMPLIFY with '*5'
                    sample = int(float(line.strip())*5)
                    # Check sample width to determine packing format
                    if sampwidth == 2:
                        data.append(sample.to_bytes(2, byteorder='little', signed=True))
                    elif sampwidth == 1:
                        data.append(sample.to_bytes(1, byteorder='little', signed=True))
        # Convert the list of bytes into a bytes object
        data_bytes = b''.join(data)

        # Write the data to a WAV file
        with wave.open(output_file, 'w') as wavfile:
            wavfile.setnchannels(channels)
            wavfile.setsampwidth(sampwidth)
            wavfile.setframerate(framerate)
            wavfile.writeframes(data_bytes)

    def __download_recording(self, filename, device_ip = esp32_ip):
        url = f"http://{device_ip}/{filename}"
        response = requests.get(url, stream=True)

        if response.status_code == 200:
            os.makedirs(self.DOWNLOAD_FOLDER, exist_ok=True)
            file_path = os.path.join(self.DOWNLOAD_FOLDER, filename)

            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=1024):
                    file.write(chunk)
            print(f"Downloaded recording to {file_path}")
        else:
            print(f"Failed to download the file. Status code: {response.status_code}")

    # def __discover_mdns_services():
    #     zeroconf = Zeroconf()
    #     listener = MyListener()
    #     browser = ServiceBrowser(zeroconf, "_http._tcp.local.", listener)
        
    #     print("Discovering mDNS services...")
    #     try:
    #         # Discover services for 10 seconds
    #         time.sleep(10)
    #     finally:
    #         zeroconf.close()

    # Create a UDP socket