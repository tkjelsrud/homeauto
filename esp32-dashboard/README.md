# ESP32 Dashboard for reTerminal E1001

## Hardware
- Seeedstudio reTerminal E1001
- ESP32-S3 microcontroller
- 7.5" e-paper display (800×480, 4-level grayscale)
- Waveshare 7.50inv2 (GDEW075T7 controller)

## Setup

### 1. Build and Upload
```bash
cd esp32-dashboard
python3 -m platformio run -t upload
python3 -m platformio device monitor
```

### 2. Pin Configuration
See [PINS.md](PINS.md) for verified working GPIO configuration.

**Critical:** MOSI is GPIO 9 (not GPIO 6 as shown in some schematics)

### 3. Libraries Used
- GxEPD2: E-paper display driver (GxEPD2_750_T7)
- Adafruit GFX: Graphics library

## Current Status
- ✅ Hello World on e-paper display (WORKING!)
- ⏳ WiFi connectivity (next iteration)
- ⏳ JSON fetching from home automation server

## Next Steps
1. ✅ Test hello world display
2. Add WiFi configuration
3. Fetch JSON from local server at `/api/...`
4. Display calendar, weather, energy data

## Verified Configuration
Tested and confirmed working: January 23, 2026
