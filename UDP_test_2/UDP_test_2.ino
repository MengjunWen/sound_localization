#include <WiFi.h>
#include <WiFiUdp.h>

// WiFi credentials
const char *ssid = "EwoutBergsma";
const char *password = "EwoutBergsma";

// Multicast settings
IPAddress multicastAddress(239, 255, 255, 250);  // Multicast address
const int multicastPort = 12345;  // Multicast port

WiFiUDP udp;

void setup() {
  Serial.begin(115200);

  // Connect to Wi-Fi
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  
  Serial.println("");
  Serial.println("WiFi connected.");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());

  // Start UDP
  udp.beginMulticast(multicastAddress, multicastPort);
}

void loop() {
  int packetSize = udp.parsePacket();
  if (packetSize) {
    Serial.printf("Received packet of size %d from %s:%d\n", packetSize, udp.remoteIP().toString().c_str(), udp.remotePort());
    
    char incomingPacket[255];
    int len = udp.read(incomingPacket, 255);
    if (len > 0) {
      incomingPacket[len] = 0;
    }
    Serial.printf("UDP packet contents: %s\n", incomingPacket);
  }
  delay(10);
}
