import time
import requests
from zeroconf import ServiceBrowser, Zeroconf

# Listener class to handle discovered services
class MyListener:
    def __init__(self):
        self.mdns_name = None
        self.ip_address = None

    def add_service(self, zeroconf, service_type, name):
        info = zeroconf.get_service_info(service_type, name)
        if info:
            service_name = info.name
            self.mdns_name = info.server  # mDNS hostname (e.g., esp32.local.)
            self.ip_address = ".".join(map(str, info.addresses[0])) if info.addresses else "No IP"
            port = info.port

            print(f"Discovered Service Name: {service_name}")
            print(f"mDNS Name: {self.mdns_name}")
            print(f"IP Address: {self.ip_address}")
            print(f"Port: {port}")
            print("-" * 30)

def discover_mdns_services():
    zeroconf = Zeroconf()
    listener = MyListener()
    browser = ServiceBrowser(zeroconf, "_http._tcp.local.", listener)  # Look for HTTP services

    print("Discovering mDNS services...")
    try:
        # Discover services for 10 seconds
        time.sleep(10)
    finally:
        zeroconf.close()

    # Return the discovered mDNS name and IP address
    return listener.mdns_name, listener.ip_address

def test_arduino_server(mdns_name):
    # Build the request URL using the mDNS name
    url = f"http://{mdns_name}/"

    try:
        # Send the request to the Arduino
        response = requests.get(url)

        # Check if the request was successful
        if response.status_code == 200:
            print("Request successful.")
            print("Response:", response.text)
            # Check if the response contains "Test"
            if "Test" in response.text:
                print("Arduino test successful: 'Test' message received.")
            else:
                print("Unexpected response received.")
        else:
            print(f"Failed to connect to Arduino. HTTP status code: {response.status_code}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Step 1: Discover the ESP32 device using mDNS
    mdns_name, ip_address = discover_mdns_services()

    # Step 2: If the ESP32 is found, send the test request
    if mdns_name:
        print(f"Using mDNS Name: {mdns_name} for testing.")
        test_arduino_server(mdns_name)
    else:
        print("No ESP32 mDNS service found.")
