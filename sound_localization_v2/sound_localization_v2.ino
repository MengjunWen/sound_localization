#include <WiFi.h>
#include <WiFiUdp.h>
#include <ESPmDNS.h>
#include <ESP32Time.h>
#include "config.h"
#include "OTAUpdate.h"
#include "AudioControl.h"

WiFiUDP udp;
ESP32Time rtc;
bool isRecording = false;
WiFiServer server(80);

void connectToWiFi() {
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nConnected to WiFi");
}

void setup() {
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

    // Synchronize time with NTP server
    synchronizeTimeWithNTP();

    // Initialize SD card and I2S setup
    initializeSDCard();
    setupI2S();

    // Setup UDP multicast listener
    udp.beginMulticast(WiFi.localIP(), multicastPort);
    Serial.printf("Listening for multicast on port %d\n", multicastPort);

    // Setup OTA functionality
    setupOTA();

    // Start the web server to serve files for download
    startWebServer();
}

void loop() {
    // Handle OTA updates
    ArduinoOTA.handle();

    // Handle UDP commands for synchronized recording
    handleUDPCommands();

    // Continuously record audio if recording is active
    if (isRecording) {
        recordAudio();
    }
}
