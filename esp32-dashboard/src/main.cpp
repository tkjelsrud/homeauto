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
// Try to include local config first, fall back to default
#if __has_include("config.h.local")
  #include "config.h.local"
#else
  #include "config.h"
#endif
#include "icons.h"

// Waveshare 7.50inv2 display
#define EPD_CS      10  // ESP_IO10/SCREEN_CS#
#define EPD_DC      11  // ESP_IO11/SCREEN_DC#
#define EPD_RST     12  // ESP_IO12/SCREEN_RST#
#define EPD_BUSY    13  // ESP_IO13/SCREEN_BUSY# (inverted)
// SPI pins: SCK=GPIO7, MOSI=GPIO9
#define EPD_SCK     7   // ESP_IO7/SCK
#define EPD_MOSI    9   // ESP_IO9/MOSI

// Battery monitoring (ADC pin)
#define BATTERY_PIN 4   // GPIO4 (ADC1_CH3) for battery voltage reading
// If using voltage divider: Vbat -> R1(100k) -> GPIO4 -> R2(100k) -> GND
// This gives Vmeasured = Vbat / 2, so max measurable is ~6.6V

// Display: 7.5" 800x480 Waveshare 7.50inv2
GxEPD2_BW<GxEPD2_750_T7, GxEPD2_750_T7::HEIGHT> display(GxEPD2_750_T7(EPD_CS, EPD_DC, EPD_RST, EPD_BUSY));

unsigned long lastUpdate = 0;
unsigned long lastWiFiCheck = 0;
const unsigned long WIFI_RETRY_INTERVAL = 30000; // 30 seconds
const unsigned long HTTP_TIMEOUT = 30000; // 30 seconds for all HTTP requests
int wifiRetryCount = 0;
struct tm timeinfo;

#define CALENDAR_DOC_SIZE 4096

// Function prototypes
void syncTime();
void connectWiFi(bool verbose = false);
bool fetchWeatherData(JsonDocument& doc);
bool fetchCalendarData(JsonDocument& doc);
bool fetchAirthingsData(JsonDocument& doc);
bool fetchMillData(JsonDocument& doc);
void displayWeather(JsonDocument& doc);
void displayCalendar(JsonDocument& doc);
void printNorwegian(const char* text);
float readBatteryVoltage();
int getBatteryPercentage(float voltage);uint64_t calculateSleepTime();
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

void connectWiFi(bool verbose) {
  if (verbose) {
    Serial.println("=== WiFi Connection Diagnostics ===");
    Serial.print("SSID: ");
    Serial.println(WIFI_SSID);
    Serial.print("Password length: ");
    Serial.println(strlen(WIFI_PASSWORD));
    
    // Set WiFi mode and disconnect any previous connection
    WiFi.mode(WIFI_STA);
    WiFi.disconnect();
    delay(100);
    
    // Scan for networks to verify SSID exists (only when verbose)
    Serial.println("Scanning for WiFi networks...");
    int n = WiFi.scanNetworks();
    Serial.print("Found ");
    Serial.print(n);
    Serial.println(" networks:");
    
    bool ssidFound = false;
    for (int i = 0; i < n; i++) {
      Serial.print(i + 1);
      Serial.print(": ");
      Serial.print(WiFi.SSID(i));
      Serial.print(" (");
      Serial.print(WiFi.RSSI(i));
      Serial.print(" dBm) ");
      Serial.println(WiFi.encryptionType(i) == WIFI_AUTH_OPEN ? "Open" : "Encrypted");
      
      if (WiFi.SSID(i) == String(WIFI_SSID)) {
        ssidFound = true;
        Serial.println("  ^^ TARGET NETWORK FOUND!");
      }
    }
    
    if (!ssidFound) {
      Serial.println("ERROR: Target SSID not found in scan!");
      Serial.println("Possible issues:");
      Serial.println("  - SSID is 5GHz only (ESP32 needs 2.4GHz)");
      Serial.println("  - Network is out of range");
      Serial.println("  - SSID name mismatch (check spelling/case)");
    }
  } else {
    // Simple mode - just set up WiFi without scanning
    WiFi.mode(WIFI_STA);
    WiFi.disconnect();
    delay(100);
  }
  
  // Disable auto-reconnect to prevent background retry spam
  WiFi.setAutoReconnect(false);
  
  // Set WiFi to maximum power for better connectivity
  WiFi.setTxPower(WIFI_POWER_19_5dBm);
  
  // Add longer delay before connection attempt
  delay(1000);
  
  Serial.print("Connecting to WiFi");
  
  // Try up to 3 times with full reset between attempts
  int maxRetries = 3;
  for (int retry = 0; retry < maxRetries; retry++) {
    if (retry > 0) {
      Serial.println();
      Serial.print("Retry attempt ");
      Serial.print(retry);
      Serial.print("/");
      Serial.print(maxRetries - 1);
      Serial.print("...");
      WiFi.disconnect(true);
      delay(1000);
    }
    
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 40) {
      delay(500);
      if (verbose || attempts % 4 == 0) {
        Serial.print(".");
      }
      attempts++;
    }
    
    if (WiFi.status() == WL_CONNECTED) {
      Serial.println(" Connected!");
      if (verbose) {
        Serial.print("IP: ");
        Serial.print(WiFi.localIP());
        Serial.print(", Signal: ");
        Serial.print(WiFi.RSSI());
        Serial.println(" dBm");
      }
      // Enable auto-reconnect only after successful connection
      WiFi.setAutoReconnect(true);
      return; // Success, exit function
    }
  }
  
  // All retries failed
  Serial.print(" Failed (Status: ");
  Serial.print(WiFi.status());
  Serial.println(")");
  // Disconnect to stop background retry attempts
  WiFi.disconnect(true);
  delay(100);
}

bool fetchWeatherData(JsonDocument& doc) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected");
    return false;
  }
  
  Serial.print("Connecting to: ");
  Serial.println(WEATHER_ENDPOINT);
  
  HTTPClient http;
  http.begin(WEATHER_ENDPOINT);
  http.setTimeout(HTTP_TIMEOUT);
  
  Serial.println("Sending HTTP GET request...");
  int httpCode = http.GET();
  Serial.print("HTTP response code: ");
  Serial.println(httpCode);
  
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
  Serial.print("Fetching calendar from: ");
  Serial.println(CALENDAR_ENDPOINT);
  HTTPClient http;
  http.begin(CALENDAR_ENDPOINT);
  http.setTimeout(HTTP_TIMEOUT);
  int httpCode = http.GET();
  Serial.print("Calendar HTTP response: ");
  Serial.println(httpCode);
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
  Serial.print("Connecting to Airthings: ");
  Serial.println(AIRTHINGS_ENDPOINT);
  http.begin(AIRTHINGS_ENDPOINT);
  http.setTimeout(HTTP_TIMEOUT);
  Serial.println("Fetching Airthings data (may take 10-20 seconds)...");
  int httpCode = http.GET();
  Serial.print("Airthings HTTP response: ");
  Serial.println(httpCode);
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

bool fetchMillData(JsonDocument& doc) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected");
    return false;
  }
  Serial.print("Fetching Mill from: ");
  Serial.println(MILL_ENDPOINT);
  HTTPClient http;
  http.begin(MILL_ENDPOINT);
  http.setTimeout(HTTP_TIMEOUT);
  int httpCode = http.GET();
  Serial.print("Mill HTTP response: ");
  Serial.println(httpCode);
  if (httpCode == HTTP_CODE_OK) {
    String payload = http.getString();
    Serial.println("Mill data received");
    DeserializationError error = deserializeJson(doc, payload);
    if (error) {
      Serial.print("Mill JSON parsing failed: ");
      Serial.println(error.c_str());
      http.end();
      return false;
    }
    http.end();
    return true;
  } else {
    Serial.print("Mill HTTP GET failed, error: ");
    Serial.println(httpCode);
    http.end();
    return false;
  }
}

// Read battery voltage from ADC
// Assumes voltage divider: Vbat -> R1(100k) -> GPIO4 -> R2(100k) -> GND
// This gives Vmeasured = Vbat / 2
float readBatteryVoltage() {
  // Configure ADC
  analogReadResolution(12); // 12-bit resolution (0-4095)
  analogSetAttenuation(ADC_11db); // 0-3.3V range
  
  // Take multiple readings and average
  int samples = 10;
  int total = 0;
  for (int i = 0; i < samples; i++) {
    total += analogRead(BATTERY_PIN);
    delay(10);
  }
  int adcValue = total / samples;
  
  // Convert ADC value to voltage
  // ADC_11db: 0-4095 maps to 0-3.3V (approximately)
  // Note: ADC on ESP32-S3 has non-linear response, especially at higher voltages
  // For more accurate readings, use esp_adc_cal library for calibration
  float voltage = (adcValue / 4095.0) * 3.3;
  
  // Check if voltage divider is used (if adcValue is very low, might be direct connection)
  // If no voltage divider, comment out the next line
  // Multiply by 2 if using voltage divider (100k/100k)
  voltage = voltage * 2.0;
  
  Serial.print("Battery ADC raw: ");
  Serial.print(adcValue);
  Serial.print(" (0-4095), Voltage at pin: ");
  Serial.print((adcValue / 4095.0) * 3.3, 2);
  Serial.print("V, Calculated battery: ");
  Serial.print(voltage, 2);
  Serial.println("V");
  
  return voltage;
}

// Convert battery voltage to percentage (for LiPo/Li-ion)
int getBatteryPercentage(float voltage) {
  // LiPo voltage curve (approximate):
  // 4.2V = 100%, 3.7V = 50%, 3.3V = 0%
  if (voltage >= 4.2) return 100;
  if (voltage <= 3.3) return 0;
  
  // Linear approximation
  return (int)((voltage - 3.3) / (4.2 - 3.3) * 100);
}

// Calculate sleep time until next scheduled wake-up
uint64_t calculateSleepTime() {
  if (!getLocalTime(&timeinfo)) {
    Serial.println("Failed to get time for sleep calculation, using fallback");
    return DEEP_SLEEP_SECONDS;
  }
  
  int currentHour = timeinfo.tm_hour;
  int currentMin = timeinfo.tm_min;
  int currentTotalMinutes = currentHour * 60 + currentMin;
  
  Serial.print("Current time: ");
  Serial.print(currentHour);
  Serial.print(":");
  Serial.println(currentMin);
  
  // Find next wake time
  int nextWakeMinutes = -1;
  
  // Check all scheduled times today
  for (int i = 0; i < NUM_WAKE_TIMES; i++) {
    int wakeMinutes = WAKE_TIMES[i][0] * 60 + WAKE_TIMES[i][1];
    if (wakeMinutes > currentTotalMinutes) {
      nextWakeMinutes = wakeMinutes;
      Serial.print("Next wake time today: ");
      Serial.print(WAKE_TIMES[i][0]);
      Serial.print(":");
      Serial.println(WAKE_TIMES[i][1]);
      break;
    }
  }
  
  // If no more times today, wake at first time tomorrow (05:00)
  if (nextWakeMinutes == -1) {
    // Calculate minutes until 05:00 tomorrow
    int minutesUntilMidnight = (24 * 60) - currentTotalMinutes;
    int firstWakeMinutes = WAKE_TIMES[0][0] * 60 + WAKE_TIMES[0][1]; // 05:00 = 300 minutes
    nextWakeMinutes = currentTotalMinutes + minutesUntilMidnight + firstWakeMinutes;
    
    Serial.print("No more times today. Next wake: tomorrow at ");
    Serial.print(WAKE_TIMES[0][0]);
    Serial.print(":");
    Serial.println(WAKE_TIMES[0][1]);
  }
  
  // Calculate sleep duration
  int sleepMinutes;
  if (nextWakeMinutes > currentTotalMinutes) {
    sleepMinutes = nextWakeMinutes - currentTotalMinutes;
  } else {
    // Next day calculation
    sleepMinutes = (24 * 60) - currentTotalMinutes + nextWakeMinutes;
  }
  
  // Add 1 minute buffer to ensure we don't wake too early
  sleepMinutes += 1;
  
  uint64_t sleepSeconds = sleepMinutes * 60;
  
  Serial.print("Sleep duration: ");
  Serial.print(sleepMinutes);
  Serial.print(" minutes (");
  Serial.print(sleepMinutes / 60.0, 1);
  Serial.println(" hours)");
  
  return sleepSeconds;
}

// Helper function to print Norwegian text with special character support
void printNorwegian(const char* text) {
  String str = String(text);
  int len = str.length();
  int i = 0;
  
  while (i < len) {
    // Check for UTF-8 encoded Norwegian characters
    if ((uint8_t)str[i] == 0xC3 && i + 1 < len) {
      uint8_t nextByte = (uint8_t)str[i + 1];
      
      // ø (U+00F8) = 0xC3 0xB8
      if (nextByte == 0xB8) {
        // Draw 'o' then overlay with '/' (thicker line)
        int16_t x = display.getCursorX();
        int16_t y = display.getCursorY();
        display.print("o");
        int16_t x2 = display.getCursorX();
        // Draw diagonal lines through the 'o' (multiple lines for thickness)
        display.drawLine(x + 2, y + 2, x + (x2-x) - 4, y - 8, GxEPD_BLACK);
        display.drawLine(x + 3, y + 2, x + (x2-x) - 3, y - 8, GxEPD_BLACK);
        display.drawLine(x + 2, y + 1, x + (x2-x) - 4, y - 9, GxEPD_BLACK);
        i += 2;
        continue;
      }
      // Ø (U+00D8) = 0xC3 0x98
      else if (nextByte == 0x98) {
        int16_t x = display.getCursorX();
        int16_t y = display.getCursorY();
        display.print("O");
        int16_t x2 = display.getCursorX();
        // Draw diagonal lines through the 'O' (multiple lines for thickness)
        display.drawLine(x + 2, y - 4, x + (x2-x) - 4, y - 16, GxEPD_BLACK);
        display.drawLine(x + 3, y - 4, x + (x2-x) - 3, y - 16, GxEPD_BLACK);
        display.drawLine(x + 2, y - 5, x + (x2-x) - 4, y - 17, GxEPD_BLACK);
        i += 2;
        continue;
      }
      // æ (U+00E6) = 0xC3 0xA6
      else if (nextByte == 0xA6) {
        display.print("ae");
        i += 2;
        continue;
      }
      // Æ (U+00C6) = 0xC3 0x86
      else if (nextByte == 0x86) {
        display.print("AE");
        i += 2;
        continue;
      }
      // å (U+00E5) = 0xC3 0xA5
      else if (nextByte == 0xA5) {
        int16_t x = display.getCursorX();
        int16_t y = display.getCursorY();
        display.print("a");
        // Draw small circle above
        display.drawCircle(x + 4, y - 15, 2, GxEPD_BLACK);
        i += 2;
        continue;
      }
      // Å (U+00C5) = 0xC3 0x85
      else if (nextByte == 0x85) {
        int16_t x = display.getCursorX();
        int16_t y = display.getCursorY();
        display.print("A");
        display.drawCircle(x + 6, y - 18, 2, GxEPD_BLACK);
        i += 2;
        continue;
      }
    }
    
    // Regular ASCII character
    display.print(str[i]);
    i++;
  }
}

void displayCalendar(JsonDocument& doc) {
  // Get current weekday (0=Monday, 6=Sunday)
  int todayIdx = -1, tomorrowIdx = -1, dayAfterIdx = -1, fourthDayIdx = -1;
  if (getLocalTime(&timeinfo)) {
    todayIdx = (timeinfo.tm_wday + 6) % 7; // tm_wday: 0=Sunday, 1=Monday...
    tomorrowIdx = (todayIdx + 1) % 7;
    dayAfterIdx = (todayIdx + 2) % 7;
    fourthDayIdx = (todayIdx + 3) % 7;
  }
  
  JsonArray days = doc["data"].as<JsonArray>();
  
  // Display days in chronological order (today, tomorrow, day after, fourth day)
  int daysToShow[4] = {todayIdx, tomorrowIdx, dayAfterIdx, fourthDayIdx};
  int y = 40;
  
  for (int d = 0; d < 4; ++d) {
    int targetIdx = daysToShow[d];
    if (targetIdx < 0) continue;
    
    // Find the day with this weekday_index
    for (int i = 0; i < days.size(); ++i) {
      int idx = days[i]["weekday_index"] | -1;
      if (idx != targetIdx) continue;
      
      // Error handling: check if day data exists
      if (days[i].isNull()) {
        Serial.print("Warning: Day ");
        Serial.print(i);
        Serial.println(" data is null, skipping");
        continue;
      }
      
    // Header: Day name with light gray background for today
    display.setFont(&FreeMonoBold18pt7b);
    
    // Add light gray background for today (d == 0)
    if (d == 0) {
      // Draw light gray rectangle behind day name
      // Use dithering pattern for light gray effect
      for (int by = y - 25; by < y + 5; by += 2) {
        for (int bx = 280; bx < 500; bx += 2) {
          display.drawPixel(bx, by, GxEPD_BLACK);
        }
      }
    }
    
    display.setCursor(280, y);
    const char* dayName = days[i]["name"] | "Ukjent";
    printNorwegian(dayName);
    y += 30;
    
    // Waste collection (if any)
    if (!days[i]["waste"].isNull()) {
      JsonArray waste = days[i]["waste"].as<JsonArray>();
      if (waste.size() > 0) {
        display.setFont(&FreeMonoBold9pt7b);
        display.setCursor(280, y);
        display.print("Hentes: ");
        for (int w = 0; w < waste.size(); ++w) {
          if (w > 0) display.print(", ");
          const char* wasteType = waste[w]["type"] | "";
          printNorwegian(wasteType);
        }
        y += 20;
      }
    }
    
    // Dinner (only if there is dinner info)
    if (!days[i]["dinner"].isNull()) {
      const char* dinner = days[i]["dinner"];
      if (dinner != nullptr && strlen(dinner) > 0) {
        display.setFont(&FreeMonoBold9pt7b);
        display.setCursor(280, y);
        // Limit dinner text to 40 characters (same as events)
        String dinnerStr = String(dinner);
        if (dinnerStr.length() > 40) {
          dinnerStr = dinnerStr.substring(0, 37) + "...";
        }
        printNorwegian(dinnerStr.c_str());
        y += 20;
      }
    }
    
    // Events today
    if (!days[i]["events"].isNull()) {
      JsonArray events = days[i]["events"].as<JsonArray>();
      if (events.size() > 0) {
        for (JsonObject ev : events) {
          if (ev["is_next_week"]) continue;
          display.setCursor(290, y);
          const char* start = ev["start"] | "";
          const char* summary = ev["summary"] | "";
          // Print time without seconds, remove :00 if present
          if (strlen(start) > 11) {
            char timeStr[6];
            strncpy(timeStr, &start[11], 5); // Copy HH:MM
            timeStr[5] = '\0';
            // Remove :00 suffix if present
            if (timeStr[3] == '0' && timeStr[4] == '0') {
              timeStr[2] = '\0'; // Truncate at HH
            }
            display.print(timeStr);
          }
          display.print(" ");
          // Limit summary to 40 characters
          String summaryStr = String(summary);
          if (summaryStr.length() > 40) {
            summaryStr = summaryStr.substring(0, 37) + "...";
          }
          printNorwegian(summaryStr.c_str());
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
          // Print time without seconds, remove :00 if present
          if (strlen(start) > 11) {
            char timeStr[6];
            strncpy(timeStr, &start[11], 5); // Copy HH:MM
            timeStr[5] = '\0';
            // Remove :00 suffix if present
            if (timeStr[3] == '0' && timeStr[4] == '0') {
              timeStr[2] = '\0'; // Truncate at HH
            }
            display.print(timeStr);
          }
          display.print(" ");
          // Limit summary to 40 characters
          String summaryStr = String(summary);
          if (summaryStr.length() > 40) {
            summaryStr = summaryStr.substring(0, 37) + "...";
          }
          printNorwegian(summaryStr.c_str());
          y += 16;
        }
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
      break; // Found the day, move to next day to show
    }
  }
}

void displayWeather(JsonDocument& doc) {
  // Track errors for footer display
  String errorMessages = "";
  bool weatherOk = true;
  bool airthingsOk = false;
  bool calendarOk = false;
  
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
    } else {
      display.print("Dato ukjent");
      if (errorMessages.length() > 0) errorMessages += ", ";
      errorMessages += "Tid ikke synket";
    }
    
    // Temperature - large with icon on same line
    display.setFont(&FreeMonoBold18pt7b);
    display.setCursor(20, 150);
    float temp = doc["data"]["instant"]["details"]["air_temperature"] | 0.0;
    display.print(temp, 1);
    display.print(" C");
    
    // Weather icon (48x48) - positioned to the right of temperature
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
    
    // Draw icon to the right of temperature (aligned with baseline)
    // Use GxEPD_WHITE to invert the icon (black background becomes white)
    display.drawBitmap(160, 120, icon, 48, 48, GxEPD_WHITE);
    
    // Humidity (body text) - moved up since icon no longer takes space below
    display.setFont(&FreeMonoBold9pt7b);
    display.setCursor(20, 200);
    float humidity = doc["data"]["instant"]["details"]["relative_humidity"] | 0.0;
    display.print("Hum: ");
    display.print(humidity, 0);
    display.print("%");

    // Wind (body text)
    display.setFont(&FreeMonoBold9pt7b);
    display.setCursor(20, 230);
    float wind = doc["data"]["instant"]["details"]["wind_speed"] | 0.0;
    display.print("Wind: ");
    display.print(wind, 1);
    display.print(" m/s");
    
    // === MILL TEMPERATURES ===
    JsonDocument millDoc;
    if (fetchMillData(millDoc)) {
      display.setFont(&FreeMonoBold9pt7b);
      int y = 280;
      JsonObject rooms = millDoc["data"]["rooms"];
      int count = 0;
      for (JsonPair room : rooms) {
        if (count >= 3) break; // Max 3 lines
        JsonArray devices = room.value().as<JsonArray>();
        if (devices.size() > 0) {
          JsonObject device = devices[0];
          String roomName = String(room.key().c_str());
          float temp = device["ambient_temp"] | 0.0;
          int power = device["power"] | 0;
          
          // Pad room name to exactly 8 characters
          while (roomName.length() < 8) roomName += " ";
          if (roomName.length() > 8) roomName = roomName.substring(0, 8);
          
          // Create formatted string
          char line[32];
          if (power > 0) {
            snprintf(line, sizeof(line), "%s:%4.1fc (PA)", roomName.c_str(), temp);
          } else {
            snprintf(line, sizeof(line), "%s:%4.1fc", roomName.c_str(), temp);
          }
          
          // Draw text normally in black
          display.setCursor(20, y);
          display.setTextColor(GxEPD_BLACK);
          display.print(line);
          
          y += 20;
          count++;
        }
      }
    }
    
    // Battery indicator in bottom-left corner
    float batteryVoltage = readBatteryVoltage();
    int batteryPercent = getBatteryPercentage(batteryVoltage);
    
    // Show battery status with debug info
    // NOTE: If ADC value is close to 4095 (max), the pin is floating - no battery connected
    // To disable battery display, comment out this entire section
    // Common issue: reTerminal E1001 may not have battery on GPIO4 by default
    
    // More lenient check - show if voltage seems valid for battery (2.5V - 5V)
    // Adjusted from 2.0-6.0 to be more specific for USB power (5V) or LiPo (3.7-4.2V)
    bool showBattery = (batteryVoltage > 2.5 && batteryVoltage < 5.5);
    
    if (showBattery) {
      display.setFont(&FreeMonoBold9pt7b);
      
      // Draw battery icon (simple rectangle with fill)
      int battX = 10;
      int battY = 460;
      display.drawRect(battX, battY, 30, 14, GxEPD_BLACK); // Battery body
      display.fillRect(battX + 30, battY + 4, 3, 6, GxEPD_BLACK); // Battery tip
      
      // Fill battery based on percentage
      int fillWidth = (batteryPercent * 26) / 100; // 26 = 30-4 (leave margin)
      if (fillWidth > 0) {
        display.fillRect(battX + 2, battY + 2, fillWidth, 10, GxEPD_BLACK);
      }
      
      // Display voltage and percentage for debugging
      display.setCursor(battX + 35, battY + 12);
      display.print(batteryVoltage, 1);
      display.print("V ");
      display.print(batteryPercent);
      display.print("%");
    } else {
      // Debug: Show why battery is not displayed
      Serial.print("Battery not displayed - voltage out of range: ");
      Serial.print(batteryVoltage, 2);
      Serial.println("V (expected 2.5-5.5V)");
    }
    
    // Vertical separator line
    display.drawLine(260, 0, 260, 480, GxEPD_BLACK);
    
    // === RIGHT COLUMN: CALENDAR (280-800px) ===
    JsonDocument caldoc;
    calendarOk = fetchCalendarData(caldoc);
    if (calendarOk) {
      displayCalendar(caldoc);
    } else {
      display.setFont(&FreeMonoBold9pt7b);
      display.setCursor(280, 60);
      display.print("Kalender ikke tilgjengelig");
      if (errorMessages.length() > 0) errorMessages += ", ";
      errorMessages += "Kalender";
    }
    
    // === FOOTER BAR (for error messages) ===
    if (errorMessages.length() > 0) {
      // Gray background footer (25px high)
      display.fillRect(0, 455, 800, 25, GxEPD_BLACK);
      display.setFont(&FreeMonoBold9pt7b);
      display.setTextColor(GxEPD_WHITE);
      display.setCursor(10, 473);
      // Limit error message length to fit on screen
      if (errorMessages.length() > 90) {
        errorMessages = errorMessages.substring(0, 87) + "...";
      }
      display.print("Feil: ");
      printNorwegian(errorMessages.c_str());
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
  
  // Initialize battery monitoring pin
  pinMode(BATTERY_PIN, INPUT);
  
  // Initialize SPI with custom pins
  SPI.begin(EPD_SCK, -1, EPD_MOSI, EPD_CS);
  
  // Initialize display
  display.init(115200);
  display.setRotation(0);
  display.setTextColor(GxEPD_BLACK);
  
  Serial.println("Display initialized");
  
  // Try to connect to WiFi with limited attempts
  bool wifiConnected = false;
  for (int attempt = 1; attempt <= MAX_WIFI_CONNECTION_ATTEMPTS && !wifiConnected; attempt++) {
    Serial.print("WiFi connection attempt ");
    Serial.print(attempt);
    Serial.print(" of ");
    Serial.println(MAX_WIFI_CONNECTION_ATTEMPTS);
    
    connectWiFi(attempt == 1); // Verbose only on first attempt
    
    if (WiFi.status() == WL_CONNECTED) {
      wifiConnected = true;
    } else if (attempt < MAX_WIFI_CONNECTION_ATTEMPTS) {
      Serial.println("Waiting 5 seconds before next attempt...");
      delay(5000);
    }
  }
  
  // Only proceed with data fetching if WiFi is connected
  if (wifiConnected) {
    // Sync time
    syncTime();
    
    // Fetch and display weather
    Serial.println("Fetching weather data...");
    JsonDocument doc;
    if (fetchWeatherData(doc)) {
      Serial.println("Weather data fetched successfully, updating display...");
      displayWeather(doc);
      lastUpdate = millis();
    } else {
      Serial.println("Failed to fetch weather data - will retry next wake");
    }
  } else {
    // WiFi failed after all attempts - show error
    Serial.print("WiFi connection failed after ");
    Serial.print(MAX_WIFI_CONNECTION_ATTEMPTS);
    Serial.println(" attempts - will retry in 30 minutes");
    
    // Show WiFi error on display
    display.setFullWindow();
    display.firstPage();
    do {
      display.fillScreen(GxEPD_WHITE);
      display.setFont(&FreeMonoBold18pt7b);
      display.setCursor(100, 200);
      display.print("WiFi feil");
      display.setFont(&FreeMonoBold12pt7b);
      display.setCursor(100, 250);
      display.print("Prover igjen om 30 min");
    } while (display.nextPage());
    display.hibernate();
  }
  
  // Always turn off WiFi and go to deep sleep to save power
  Serial.println("Turning off WiFi and entering deep sleep...");
  
  // Calculate smart sleep time based on schedule
  uint64_t sleepTime = calculateSleepTime();
  
  // Check battery and potentially extend sleep if critical
  float batteryVoltage = readBatteryVoltage();
  
  if (batteryVoltage > 2.5 && batteryVoltage < 5.5) {
    // Valid battery reading exists
    if (batteryVoltage < BATTERY_LOW_THRESHOLD) {
      // Low battery - potentially skip next wake and sleep longer
      Serial.println("WARNING: Low battery detected!");
      Serial.print("Battery voltage: ");
      Serial.print(batteryVoltage, 2);
      Serial.println("V");
      // Still use scheduled time, but log the warning
    }
  }
  
  Serial.print("Entering deep sleep for ");
  Serial.print(sleepTime);
  Serial.println(" seconds");
  
  WiFi.disconnect(true);
  WiFi.mode(WIFI_OFF);
  delay(100);
  
  // Enter deep sleep
  esp_sleep_enable_timer_wakeup(sleepTime * 1000000ULL); // Convert to microseconds
  Serial.println("Going to sleep now...");
  Serial.flush(); // Wait for serial to finish
  esp_deep_sleep_start();
  
  // Code never reaches here - ESP32 will restart after waking
}

void loop() {
  // This code should never be reached with deep sleep enabled
  // If we get here, something went wrong with deep sleep
  Serial.println("ERROR: loop() should not execute with deep sleep enabled!");
  Serial.println("Attempting to enter deep sleep again...");
  
  WiFi.disconnect(true);
  WiFi.mode(WIFI_OFF);
  delay(100);
  
  esp_sleep_enable_timer_wakeup(DEEP_SLEEP_SECONDS * 1000000ULL);
  esp_deep_sleep_start();
}
