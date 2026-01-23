# reTerminal E1001 Pin Configuration

## E-Paper Display Pins (VERIFIED WORKING)

| Signal | GPIO | Function | Notes |
|--------|------|----------|-------|
| CS     | 10   | Chip Select | ESP_IO10/SCREEN_CS# |
| DC     | 11   | Data/Command | ESP_IO11/SCREEN_DC# |
| RST    | 12   | Reset | ESP_IO12/SCREEN_RST# |
| BUSY   | 13   | Busy Signal | ESP_IO13/SCREEN_BUSY# (inverted in ESPHome) |
| SCK    | 7    | SPI Clock | ESP_IO7/SCK |
| MOSI   | 9    | SPI Data Out | **ESP_IO9/MOSI** (NOT GPIO6!) |

## Display Specifications
- **Manufacturer:** Waveshare
- **Model:** 7.50inv2 (Good Display GDEW075T7 controller)
- **Size:** 7.5" monochrome e-paper
- **Resolution:** 800×480 pixels
- **Grayscale:** 4-level grayscale support
- **Arduino Library:** GxEPD2_750_T7

## SPI Configuration
```cpp
SPI.begin(EPD_SCK, -1, EPD_MOSI, EPD_CS);
// SCK=7, MISO=-1 (not used), MOSI=9, CS=10
```

## Important Notes
- **MOSI is GPIO 9, not GPIO 6** as shown in some schematic diagrams
- Configuration verified from working ESPHome config
- BUSY pin may need inversion depending on library
- Display uses Waveshare driver, not generic GxEPD2_750

## Sources
- ESPHome configuration (confirmed working)
- Schematic (FPC connector to screen, 24P 1A)
- Tested and verified: January 23, 2026
