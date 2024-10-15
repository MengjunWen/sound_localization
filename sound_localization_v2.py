import socket
import requests
import os
import json
import time
from zeroconf import Zeroconf, ServiceBrowser, ServiceStateChange

# Configuration settings
SERVICE_TYPE = "_http._tcp.local."
ESP32_SERVICE_NAME = "ESP32_Audio_Device"
UDP_PORT = 12345
DOWNLOAD_FOLDER = "./downloads"

# Global variable to store the ESP32 IP address
esp32_ip = None

def on_service_state_change(zeroconf, service_type, name, state_change):
    global esp32_ip
    if state_change is ServiceStateChange.Added:
        info = zeroconf.get_service_info(service_type, name)
        if info and ESP32_SERVICE_NAME in name:
            esp32_ip = socket.inet_ntoa(info.addresses[0])
            print(f"Discovered ESP32 device at IP address: {esp32_ip}")

def discover_esp32():
    zeroconf = Zeroconf()
    listener = ServiceBrowser(zeroconf, SERVICE_TYPE, handlers=[on_service_state_change])

    print("Searching for ESP32 device on the network...")
    for _ in range(10):  # Retry for up to 10 seconds to find the device
        if esp32_ip:
            break
        time.sleep(1)
    
    zeroconf.close()
    if not esp32_ip:
        print("Failed to discover ESP32 device using mDNS.")
        exit(1)

# UDP socket setup
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def send_udp_command(command):
    sock.sendto(command.encode(), (esp32_ip, UDP_PORT))
    print(f"Sent UDP command: {command}")

def start_recording():
    send_udp_command("START_RECORDING")

def stop_recording():
    send_udp_command("STOP_RECORDING")

def list_recordings():
    url = f"http://{esp32_ip}/list"
    response = requests.get(url)

    if response.status_code == 200:
        recordings = json.loads(response.text)
        print("Available recordings on the ESP32 device:")
        for recording in recordings:
            print(recording)
    else:
        print(f"Failed to retrieve recording list. Status code: {response.status_code}")

def download_recording(filename):
    url = f"http://{esp32_ip}/{filename}"
    response = requests.get(url, stream=True)

    if response.status_code == 200:
        os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
        file_path = os.path.join(DOWNLOAD_FOLDER, filename)

        with open(file_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=1024):
                file.write(chunk)
        print(f"Downloaded recording to {file_path}")
    else:
        print(f"Failed to download the file. Status code: {response.status_code}")

if __name__ == "__main__":
    discover_esp32()  # Discover the ESP32 device using mDNS

    while True:
        print("\nOptions:")
        print("1. Start Recording")
        print("2. Stop Recording")
        print("3. List Recordings")
        print("4. Download Recording")
        print("5. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            start_recording()
        elif choice == '2':
            stop_recording()
        elif choice == '3':
            list_recordings()
        elif choice == '4':
            filename = input("Enter the filename to download (e.g., recording_123456.wav): ")
            download_recording(filename)
        elif choice == '5':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please enter a valid option.")
