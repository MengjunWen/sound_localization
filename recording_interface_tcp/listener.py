# mDNS discovery listener class
import socket
from zeroconf import ServiceListener

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