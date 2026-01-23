#ifndef CONFIG_H
#define CONFIG_H

// WiFi Configuration
// Replace with your network credentials
const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// Server Configuration
const char* WEATHER_ENDPOINT = "http://YOUR_SERVER:5000/weather";

// Calendar endpoint
const char* CALENDAR_ENDPOINT = "http://YOUR_SERVER:5000/bigcalendar";

// Airthings endpoint
const char* AIRTHINGS_ENDPOINT = "http://YOUR_SERVER:5000/airthings";

// Update interval (milliseconds)
const unsigned long UPDATE_INTERVAL = 1800000; // 30 minutes

#endif
