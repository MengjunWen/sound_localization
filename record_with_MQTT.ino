#include <driver/i2s.h>
#include <SD.h>
#include <SPI.h>
#include <WiFi.h>
#include <PubSubClient.h>

#include <AsyncTCP.h>
#include <ESPAsyncWebServer.h>

// WiFi credentials
const char* ssid = "EwoutBergsma";
const char* password = "EwoutBergsma";

// MQTT Server
const char* mqtt_server = "192.168.0.155";
const int mqtt_port = 1883;

WiFiClient espClient;
PubSubClient client(espClient);
AsyncWebServer server(80);

File myFile;
bool isRecording = false;
bool doneRecording = false;
bool createFile = true;
const char* pub_ip = "ESP32_3/ip";
//for recording sample
#define sBuffer 64 
#define SAMPLE_RATE 20000
//for i2s mic
#define I2S_WS 22
#define I2S_SD 21
#define I2S_SCK 26
// Chip Select pin for SD card
#define CS_PIN 5 
int16_t raw_samples[sBuffer];

void setup_wifi() {
  delay(10);
  Serial.println("Connecting to WiFi..");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

void callback(char* topic, byte* message, unsigned int length) {
  Serial.print("Message arrived on topic: ");
  bool value = (message[0] == '1');
  if ((isRecording == !value)&&(isRecording)){
    doneRecording = true;
    createFile = true;
    };
  if (isRecording != value){
    isRecording = value;
    };
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect("ESP32_3")) {
      Serial.println("connected");
      client.subscribe("record");
      client.publish(pub_ip, WiFi.localIP().toString().c_str());
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void setup() {  
  // we need serial output for the plotter
  Serial.begin(115200);
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
  // start up the I2S peripheral
  Serial.println("Setup I2S ...");
  i2s_install();
  i2s_setpin();
  i2s_start(I2S_NUM_0);
  // Check for SD card initialization
  SPI.begin();
  SD.begin(CS_PIN);
  if (!SD.begin(CS_PIN)) {
    Serial.println("Card Mount Failed");
    return;
  }
  uint8_t cardType = SD.cardType();
  if (cardType == CARD_NONE) {
    Serial.println("No SD card attached");
    return;
  }
  Serial.println("SD Card initialized.");
  server.on("/download/{file}", HTTP_GET, [](AsyncWebServerRequest *request) {
    String filename = "/" + request->pathArg(0);
    if (SD.exists(filename)) {
      request->send(SD, filename, "text/plain", true);
    } else {
      request->send(404, "text/plain", "File not found");
    }
  });

  server.begin();
}


void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  if (doneRecording) {
    myFile.close();
    doneRecording = false;
    Serial.println("Recording finished and file closed.");
  };
  if (createFile) {
    String filename = createFilename();
    myFile = SD.open(filename.c_str(), FILE_WRITE);
    createFile = false;
  };
  if (isRecording) {
    size_t bytesIn = 0;
    i2s_read(I2S_NUM_0, &raw_samples, sBuffer, &bytesIn, portMAX_DELAY);//raw_samples读取数据的目标地址。
    int samples_read = bytesIn / sizeof(int16_t) ;//bytesIn是读取字节数,sample
    if (samples_read > 0) {
      float mean = 0;
      for (int i = 0; i < samples_read; ++i) {
        myFile.println((int)raw_samples[i]);
      }
    }
  };
}

void i2s_install(){
  const i2s_config_t i2s_config = {
    //.mode = i2s_mode_t(I2S_MODE_MASTER | I2S_MODE_RX),
    .mode = i2s_mode_t(I2S_MODE_MASTER | I2S_MODE_TX | I2S_MODE_RX),//没有太大区别
    .sample_rate = SAMPLE_RATE,
    .bits_per_sample = i2s_bits_per_sample_t(16),
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = i2s_comm_format_t(I2S_COMM_FORMAT_STAND_I2S),
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1, // default interrupt priority
    .dma_buf_count = 4,
    .dma_buf_len = 1024,
    .use_apll = false
  };
  i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL);
}

void i2s_setpin(){
  const i2s_pin_config_t pin_config = {
    .bck_io_num = I2S_SCK,
    .ws_io_num = I2S_WS,
    .data_out_num = -1,// not used (only for speakers)
    .data_in_num = I2S_SD
  };
  i2s_set_pin(I2S_NUM_0, &pin_config);
}

String createFilename() {
  static int fileNumber = 0;  // Static variable to increment filename
  fileNumber++;
  return "/recording" + String(fileNumber) + ".txt";
}
