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

// External declarations for variables used in the main sketch
extern ESP32Time rtc;
extern bool isRecording;
extern WiFiUDP udp;
extern WiFiServer server;

File audioFile;

// SPI pin definitions for SD card
#define SD_CS 5  // Chip select pin for SD card (you can change this if needed)

// I2S setup for audio recording
void setupI2S() {
    i2s_config_t i2s_config = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
        .sample_rate = 16000,
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
        .bck_io_num = 26,     // Bit Clock pin
        .ws_io_num = 25,      // Word Select (L/R clock) pin
        .data_out_num = -1,   // Data Out not used in RX mode
        .data_in_num = 35     // Data In pin
    };

    i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL);
    i2s_set_pin(I2S_NUM_0, &pin_config);
    Serial.println("I2S setup completed");
}

// Initialize the SD card using SPI mode
void initializeSDCard() {
    if (!SD.begin(SD_CS)) {
        Serial.println("SD Card Mount Failed");
        return;
    }

    uint8_t cardType = SD.cardType();
    if (cardType == CARD_NONE) {
        Serial.println("No SD card attached");
        return;
    }

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

    uint64_t cardSize = SD.cardSize() / (1024 * 1024);
    Serial.printf("SD Card Size: %lluMB\n", cardSize);
    Serial.println("SD Card initialized successfully");
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

// Record audio data
void recordAudio() {
    uint8_t i2sData[512];
    size_t bytesRead = 0;
    i2s_read(I2S_NUM_0, (void*)i2sData, sizeof(i2sData), &bytesRead, portMAX_DELAY);
    if (bytesRead > 0 && audioFile) {
        audioFile.write(i2sData, bytesRead);
    }
}

// Start audio recording
void startRecording() {
    String fileName = "/recording_" + String(rtc.getEpoch()) + ".wav";
    audioFile = SD.open(fileName, FILE_WRITE);
    if (audioFile) {
        isRecording = true;
        Serial.println("Recording started...");
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
    }
}

// Handle UDP commands for starting and stopping the recording
void handleUDPCommands() {
    int packetSize = udp.parsePacket();
    if (packetSize) {
        char incomingPacket[255];
        int len = udp.read(incomingPacket, 255);
        if (len > 0) {
            incomingPacket[len] = 0;
        }

        String packet = String(incomingPacket);
        if (packet == "START_RECORDING") {
            startRecording();
        } else if (packet == "STOP_RECORDING") {
            stopRecording();
        }
    }
}

// Serve files over HTTP for download
void startWebServer() {
    server.begin();
    Serial.println("HTTP server started");

    while (true) {
        WiFiClient client = server.available();
        if (client) {
            String request = client.readStringUntil('\r');
            client.flush();

            // Handle the list files request
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
            } else if (request.indexOf("GET /") >= 0) {
                // Handle file download request
                String fileName = request.substring(5, request.indexOf(" ", 5));
                fileName = "/" + fileName; // Ensure the file path is correct
                if (SD.exists(fileName)) {
                    File downloadFile = SD.open(fileName, FILE_READ);
                    client.println("HTTP/1.1 200 OK");
                    client.println("Content-Type: application/octet-stream");
                    client.println("Connection: close");
                    client.println();

                    while (downloadFile.available()) {
                        client.write(downloadFile.read());
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
}

#endif // AUDIO_CONTROL_H
