#ifndef AUDIO_CONTROL_H
#define AUDIO_CONTROL_H

#include <WiFi.h>
#include <WiFiUdp.h>
#include <ESPmDNS.h>
#include <SD.h>
#include <SPI.h>
#include <ESP32Time.h>
#include "driver/i2s.h"
#include "config.h"
#include "ES8388.h"

#define LED_PIN 2

// External declarations for variables used in the main sketch
extern ESP32Time rtc;
extern bool isRecording;
extern WiFiUDP udp;
extern WiFiServer server;

File audioFile;

// SPI pin definitions for SD card
#define SD_CS_PIN    21   // Chip Select (CS) pin, adjust based on your board
#define SD_MISO_PIN  12  // MISO pin
#define SD_MOSI_PIN  13  // MOSI pin
#define SD_SCLK_PIN  14  // Clock pin

// Global Variables for scheduling
bool scheduledRecording = false;
time_t startTime = 0;
time_t stopTime = 0;

ES8388 es8388(18, 23, 400000);
size_t readsize = 0;
uint16_t rxbuf[256], txbuf[256];

// Helper function to parse time from string "hh:mm:ss"
time_t parseTime(String timeStr) {
    int hours = timeStr.substring(0, 2).toInt();
    int minutes = timeStr.substring(3, 5).toInt();
    int seconds = timeStr.substring(6, 8).toInt();
    return hours * 3600 + minutes * 60 + seconds; // Convert to seconds from midnight
}

// I2S setup for audio recording
void setupI2S() {
    i2s_config_t i2s_config = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX | I2S_MODE_RX),
        .sample_rate = 44100,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
        .channel_format = I2S_CHANNEL_FMT_RIGHT_LEFT,
        .communication_format = I2S_COMM_FORMAT_I2S_MSB,
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count = 8,
        .dma_buf_len = 64,
        .use_apll = false,
        .tx_desc_auto_clear = true,
        .fixed_mclk = 0
    };
    
    i2s_pin_config_t pin_config = {
        .mck_io_num = 0,     // Master Clock pin
        .bck_io_num = 5,     // Bit Clock pin
        .ws_io_num = 25,      // Word Select (L/R clock) pin
        .data_out_num = 26,   // Data Out not used in RX mode
        .data_in_num = 35     // Data In pin
    };

    i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL);
    i2s_set_pin(I2S_NUM_0, &pin_config);
    Serial.println("I2S setup completed");
}

void setupES8388() {
    es8388.init();
    es8388.inputSelect(IN1);
    es8388.setInputGain(8);
    es8388.outputSelect(OUT1);
    es8388.setOutputVolume(12);
    es8388.mixerSourceSelect(MIXADC, MIXADC);
    es8388.mixerSourceControl(DACOUT);
    Serial.println("ES8388 setup completed");
}

// Initialize the SD card using SPI mode
void initializeSDCard() {
    SPI.begin(SD_SCLK_PIN, SD_MISO_PIN, SD_MOSI_PIN, SD_CS_PIN);
    // Initialize the SD card
    if (!SD.begin(SD_CS_PIN, SPI)) {
      Serial.println("Card Mount Failed");
      return;
    }
    // Retrieve card information
    uint8_t cardType = SD.cardType();

    if (cardType == CARD_NONE) {
      Serial.println("No SD card attached");
      return;
    }
    // Print card type
    Serial.print("SD Card Type: ");
    if (cardType == CARD_MMC) {
      Serial.println("MMC");
    } else if (cardType == CARD_SD) {
      Serial.println("SDSC");
    } else if (cardType == CARD_SDHC) {
      Serial.println("SDHC");
    } else {
      Serial.println("UNKNOWN");
    }
    // Print card size
    uint64_t cardSize = SD.cardSize() / (1024 * 1024);
    Serial.printf("SD Card Size: %lluMB\n", cardSize);
}

void eraseDirectory(File dir, const String& path = "/") {
  if (!dir) {
    Serial.println("Failed to open directory");
    return;
  }

 while (true) {
        File entry = dir.openNextFile();
        if (!entry) {
            break; // No more files
        }

        String entryPath = path + entry.name();
        
        if (entry.isDirectory()) {
            // Recursively erase subdirectory contents
            // eraseDirectory(entry, entryPath + "/"); 
            // SD.rmdir(entryPath.c_str()); // Remove the empty directory
        } else {
            // Only delete the file if it ends with ".wav"
            if (entryPath.endsWith(".wav")) {
                if (SD.remove(entryPath.c_str())) {
                    Serial.print("Deleted .wav file: ");
                    Serial.println(entryPath);
                } else {
                    Serial.print("Failed to delete .wav file: ");
                    Serial.println(entryPath);
                }
            }
        }
        entry.close();
    }
    dir.close();
}

void eraseSD() {
  Serial.println("test");
  File root = SD.open("/");
  if (!root) {
    Serial.println("Failed to open root directory");
    return;
  }
  Serial.println("test2");
  eraseDirectory(root);
  Serial.println("SD card erased");
}

void recordAudio() {
    // uint8_t i2sData[512];
    // size_t bytesRead = 0;
    // i2s_read(I2S_NUM_0, (void*)i2sData, sizeof(i2sData), &bytesRead, portMAX_DELAY);
    // if (bytesRead > 0 && audioFile) {
    //     audioFile.write(i2sData, bytesRead);
    // }
    long long sum = 0;
    int read_result = i2s_read(I2S_NUM_0, &rxbuf[0], 256 * 2, &readsize, 1000);
    if (read_result != ESP_OK) {
        Serial.printf("i2s_read error: %d\n", read_result);
    }
    // for (int i = 0; i < readsize / 2; i++) {
    //     sum += rxbuf[i];
    // }
    // Serial.println(sum);
    if (readsize > 0 && audioFile) {
        audioFile.write((uint8_t *)rxbuf, readsize);
    }
}

void startRecording() {
    String fileName = "/"+ String(deviceName) + "_" + String(rtc.getEpoch()) + ".bin";
    audioFile = SD.open(fileName, FILE_WRITE);
    if (audioFile) {
        isRecording = true;
        Serial.println("Recording started...");
        digitalWrite(LED_PIN, HIGH);  // Turn on the built-in LED
    } else {
        Serial.println("Failed to open file for recording");
    }
}

// Stop audio recording
void stopRecording() {
    if (audioFile) {
        isRecording = false;
        audioFile.close();
        Serial.println("Recording stopped and file saved.");
        digitalWrite(LED_PIN, LOW);  // Turn off the built-in LED
    }
}

// Print current time in HH:MM:SS format
void printCurrentTime() {
    String currentTime = rtc.getTime("%H:%M:%S");
    Serial.println("Current time: " + currentTime);
}

// Check if it's time to start or stop recording
void checkRecordingSchedule() {
    time_t currentTime = rtc.getEpoch(); // Assuming rtc.getEpoch() returns seconds since midnight
    //printCurrentTime();  // Print the current time to the Serial Monitor
    if (scheduledRecording) {
        if (currentTime >= startTime && currentTime < stopTime && !isRecording) {
            startRecording();
        }
        if (currentTime >= stopTime && isRecording) {
            stopRecording();
            scheduledRecording = false; // Reset scheduling after stopping
        }
    }
}

// Handle HTTP requests for scheduling recording
void handleWebServer() {
    WiFiClient client = server.available();
    if (client) {
        String request = client.readStringUntil('\r');
        client.flush();
        if (request.indexOf("GET /list") >= 0) {
                client.println("HTTP/1.1 200 OK");
                client.println("Content-Type: application/json");
                client.println("Connection: close");
                client.println();

                client.print("[");
                File root = SD.open("/");
                File file = root.openNextFile();
                bool firstFile = true;
                while (file) {
                    if (!firstFile) {
                        client.print(",");
                    }
                    client.print("\"");
                    client.print(file.name());
                    client.print("\"");
                    firstFile = false;
                    file = root.openNextFile();
                }
                client.print("]");
                root.close();
            } 
            else if (request.indexOf("GET /start") >= 0){
                client.println("HTTP/1.1 200 OK");
                client.println("Content-Type: application/json");
                client.println("Connection: close");
                client.println();
                client.println("{\"status\": \"Recording started\"}");
                startRecording();
                root.close();
            }
            else if (request.indexOf("GET /stop") >= 0){
                client.println("HTTP/1.1 200 OK");
                client.println("Content-Type: application/json");
                client.println("Connection: close");
                client.println();
                client.println("{\"status\": \"Recording stopped\"}");
                stopRecording();
                root.close();
            }
            else if (request.indexOf("GET /") >= 0) {
                // Handle file download request
                String fileName = request.substring(5, request.indexOf(" ", 5));
                fileName = "/" + fileName; // Ensure the file path is correct
                if (SD.exists(fileName)) {
                    File downloadFile = SD.open(fileName, FILE_READ);
                    client.println("HTTP/1.1 200 OK");
                    client.println("Content-Type: application/octet-stream");
                    client.println("Connection: close");
                    client.println();
                    uint8_t buffer[2048];
                    while (downloadFile.available()) {
                        int bytesRead = downloadFile.read(buffer, sizeof(buffer));
                        client.write(buffer, bytesRead);  // Send the whole buffer at once
                    }
                    downloadFile.close();
                } else {
                    client.println("HTTP/1.1 404 Not Found");
                    client.println("Content-Type: text/html");
                    client.println();
                    client.println("<h1>File Not Found</h1>");
                }
            }
            client.stop();
    }
}

// Start HTTP server and handle requests
void startWebServer() {
    server.begin();
    Serial.println("HTTP server started");
}

// This function should be called in the main loop
void handleWebServerTasks() {
    handleWebServer();           // Handle any incoming HTTP requests
    //checkRecordingSchedule();     // Check if recording needs to be scheduled
}

// Synchronize time with NTP server
void synchronizeTimeWithNTP() {
    configTime(gmtOffset_sec, daylightOffset_sec, ntpServer);
    struct tm timeinfo;
    if (getLocalTime(&timeinfo)) {
        rtc.setTimeStruct(timeinfo);
        Serial.println("Time synchronized with NTP server");
    } else {
        Serial.println("Failed to obtain time from NTP server");
    }
}

// Function to handle incoming UDP packets and execute commands
void handleUDPCommands() {
    int packetSize = udp.parsePacket();  // Check if there is an incoming packet

    if (packetSize > 0) {
        char incomingPacket[255];  // Buffer to hold incoming packet
        int len = udp.read(incomingPacket, 255);  // Read the packet into the buffer
        if (len > 0) {
            incomingPacket[len] = '\0';  // Null-terminate the packet string
        }

        // Convert packet to String and print it
        String packet = String(incomingPacket);
        Serial.println("Received UDP packet: " + packet);

        // Basic command handling
        if (packet.equals("START_RECORDING")) {
            startRecording();
        } else if (packet.equals("STOP_RECORDING")) {
            stopRecording();
        } else if (packet.equals("ERASE_SD")) {
            eraseSD();
        } 
        else {
            Serial.println("Unknown command received.");
        }
    }
    
}

#endif // AUDIO_CONTROL_H
