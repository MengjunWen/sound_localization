import socket
from zeroconf import Zeroconf, ServiceBrowser, ServiceListener
import time

# Multicast UDP sender configuration
MULTICAST_GROUP = '239.0.0.1'
MULTICAST_PORT = 12345

# Create a UDP socket
def send_multicast_packet(message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)  # TTL=2 for local network
    try:
        # Send the message to the multicast group
        sock.sendto(message.encode(), (MULTICAST_GROUP, MULTICAST_PORT))
        print(f"Sent: {message} to {MULTICAST_GROUP}:{MULTICAST_PORT}")
    finally:
        sock.close()

# mDNS discovery listener class
class MyListener(ServiceListener):
    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        if info:
            print(f"Service {name} added, address: {socket.inet_ntoa(info.addresses[0])}, port: {info.port}")
        else:
            print(f"Service {name} added, no details available")

    def remove_service(self, zeroconf, type, name):
        print(f"Service {name} removed")

    def update_service(self, zeroconf, type, name):
        print(f"Service {name} updated")

# Function to discover mDNS services
def discover_mdns_services():
    zeroconf = Zeroconf()
    listener = MyListener()
    browser = ServiceBrowser(zeroconf, "_http._tcp.local.", listener)
    
    print("Discovering mDNS services...")
    try:
        # Discover services for 10 seconds
        time.sleep(10)
    finally:
        zeroconf.close()

if __name__ == "__main__":
    # Test multicast packet sending
    test_message = "Hello ESP32!"
    send_multicast_packet(test_message)

    # Test mDNS service discovery
    discover_mdns_services()
