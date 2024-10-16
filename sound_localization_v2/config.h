#ifndef CONFIG_H
#define CONFIG_H

// WiFi credentials
const char* ssid = "TEST";          // Replace with your Wi-Fi SSID
const char* password = "TEST";  // Replace with your Wi-Fi password
const char* otaPassword = "2357"; // Replace with your OTA password

// NTP Server Configuration
const char* ntpServer = "pool.ntp.org";
const long gmtOffset_sec = 3600;  // Adjust to your timezone
const int daylightOffset_sec = 0;

// Multicast Configuration
const char* multicastAddress = "239.0.0.1";
const unsigned int multicastPort = 12345;

// Device Information
const char* deviceName = "ESP32_Audio_Device";

#endif // CONFIG_H
