#include <WiFi.h>
#include <WiFiUdp.h>
#include <ESPmDNS.h>
#include "config.h"
#include "OTAUpdate.h"
#include "AudioControl.h"
WiFiUDP udp;
ESP32Time rtc;
bool isRecording = false;
WiFiServer server(80);
IPAddress multicastAddress(239, 0, 0, 1);
#define LED_PIN 2  

void connectToWiFi() {
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nConnected to WiFi");
}

void setup() {
    pinMode(LED_PIN, OUTPUT);  // Set LED_PIN as an output
    digitalWrite(LED_PIN, LOW); // Ensure LED is off initially
    Serial.begin(115200);
    Serial.println("Starting");
    for(int i = 0; i < 10; i++){
      delay(1000);
      Serial.println("...");
    }
    connectToWiFi();
    // Setup mDNS for device discovery
    if (MDNS.begin(deviceName)) {
        Serial.println("mDNS responder started");
        MDNS.addService("http", "tcp", 80);  // Advertise HTTP service on port 80
    } else {
        Serial.println("Error starting mDNS");
    }
    synchronizeTimeWithNTP();
    initializeSDCard();
    setupI2S();
    setupES8388();
    udp.beginMulticast(multicastAddress, multicastPort);
    Serial.printf("Listening for multicast on port %d\n", multicastPort);
    setupOTA();
    startWebServer();
}

void loop() {
    ArduinoOTA.handle();
    handleWebServerTasks();  
    handleUDPCommands(); 
    if (isRecording) {
        recordAudio();
    }
}
