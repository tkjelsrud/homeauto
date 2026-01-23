#include <Arduino.h>
#include <SPI.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <time.h>
#include <ArduinoJson.h>
#include <GxEPD2_BW.h>
#include <Fonts/FreeMonoBold24pt7b.h>
#include <Fonts/FreeMonoBold18pt7b.h>
#include <Fonts/FreeMonoBold12pt7b.h>
#include <Fonts/FreeMonoBold9pt7b.h>
#include "config.h"
#include "icons.h"

// Waveshare 7.50inv2 display
#define EPD_CS      10  // ESP_IO10/SCREEN_CS#
#define EPD_DC      11  // ESP_IO11/SCREEN_DC#
#define EPD_RST     12  // ESP_IO12/SCREEN_RST#
#define EPD_BUSY    13  // ESP_IO13/SCREEN_BUSY# (inverted)
// SPI pins: SCK=GPIO7, MOSI=GPIO9
#define EPD_SCK     7   // ESP_IO7/SCK
#define EPD_MOSI    9   // ESP_IO9/MOSI

// Display: 7.5" 800x480 Waveshare 7.50inv2
GxEPD2_BW<GxEPD2_750_T7, GxEPD2_750_T7::HEIGHT> display(GxEPD2_750_T7(EPD_CS, EPD_DC, EPD_RST, EPD_BUSY));

unsigned long lastUpdate = 0;
unsigned long lastWiFiCheck = 0;
const unsigned long WIFI_RETRY_INTERVAL = 60000; // 60 seconds
struct tm timeinfo;

#define CALENDAR_DOC_SIZE 4096

// Function prototypes
void syncTime();
void connectWiFi();
bool fetchWeatherData(JsonDocument& doc);
bool fetchCalendarData(JsonDocument& doc);
bool fetchAirthingsData(JsonDocument& doc);
void displayWeather(JsonDocument& doc);
void displayCalendar(JsonDocument& doc);

void syncTime() {
  configTime(3600, 3600, "pool.ntp.org", "time.nist.gov"); // UTC+1 + DST
  Serial.print("Syncing time");
  int attempts = 0;
  while (!getLocalTime(&timeinfo) && attempts < 10) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  if (attempts < 10) {
    Serial.println("\nTime synced!");
  } else {
    Serial.println("\nTime sync failed");
  }
}

void connectWiFi() {
  Serial.print("Connecting to WiFi");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nWiFi connection failed!");
  }
}

bool fetchWeatherData(JsonDocument& doc) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected");
    return false;
  }
  
  HTTPClient http;
  http.begin(WEATHER_ENDPOINT);
  
  int httpCode = http.GET();
  
  if (httpCode == HTTP_CODE_OK) {
    String payload = http.getString();
    Serial.println("Weather data received:");
    Serial.println(payload);
    
    DeserializationError error = deserializeJson(doc, payload);
    
    if (error) {
      Serial.print("JSON parsing failed: ");
      Serial.println(error.c_str());
      http.end();
      return false;
    }
    
    http.end();
    return true;
  } else {
    Serial.print("HTTP GET failed, error: ");
    Serial.println(httpCode);
    http.end();
    return false;
  }
}

bool fetchCalendarData(JsonDocument& doc) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected");
    return false;
  }
  HTTPClient http;
  http.begin(CALENDAR_ENDPOINT);
  int httpCode = http.GET();
  if (httpCode == HTTP_CODE_OK) {
    String payload = http.getString();
    Serial.println("Calendar data received:");
    Serial.println(payload);
    DeserializationError error = deserializeJson(doc, payload);
    if (error) {
      Serial.print("Calendar JSON parsing failed: ");
      Serial.println(error.c_str());
      http.end();
      return false;
    }
    http.end();
    return true;
  } else {
    Serial.print("HTTP GET failed, error: ");
    Serial.println(httpCode);
    http.end();
    return false;
  }
}

bool fetchAirthingsData(JsonDocument& doc) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected");
    return false;
  }
  HTTPClient http;
  http.begin(AIRTHINGS_ENDPOINT);
  http.setTimeout(25000); // 25 second timeout for slow Bluetooth response
  Serial.println("Fetching Airthings data (may take 10-20 seconds)...");
  int httpCode = http.GET();
  if (httpCode == HTTP_CODE_OK) {
    String payload = http.getString();
    Serial.println("Airthings data received:");
    Serial.println(payload);
    DeserializationError error = deserializeJson(doc, payload);
    if (error) {
      Serial.print("Airthings JSON parsing failed: ");
      Serial.println(error.c_str());
      http.end();
      return false;
    }
    http.end();
    return true;
  } else {
    Serial.print("Airthings HTTP GET failed, error: ");
    Serial.println(httpCode);
    http.end();
    return false;
  }
}

void displayCalendar(JsonDocument& doc) {
  // Get current weekday (0=Monday, 6=Sunday)
  int todayIdx = -1, tomorrowIdx = -1;
  if (getLocalTime(&timeinfo)) {
    todayIdx = (timeinfo.tm_wday + 6) % 7; // tm_wday: 0=Sunday, 1=Monday...
    tomorrowIdx = (todayIdx + 1) % 7;
  }
  JsonArray days = doc["data"].as<JsonArray>();
  int y = 40;
  for (int i = 0; i < days.size(); ++i) {
    int idx = days[i]["weekday_index"] | -1;
    if (idx != todayIdx && idx != tomorrowIdx) continue;
    // Header: Day name
    display.setFont(&FreeMonoBold18pt7b);
    display.setCursor(280, y);
    display.print((const char*)days[i]["name"]);
    y += 30;
    // Dinner
    display.setFont(&FreeMonoBold9pt7b);
    display.setCursor(280, y);
    display.print("Middag: ");
    display.print((const char*)days[i]["dinner"]);
    y += 20;
    // Events today
    JsonArray events = days[i]["events"].as<JsonArray>();
    if (events.size() > 0) {
      display.setCursor(280, y);
      display.print("Hendelser:");
      y += 18;
      for (JsonObject ev : events) {
        if (ev["is_next_week"]) continue;
        display.setCursor(290, y);
        const char* start = ev["start"] | "";
        const char* summary = ev["summary"] | "";
        if (strlen(start) > 11) display.print(&start[11]); // print time only
        display.print(" ");
        display.print(summary);
        y += 16;
      }
    }
    // Next week events
    bool hasNextWeek = false;
    for (JsonObject ev : events) if (ev["is_next_week"]) hasNextWeek = true;
    if (hasNextWeek) {
      display.setCursor(280, y);
      display.print("Neste uke:");
      y += 18;
      for (JsonObject ev : events) {
        if (!ev["is_next_week"]) continue;
        display.setCursor(290, y);
        const char* start = ev["start"] | "";
        const char* summary = ev["summary"] | "";
        if (strlen(start) > 11) display.print(&start[11]);
        display.print(" ");
        display.print(summary);
        y += 16;
      }
    }
    // Timeplaner
    if (!days[i]["timeplaner"].isNull()) {
      display.setCursor(280, y);
      display.print("Timeplan:");
      y += 16;
      JsonObject tp = days[i]["timeplaner"].as<JsonObject>();
      
      // Collect all students and their lessons
      String students[2];
      JsonArray lessons[2];
      int studentCount = 0;
      
      for (JsonPair kv : tp) {
        if (studentCount < 2) {
          // Remove prefix (4a_, 6b_, etc.) from name
          String fullName = String(kv.key().c_str());
          int underscorePos = fullName.indexOf('_');
          if (underscorePos > 0) {
            students[studentCount] = fullName.substring(underscorePos + 1);
          } else {
            students[studentCount] = fullName;
          }
          lessons[studentCount] = kv.value().as<JsonArray>();
          studentCount++;
        }
      }
      
      // Display in two columns
      int maxLessons = 0;
      for (int s = 0; s < studentCount; s++) {
        if (lessons[s].size() > maxLessons) maxLessons = lessons[s].size();
      }
      
      // Column headers
      int col1X = 290;
      int col2X = 490;
      for (int s = 0; s < studentCount; s++) {
        display.setCursor(s == 0 ? col1X : col2X, y);
        display.print(students[s]);
      }
      y += 16;
      
      // Lessons vertically
      for (int l = 0; l < maxLessons; l++) {
        for (int s = 0; s < studentCount; s++) {
          if (l < lessons[s].size()) {
            display.setCursor(s == 0 ? col1X : col2X, y);
            display.print((const char*)lessons[s][l]);
          }
        }
        y += 14;
      }
    }
    y += 18;
  }
}

void displayWeather(JsonDocument& doc) {
  display.setFullWindow();
  display.firstPage();
  
  do {
    display.fillScreen(GxEPD_WHITE);
    
    // === LEFT COLUMN: WEATHER (0-260px) ===
    
    // Date as header in large font
    display.setFont(&FreeMonoBold18pt7b);
    display.setCursor(20, 50);
    if (getLocalTime(&timeinfo)) {
      char dateStr[16];
      strftime(dateStr, sizeof(dateStr), "%d.%m.%Y", &timeinfo);
      display.print(dateStr);
    }
    
    // Temperature - large
    display.setFont(&FreeMonoBold18pt7b);
    display.setCursor(20, 150);
    float temp = doc["data"]["instant"]["details"]["air_temperature"] | 0.0;
    display.print(temp, 1);
    display.print(" C");
    
    // Weather icon (48x48) - choose based on symbol
    const char* symbol = doc["data"]["next_1_hours"]["summary"]["symbol_code"] | "unknown";
    const unsigned char* icon = icon_cloud; // default
    
    if (strstr(symbol, "clear") || strstr(symbol, "fair")) {
      icon = icon_sun;
    } else if (strstr(symbol, "rain") || strstr(symbol, "sleet")) {
      icon = icon_rain;
    } else if (strstr(symbol, "snow")) {
      icon = icon_snow;
    } else if (strstr(symbol, "cloud")) {
      icon = icon_cloud;
    }
    
    display.drawBitmap(100, 180, icon, 48, 48, GxEPD_BLACK);
    
    // Humidity (body text)
    display.setFont(&FreeMonoBold9pt7b);
    display.setCursor(20, 290);
    float humidity = doc["data"]["instant"]["details"]["relative_humidity"] | 0.0;
    display.print("Hum: ");
    display.print(humidity, 0);
    display.print("%");

    // Wind (body text)
    display.setFont(&FreeMonoBold9pt7b);
    display.setCursor(20, 330);
    float wind = doc["data"]["instant"]["details"]["wind_speed"] | 0.0;
    display.print("Wind: ");
    display.print(wind, 1);
    display.print(" m/s");
    
    // === INDOOR AIR QUALITY (Airthings) ===
    JsonDocument airDoc;
    if (fetchAirthingsData(airDoc)) {
      display.setFont(&FreeMonoBold12pt7b);
      display.setCursor(20, 380);
      display.print("Inne");
      
      display.setFont(&FreeMonoBold9pt7b);
      display.setCursor(20, 410);
      float indoorTemp = airDoc["data"]["temperature"] | 0.0;
      display.print("Temp: ");
      display.print(indoorTemp, 1);
      display.print(" C");
      
      display.setCursor(20, 430);
      float indoorHum = airDoc["data"]["humidity"] | 0.0;
      display.print("Hum: ");
      display.print(indoorHum, 0);
      display.print("%");
      
      const char* radonLevel = airDoc["data"]["radon_24h_level"] | "good";
      if (strcmp(radonLevel, "good") != 0) {
        display.setCursor(20, 450);
        display.print("Radon: ");
        display.print(radonLevel);
      }
    }
    
    // Vertical separator line
    display.drawLine(260, 0, 260, 480, GxEPD_BLACK);
    
    // === RIGHT COLUMN: CALENDAR (280-800px) ===
    JsonDocument caldoc;
    bool calendarOk = fetchCalendarData(caldoc);
    if (calendarOk) {
      displayCalendar(caldoc);
    } else {
      display.setFont(&FreeMonoBold9pt7b);
      display.setCursor(280, 60);
      display.print("Kalender ikke tilgjengelig");
    }
    
    // === FOOTER BAR (for error messages) ===
    if (!calendarOk) {
      // Gray background footer (25px high)
      display.fillRect(0, 455, 800, 25, GxEPD_BLACK);
      display.setFont(&FreeMonoBold9pt7b);
      display.setTextColor(GxEPD_WHITE);
      display.setCursor(10, 473);
      display.print("Kalender data ikke tilgjengelig");
      display.setTextColor(GxEPD_BLACK); // Reset to black
    }
    
  } while (display.nextPage());
  
  Serial.println("Display updated!");
  display.hibernate();
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("reTerminal E1001 - Weather Dashboard");
  
  // Initialize SPI with custom pins
  SPI.begin(EPD_SCK, -1, EPD_MOSI, EPD_CS);
  
  // Initialize display
  display.init(115200);
  display.setRotation(0);
  display.setTextColor(GxEPD_BLACK);
  
  Serial.println("Display initialized");
  
  // Connect to WiFi
  connectWiFi();
  
  // Sync time
  if (WiFi.status() == WL_CONNECTED) {
    syncTime();
  }
  
  // Fetch and display weather immediately
  if (WiFi.status() == WL_CONNECTED) {
    JsonDocument doc;
    if (fetchWeatherData(doc)) {
      displayWeather(doc);
      lastUpdate = millis();
    } else {
      Serial.println("Failed to fetch weather data");
    }
  } else {
    Serial.println("WiFi not connected - will retry in 60 seconds");
    lastWiFiCheck = millis();
  }
}

void loop() {
  // Check WiFi connection periodically
  if (WiFi.status() != WL_CONNECTED && millis() - lastWiFiCheck >= WIFI_RETRY_INTERVAL) {
    Serial.println("WiFi disconnected, attempting to reconnect...");
    connectWiFi();
    lastWiFiCheck = millis();
    
    if (WiFi.status() == WL_CONNECTED) {
      syncTime();
    }
  }
  
  // Update weather data periodically (only if connected)
  if (WiFi.status() == WL_CONNECTED && millis() - lastUpdate >= UPDATE_INTERVAL) {
    Serial.println("Updating weather data...");
    
    JsonDocument doc;
    if (fetchWeatherData(doc)) {
      displayWeather(doc);
      lastUpdate = millis();
    } else {
      Serial.println("Failed to update weather data");
    }
  }
  
  delay(1000);
}
