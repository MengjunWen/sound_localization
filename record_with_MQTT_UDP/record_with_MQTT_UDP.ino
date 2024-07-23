#include <driver/i2s.h>
#include <FS.h>
#include <SD.h>
#include <SPI.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ESPAsyncWebServer.h>
#include <WiFiUdp.h>

//Test 23-07-2024
// WiFi credentials
const char* ssid = "EwoutBergsma";
const char* password = "EwoutBergsma";

// Multicast settings
IPAddress multicastAddress(239, 255, 255, 250);  // Multicast address
const int multicastPort = 12345;  // Multicast port

WiFiUDP udp;
// MQTT Server
const char* mqtt_server = "192.168.0.155";
const int mqtt_port = 1883;

WiFiClient espClient;
PubSubClient client(espClient);
AsyncWebServer server(80);


// HTML content
const char index_html[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Download File</title>
</head>
<body>
    <h1>Download Test File</h1>
    <button id="downloadBtn" onclick="downloadFile()">Download</button>

    <script>
        function downloadFile() {
            const fileName = prompt("Enter the name of the file to download:");
            if (fileName) {
                window.location.href = "/download?file=" + encodeURIComponent(fileName);
            }
        }
    </script>
</body>
</html>
)rawliteral";


File myFile;
bool isRecording = false;
bool doneRecording = false;
bool start = false;
bool createFile = true;
const char* pub_ip = "ESP32_1/ip";
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
int countdown = 10;

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
    if (client.connect("ESP32_1")) {
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
  // Start UDP
  udp.beginMulticast(multicastAddress, multicastPort);
  // start up the I2S peripheral
  Serial.println("Setup I2S ...");
  i2s_install();
  i2s_setpin();
  i2s_start(I2S_NUM_0);
  pinMode(2, OUTPUT);
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
    // Route to download a file
  server.on("/download", HTTP_GET, [](AsyncWebServerRequest *request){
    if (request->hasParam("file")) {
      String fileName = request->getParam("file")->value();
      if (SD.exists("/" + fileName)) {
        request->send(SD, "/" + fileName, "application/octet-stream");
      } else {
        request->send(404, "text/plain", "File not found");
      }
    } else {
      request->send(400, "text/plain", "File parameter missing");
    }
  });
  server.on("/delete", HTTP_GET, [](AsyncWebServerRequest *request){
  if (request->hasParam("file")) {
    String fileName = request->getParam("file")->value();
    if (SD.exists("/" + fileName)) {
      if (SD.remove("/" + fileName)) {
        request->send(200, "text/plain", "File deleted successfully");
      } else {
        request->send(500, "text/plain", "Failed to delete file");
      }
    } else {
      request->send(404, "text/plain", "File not found");
    }
  } else {
    request->send(400, "text/plain", "File parameter missing");
  }
});
server.on("/list", HTTP_GET, [](AsyncWebServerRequest *request){
  File root = SD.open("/");
  if (!root) {
    request->send(500, "application/json", "{\"error\":\"Failed to open directory\"}");
    return;
  }

  if (!root.isDirectory()) {
    request->send(500, "application/json", "{\"error\":\"Not a directory\"}");
    return;
  }

  String jsonResponse = "[";
  File file = root.openNextFile();
  bool first = true;
  while (file) {
    if (!first) {
      jsonResponse += ",";
    }
    jsonResponse += "\"" + String(file.name()) + "\"";
    first = false;
    file = root.openNextFile();
  }
  jsonResponse += "]";
  
  request->send(200, "application/json", jsonResponse);
});


  // Start server
  server.begin();
}


void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  if (doneRecording) {
    digitalWrite(2, LOW);
    myFile.close();
    doneRecording = false;
    start = false;
    Serial.println("Recording finished and file closed.");
  };
  if (createFile) {
    String filename = createFilename();
    myFile = SD.open(filename.c_str(), FILE_WRITE);
    createFile = false;
  };
  if (start) {

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
  int packetSize = udp.parsePacket();
  if (packetSize) {
    //Serial.printf("Received packet of size %d from %s:%d\n", packetSize, udp.remoteIP().toString().c_str(), udp.remotePort());
    //digitalWrite(2, !digitalRead(2));
    char incomingPacket[255];
    int len = udp.read(incomingPacket, 255);
    if (len > 0) {
      incomingPacket[len] = 0;
    }
    Serial.printf("Start recoding in: %s\n", incomingPacket);
    countdown = atoi(incomingPacket);
    if ((countdown == 0) and (isRecording)){
      start = true;
      digitalWrite(2, HIGH);
    }
  }
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
