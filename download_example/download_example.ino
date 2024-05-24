#include <WiFi.h>
#include <ESPAsyncWebServer.h>
#include <FS.h>
#include <SD.h>
#include <SPI.h>

// Replace with your network credentials
const char* ssid = "EwoutBergsma";
const char* password = "EwoutBergsma";

// Chip Select pin for SD card
#define CS_PIN 5

// Create AsyncWebServer object on port 80
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

void setup() {
  // Start Serial communication
  Serial.begin(115200);

  // Initialize SD card
  if (!SD.begin(CS_PIN)) {
    Serial.println("Card Mount Failed");
    return;
  }

  // Connect to Wi-Fi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");

  // Print the IP address
  Serial.println("IP Address: ");
  Serial.println(WiFi.localIP());

  // Serve the HTML page
  server.on("/", HTTP_GET, [](AsyncWebServerRequest *request){
    request->send_P(200, "text/html", index_html);
  });

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
  // Nothing to do here
}