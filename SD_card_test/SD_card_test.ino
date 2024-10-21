#include "FS.h"
#include "SD.h"
#include "SPI.h"

// Define the GPIO pins used for the SD card
#define SD_CS_PIN    21   // Chip Select (CS) pin, adjust based on your board
#define SD_MISO_PIN  12  // MISO pin
#define SD_MOSI_PIN  13  // MOSI pin
#define SD_SCLK_PIN  14  // Clock pin

void setup() {
  // Initialize serial communication for debugging
  Serial.begin(115200);
  Serial.println("Starting");
  for(int i = 0; i < 10; i++){
    delay(1000);
    Serial.println("...");
  }
  
  // Initialize the SPI bus manually with custom pin assignment
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

void loop() {
  // Your logic here
}

