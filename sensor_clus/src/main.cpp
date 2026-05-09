#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include "DHT.h"

// --- Wi-Fi Credentials ---
const char* ssid = "LAB-06";
const char* password = "1234567890";

// --- Pin Definitions (Single-Side Mapping) ---
#define DHTPIN 27         
#define DHTTYPE DHT11
#define MQ7_ANALOG_PIN 34 
#define DUST_LED_PIN 26   
#define DUST_OUT_PIN 35   

// --- Global Variables & Objects ---
DHT dht(DHTPIN, DHTTYPE);
WebServer server(80);

// --- Circular Buffer Setup (The Queue) ---
const int MAX_HISTORY = 30; // Maximum number of readings to store

// A structure to hold a single "snapshot" of all sensors at once
struct SensorData {
  float temperature;
  float humidity;
  int mq7;
  float pm25;
};

SensorData dataHistory[MAX_HISTORY]; // The fixed-size array
int head = 0;  // Tracks where to write the NEXT piece of data
int count = 0; // Tracks how many items are currently in the array

// --- GP2Y1010 Read Function ---
float readDustSensor() {
  digitalWrite(DUST_LED_PIN, LOW); 
  delayMicroseconds(280);
  int voMeasured = analogRead(DUST_OUT_PIN); 
  delayMicroseconds(40);
  digitalWrite(DUST_LED_PIN, HIGH); 
  delayMicroseconds(9680);

  float calcVoltage = voMeasured * (3.3 / 4095.0);
  float density = 170 * calcVoltage - 0.1;
  return (density < 0) ? 0.0 : density;
}

// --- HTML Dashboard Generation ---
void handleRoot() {
  String html = "<!DOCTYPE html><html><head><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">";
  html += "<title>Air Quality Dashboard</title>";
  html += "<style>body { font-family: Arial, sans-serif; text-align: center; background-color: #f4f4f9; padding: 20px; }";
  html += ".card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); display: inline-block; margin: 10px; width: 250px; }";
  html += "h1 { color: #333; } h2 { color: #007BFF; margin: 5px 0; } p { color: #666; font-size: 1.2em; }</style>";
  
  // Updated Script: It fetches the array of 30 items, and grabs the last one to show on screen
  html += "<script>setInterval(() => { fetch('/api/data').then(r => r.json()).then(dataList => {";
  html += "if (dataList.length > 0) {";
  html += "  let latest = dataList[dataList.length - 1];"; // Get the newest data point
  html += "  document.getElementById('temp').innerText = latest.t + ' &deg;C';";
  html += "  document.getElementById('hum').innerText = latest.h + ' %';";
  html += "  document.getElementById('co').innerText = latest.mq + ' / 4095';";
  html += "  document.getElementById('dust').innerText = latest.pm + ' ug/m3';";
  html += "} }); }, 3000);</script></head><body>";
  
  html += "<h1>ESP32 Air Quality Monitor</h1>";
  html += "<div class='card'><h2>Temperature</h2><p id='temp'>-- &deg;C</p></div>";
  html += "<div class='card'><h2>Humidity</h2><p id='hum'>-- %</p></div>";
  html += "<div class='card'><h2>CO Level (MQ-7)</h2><p id='co'>-- / 4095</p></div>";
  html += "<div class='card'><h2>PM2.5 (GP2Y1010)</h2><p id='dust'>-- ug/m3</p></div>";
  html += "</body></html>";
  
  server.send(200, "text/html", html);
}

// --- JSON API Endpoint (Exports the Queue) ---
void handleApiData() {
  String json = "["; // Start JSON array
  
  // Loop through the circular buffer from oldest to newest
  for (int i = 0; i < count; i++) {
    // Math trick to find the oldest item index, wrapping around the array bounds
    int idx = (head + MAX_HISTORY - count + i) % MAX_HISTORY;
    
    json += "{";
    json += "\"t\":" + String(dataHistory[idx].temperature) + ",";
    json += "\"h\":" + String(dataHistory[idx].humidity) + ",";
    json += "\"co\":" + String(dataHistory[idx].mq7) + ",";
    json += "\"pm\":" + String(dataHistory[idx].pm25);
    json += "}";
    
    // Add a comma between items, but not after the very last one
    if (i < count - 1) {
      json += ",";
    }
  }
  json += "]"; // End JSON array
  
  server.send(200, "application/json", json);
}

void setup() {
  Serial.begin(115200);
  
  pinMode(DUST_LED_PIN, OUTPUT);
  digitalWrite(DUST_LED_PIN, HIGH);
  dht.begin();

  Serial.print("Connecting to Wi-Fi");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected! IP Address: ");
  Serial.println(WiFi.localIP());

  server.on("/", handleRoot);
  server.on("/api/data", handleApiData);
  server.begin();
}

void loop() {
  server.handleClient();

  // Read sensors every 2 seconds
  static unsigned long lastRead = 0;
  if (millis() - lastRead > 2000) {
    lastRead = millis();
    
    float t = dht.readTemperature();
    float h = dht.readHumidity();
    int mq = analogRead(MQ7_ANALOG_PIN);
    float pm = readDustSensor();
    
    if (isnan(t) || isnan(h)) {
      Serial.println("Failed to read from DHT sensor!");
    } else {
      // --- ADD DATA TO CIRCULAR QUEUE ---
      // Save current readings at the 'head' position
      dataHistory[head].temperature = t;
      dataHistory[head].humidity = h;
      dataHistory[head].mq7 = mq;
      dataHistory[head].pm25 = pm;
      
      // Move head forward by 1. If it hits 30, wrap back to 0.
      head = (head + 1) % MAX_HISTORY;
      
      // Keep track of total items, capping at 30.
      if (count < MAX_HISTORY) {
        count++;
      }
      
      Serial.printf("Queue Size: %d/30 | Temp: %.1f C\n", count, t);
    }
  }
}