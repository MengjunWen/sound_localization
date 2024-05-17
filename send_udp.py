import socket
import struct
import time

# Multicast settings
multicast_group = '239.255.255.250'
multicast_port = 12345
message = b'Hello, ESP32!'

# Create the datagram socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Set the time-to-live for messages to 1 so they do not go past the local network segment.
ttl = struct.pack('b', 1)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

try:
    while True:
        # Send data to the multicast group
        print(f'Sending message to {multicast_group}:{multicast_port}')
        sent = sock.sendto(message, (multicast_group, multicast_port))

        # Wait for a short time before sending the next message
        time.sleep(2)

finally:
    print('Closing socket')
    sock.close()
