import socket
import struct
import time
import paho.mqtt.client as mqtt

# MQTT settings
mqtt_broker = '192.168.0.155'  # Replace with your MQTT broker address
mqtt_port = 1883  # Default MQTT port
mqtt_topic = 'record'
mqtt_message = 1

# Multicast settings
multicast_group = '239.255.255.250'
multicast_port = 12345

# Create the MQTT client
mqtt_client = mqtt.Client()

# Connect to the MQTT broker
mqtt_client.connect(mqtt_broker, mqtt_port, 60)

# Publish the MQTT message
mqtt_client.publish(mqtt_topic, mqtt_message)
print(f'Published MQTT message to topic {mqtt_topic}')

# Create the datagram socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Set the time-to-live for messages to 1 so they do not go past the local network segment.
ttl = struct.pack('b', 1)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

try:
    for i in reversed(range(3)):
        # Send data to the multicast group
        print(f'Sending message to {multicast_group}:{multicast_port}')
        message = '{}'.format(i)
        b = bytes(message, encoding='utf-8')
        sent = sock.sendto(b, (multicast_group, multicast_port))

        # Wait for a short time before sending the next message
        time.sleep(1)

    time.sleep(4)
    mqtt_client.publish(mqtt_topic, 0)
    print(f'Published MQTT message to topic {mqtt_topic}')

finally:
    print('Closing socket')
    sock.close()
    mqtt_client.disconnect()
