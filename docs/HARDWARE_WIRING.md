# WaveAlert360 Hardware Wiring Guide

## LED Strip Wiring Diagram

### Overview
WaveAlert360 uses three independent WS2811/WS2812 addressable LED strips (48 LEDs each) controlled by a Raspberry Pi Zero 2 W.

### GPIO Pinout — Raspberry Pi Zero 2 W

> Reference: [pinout.xyz](https://pinout.xyz/)
>
> Orient your Pi with the GPIO header on the right and HDMI port on the left.
> Pin 1 is top-left (the only pin with a square solder pad on the underside).

```
        WaveAlert360 GPIO Pinout — Raspberry Pi Zero 2 W
        ═══════════════════════════════════════════════════

        ┌───────────────────────────────────────────────────────────────────────┐
        │                                                                       │
        │   ┌─────────────────────────────────────────────────────────────┐     │
        │   │ ┌──────┐                    40-Pin Header                   │     │
        │   │ │ USB  │                  (pin 1 = top-left)                │     │
        │   │ └──────┘                                                    │     │
        │   │                                                             │     │
        │   │ ┌──────┐                                                    │     │
        │   │ │ HDMI │                                                    │     │
        │   │ └──────┘                                                    │     │
        │   └────────────────────────────────────────────────┬────────────┘     │
        │                                                    │                  │
        │     ACTIVE WaveAlert360 connections marked  ◄══    │                  │
        │     GND pins usable for strips marked       ■      │                  │
        │                                                    │                  │
        └────────────────────────────────────────────────────┼──────────────────┘
                                                             │
       ACTIVE PINS                                           │
       ═══════════                                           │
                                                             ▼
               (LEFT / Odd Pins)              (RIGHT / Even Pins)
         ┌─────────────────────┐        ┌─────────────────────┐
   Pin 1 │  3V3 Power      ◄══ │●      ●│  5V Power       ◄══│ Pin 2
         │  Red wire → GREEN    │        │  Red wire → RED    │
         │  strip power (+V)    │        │  strip power (+5V)  │
         ├─────────────────────┤        ├─────────────────────┤
   Pin 3 │  GPIO 2  (I2C SDA)  │●      ●│  5V Power       ◄══│ Pin 4
         │                     │        │  Red wire → YELLOW │
         │                     │        │  strip power (+5V)  │
         ├─────────────────────┤        ├─────────────────────┤
   Pin 5 │  GPIO 3  (I2C SCL)  │●      ●│  Ground          ■ │ Pin 6
         │                     │        │  White wire → RED   │
         │                     │        │  strip GND          │
         ├─────────────────────┤        ├─────────────────────┤
   Pin 7 │  GPIO 4  (GPCLK0)   │●      ●│  GPIO 14 (UART TX) │ Pin 8
         ├─────────────────────┤        ├─────────────────────┤
   Pin 9 │  Ground          ■  │●      ●│  GPIO 15 (UART RX) │ Pin 10
         ├─────────────────────┤        ├─────────────────────┤
  Pin 11 │  GPIO 17            │●      ●│  GPIO 18 (PWM0) ◄══│ Pin 12
         │                     │        │  Green wire → RED   │
         │                     │        │  strip data (DIN)   │
         ├─────────────────────┤        ├─────────────────────┤
  Pin 13 │  GPIO 27            │●      ●│  Ground          ■ │ Pin 14
         ├─────────────────────┤        ├─────────────────────┤
  Pin 15 │  GPIO 22            │●      ●│  GPIO 23            │ Pin 16
         ├─────────────────────┤        ├─────────────────────┤
  Pin 17 │  3V3 Power          │●      ●│  GPIO 24            │ Pin 18
         ├─────────────────────┤        ├─────────────────────┤
  Pin 19 │  GPIO 10 (SPI MOSI) │●      ●│  Ground          ■ │ Pin 20
         ├─────────────────────┤        ├─────────────────────┤
  Pin 21 │  GPIO 9  (SPI MISO) │●      ●│  GPIO 25            │ Pin 22
         ├─────────────────────┤        ├─────────────────────┤
  Pin 23 │  GPIO 11 (SPI SCLK) │●      ●│  GPIO 8  (SPI CE0)  │ Pin 24
         ├─────────────────────┤        ├─────────────────────┤
  Pin 25 │  Ground          ■  │●      ●│  GPIO 7  (SPI CE1)  │ Pin 26
         ├─────────────────────┤        ├─────────────────────┤
  Pin 27 │  GPIO 0  (EEPROM)   │●      ●│  GPIO 1  (EEPROM)   │ Pin 28
         ├─────────────────────┤        ├─────────────────────┤
  Pin 29 │  GPIO 5             │●      ●│  Ground          ■ │ Pin 30
         ├─────────────────────┤        ├─────────────────────┤
  Pin 31 │  GPIO 6             │●      ●│  GPIO 12 (PWM0)     │ Pin 32
         ├─────────────────────┤        ├─────────────────────┤
  Pin 33 │  GPIO 13 (PWM1) ◄══ │●      ●│  Ground          ■ │ Pin 34
         │  Green wire → GREEN │        │  White wire → GREEN │
         │  strip data (DIN)   │        │  strip GND          │
         ├─────────────────────┤        ├─────────────────────┤
  Pin 35 │  GPIO 19 (PCM FS)   │●      ●│  GPIO 16            │ Pin 36
         ├─────────────────────┤        ├─────────────────────┤
  Pin 37 │  GPIO 26            │●      ●│  GPIO 20 (PCM DIN)  │ Pin 38
         ├─────────────────────┤        ├─────────────────────┤
  Pin 39 │  Ground          ■  │●      ●│  GPIO 21 (PCM) ◄══ │ Pin 40
         │  White wire →       │        │  Green wire →       │
         │  YELLOW strip GND   │        │  YELLOW strip data  │
         └─────────────────────┘        └─────────────────────┘
```

### WaveAlert360 Pin Summary

| Physical Pin | BCM GPIO | Function | Wire Color | LED Strip |
|:---:|:---:|:---:|:---:|:---|
| **1** | — | 3.3V Power | Red wire | GREEN strip power |
| **2** | — | 5V Power | Red wire | RED strip power |
| **4** | — | 5V Power | Red wire | YELLOW strip power |
| **6** | — | Ground | White wire | RED strip GND |
| **12** | GPIO 18 | PWM0 | Green wire | RED strip data (48 LEDs — DANGER) |
| **33** | GPIO 13 | PWM1 | Green wire | GREEN strip data (48 LEDs — SAFE) |
| **34** | — | Ground | White wire | GREEN strip GND |
| **39** | — | Ground | White wire | YELLOW strip GND |
| **40** | GPIO 21 | PCM DOUT | Green wire | YELLOW strip data (48 LEDs — CAUTION) |

> **Note:** The GREEN strip is powered from Pin 1 (3.3V) instead of 5V.
> This works at low brightness but the strip may appear slightly dimmer than the other two.

### LED Strip Wire Colors

Each WS2811/WS2812 LED strip has **3 wires**:

| Wire Color | Function | Description |
|:---:|:---:|:---|
| **Red wire** | Power | Supplies voltage to the LEDs |
| **White wire** | Ground (GND) | Common return / reference |
| **Green wire** | Data (DIN) | Signal from Pi GPIO to strip |

### Complete Wiring Schematic

```
    ┌────────────────────────────────────────────────────────────────┐
    │                   Raspberry Pi Zero 2 W                        │
    │                    Running WaveAlert360                        │
    │                                                                │
    │  3.3V     5V      5V     GND     GPIO18   GPIO13   GND    GND     GPIO21  │
    │ (Pin 1) (Pin 2) (Pin 4) (Pin 6)  (Pin 12) (Pin 33) (Pin 34) (Pin 39) (Pin 40) │
    └───┬───────┬───────┬───────┬────────┬────────┬────────┬────────┬────────┬───┘
        │       │       │       │        │        │        │        │        │
        │       │       │       │        │        │        │        │        │
   ┌────┼───────┼───────┼───────┼────────┼────────┼────────┼────────┼────────┼───┐
   │    │       │       │       │        │        │        │        │        │   │
   │    │    ┌──┴──┐    │    ┌──┴──┐  ┌──┴──┐  ┌──┴──┐  ┌──┴──┐  ┌──┴──┐  ┌──┴──┐│
   │    │    │     │    │    │     │  │     │  │     │  │     │  │     │  │     ││
   │    │    │ Red │    │    │White│  │Green│  │Green│  │White│  │White│  │Green││
   │    │    │wire │    │    │wire │  │wire │  │wire │  │wire │  │wire │  │wire ││
   │    │    └──┬──┘    │    └──┬──┘  └──┬──┘  └──┬──┘  └──┬──┘  └──┬──┘  └──┬──┘│
   │    │       │       │       │        │        │        │        │        │   │
   │    │       ▼       │       ▼        ▼        ▼        ▼        ▼        ▼   │
   │    │  ╔════════╗   │  ╔════════╗╔════════╗╔════════╗╔════════╗╔════════╗╔════════╗│
   │    │  │+5V PWR │   │  │  GND  ││  DATA  ││  DATA  ││  GND  ││  GND  ││  DATA  ││
   │    │  ╚═══╤════╝   │  ╚═══╤════╝╚═══╤════╝╚═══╤════╝╚═══╤════╝╚═══╤════╝╚═══╤════╝│
   │    │      │        │      │         │         │         │         │         │   │
   │    │  ┌───┴────────┼──────┴─────────┴──┐  ┌───┴─────────┴──┐  ┌───┴─────────┴──┐│
   │    │  │     RED STRIP (DANGER)         │  │  GREEN STRIP   │  │  YELLOW STRIP  ││
   │    │  │        48 LEDs                 │  │    (SAFE)       │  │   (CAUTION)    ││
   │    │  │                                │  │   48 LEDs       │  │   48 LEDs      ││
   │    │  │  Red wire ──► +5V  (Pin 2)     │  │                 │  │                ││
   │    │  │  White wire─► GND  (Pin 6)     │  │  Red wire ──►   │  │  Red wire ──►  ││
   │    │  │  Green wire─► DIN  (Pin 12)    │  │   +V (Pin 1)    │  │   +5V (Pin 4)  ││
   │    │  │                                │  │  White wire─►   │  │  White wire─►  ││
   │    │  │                                │  │   GND (Pin 34)  │  │   GND (Pin 39) ││
   │    │  │                                │  │  Green wire─►   │  │  Green wire─►  ││
   │    │  │                                │  │   DIN (Pin 33)  │  │   DIN (Pin 40) ││
   │    │  └────────────────────────────────┘  └─────────────────┘  └────────────────┘│
   │    │                                                                           │
   └────┼───────────────────────────────────────────────────────────────────────────┘
        │
        │   POWER FLOW:  USB adapter (5V/2.5A+) ──► Pi ──► LED strips
        │   IMPORTANT:   Only ONE LED strip is ever active at a time.
        │
        └── Pin 1 = 3.3V (GREEN strip), Pin 2 = 5V (RED strip), Pin 4 = 5V (YELLOW strip)
```

### Per-Strip Wiring Table

| Strip | Red Wire (Power) | White Wire (GND) | Green Wire (Data) |
|:---|:---:|:---:|:---:|
| RED strip (DANGER) | Pi Pin 2 (5V) | Pi Pin 6 (GND) | Pi Pin 12 (GPIO 18) |
| GREEN strip (SAFE) | Pi Pin 1 (3.3V) | Pi Pin 34 (GND) | Pi Pin 33 (GPIO 13) |
| YELLOW strip (CAUTION) | Pi Pin 4 (5V) | Pi Pin 39 (GND) | Pi Pin 40 (GPIO 21) |

> **Note:** Each strip uses its own dedicated power, ground, and data pin — no shared pins.

## Hardware Specifications

### LED Strips
- **Type**: WS2811 or WS2812 addressable RGB LED strips
- **Count**: 48 LEDs per strip × 3 strips = 144 total LEDs
- **Voltage**: 5V DC
- **Data Protocol**: Single-wire PWM (800kHz)
- **Color Order**: GRB (Green-Red-Blue)
- **Current Draw**: ~240mA per strip at operating brightness (48 LEDs × 20mA × 25%)
  - Only ONE strip active at a time; safe for Pi 5V rail
  - Full white max: ~2.8A per strip (48 LEDs × 60mA) — not used

### Raspberry Pi Configuration
- **Model**: Raspberry Pi Zero 2 W
- **GPIO Interface**: BCM numbering
- **PWM Channels**:
  - Channel 0: GPIO 18 (RED) and GPIO 21 (YELLOW)
  - Channel 1: GPIO 13 (GREEN)
- **DMA Channel**: 10
- **Library**: rpi_ws281x (C library with Python bindings)

### Power Supply Requirements
- **Power Source**: Raspberry Pi power rails
  - Pin 2 (5V) → RED strip
  - Pin 4 (5V) → YELLOW strip
  - Pin 1 (3.3V) → GREEN strip
- **Current Draw**: ~240mA max (one strip active at 25% brightness)
- **Pi Power Adapter**: Use a quality 5V/2.5A+ USB adapter for the Pi
- **Wiring**:
  - Each strip has dedicated power, ground, and data pins (no sharing)
  - Keep wires short to minimize voltage drop

## Software Configuration

### GPIO Pin Mapping (from led_failsafe_manager.py)

```python
# Strip 1: RED/DANGER (GPIO 18)
RED_STRIP_PIN = 18
RED_STRIP_CHANNEL = 0

# Strip 2: YELLOW/CAUTION (GPIO 21) 
YELLOW_STRIP_PIN = 21
YELLOW_STRIP_CHANNEL = 0

# Strip 3: GREEN/SAFE (GPIO 13)
GREEN_STRIP_PIN = 13
GREEN_STRIP_CHANNEL = 1
GREEN_STRIP_ENABLED = True

# Common Settings
LED_COUNT = 48
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 65  # 0-255
LED_INVERT = False
```

## Alert Level Behavior

| Alert Level | Active Strip | GPIO Pin | Pattern | Duration |
|------------|--------------|----------|---------|----------|
| **DANGER** | RED | 18 | Blink (0.5s on/off) | 10 cycles |
| **CAUTION** | YELLOW | 21 | Blink (0.5s on/off) | 10 cycles |
| **SAFE** | GREEN | 13 | Blink (0.5s on/off) | 10 cycles |

**Important**: Only ONE strip is active at any time. Inactive strips are turned OFF.

## Safety Notes

⚠️ **Safety Information**:

1. **Pi-powered LED strips are safe in this configuration**
   - Only ONE strip is active at any time
   - Brightness is set to 65/255 (~25%) — single color only
   - Actual draw is ~240mA, well within Pi 5V rail capacity (~1.2A)
   - If you increase brightness significantly or run multiple strips simultaneously, use an external 5V PSU instead

2. **Use a quality Pi power adapter**
   - 5V / 2.5A or higher USB power adapter recommended
   - Ensures stable voltage for both Pi and LED strips

3. **Common ground is essential**
   - All strip GND wires must connect to Pi GND pins
   - Ensures proper signal levels
   - Prevents ground loops

4. **Data line protection (optional but recommended)**
   - 330-470Ω resistor in series with data line
   - Protects GPIO pins from voltage spikes
   - Not strictly required for short runs

5. **Do NOT increase LED_BRIGHTNESS above ~100 without an external PSU**
   - Higher brightness or full white (all RGB channels) draws significantly more current
   - At full brightness with all 3 strips: up to 8.4A — requires external supply

## Testing

### Verify Wiring
```bash
# Test each strip individually
sudo python3 device/test_red_blink.py
sudo python3 device/test_yellow_blink.py
sudo python3 device/test_green_blink.py

# Test all strips together
sudo python3 device/test_beach_sign_alerts.py
```

### Turn Off All LEDs
```bash
sudo python3 device/turn_off_all_leds.py
```

## Troubleshooting

### LEDs Not Lighting Up
1. Verify Pi power adapter is 5V/2.5A+ (insufficient adapter = dim or dead LEDs)
2. Verify data pin connections (GPIO 18, 21, 13)
3. Ensure all strip GND wires connect to Pi GND pins
4. Run with sudo (GPIO access requires root)
5. Check if another process is using GPIO pins

### Wrong Colors Displayed
1. Verify color order setting (GRB vs RGB)
2. Check strip type (WS2811 vs WS2812)
3. Adjust brightness if colors appear dim

### Flickering or Unstable
1. Check Pi power adapter capacity (2.5A+ recommended)
2. Minimize data wire length
3. Add capacitor (100-470µF) across strip power/ground near the strip
4. Check for loose connections
5. If flickering persists, consider external 5V PSU for strips

## Physical Installation

### Recommended Layout
```
┌────────────────────────────────────────┐
│                                        │
│            BEACH SIGN FACE             │
│                                        │
│   ╔═══════════════════════════════╗   │
│   ║    RED Strip (Top)            ║   │ ← DANGER
│   ║    48 LEDs                    ║   │
│   ╚═══════════════════════════════╝   │
│                                        │
│   ╔═══════════════════════════════╗   │
│   ║    YELLOW Strip (Middle)      ║   │ ← CAUTION
│   ║    48 LEDs                    ║   │
│   ╚═══════════════════════════════╝   │
│                                        │
│   ╔═══════════════════════════════╗   │
│   ║    GREEN Strip (Bottom)       ║   │ ← SAFE
│   ║    48 LEDs                    ║   │
│   ╚═══════════════════════════════╝   │
│                                        │
└────────────────────────────────────────┘

Raspberry Pi mounted in weatherproof enclosure on back
(LED strips powered from Pi 5V rail — no external PSU needed)
```

## References

- [rpi_ws281x Library Documentation](https://github.com/jgarff/rpi_ws281x)
- [Raspberry Pi GPIO Pinout](https://pinout.xyz/)
- [WS2812 LED Strip Specifications](https://cdn-shop.adafruit.com/datasheets/WS2812.pdf)
- [LED Safety Guide](https://learn.adafruit.com/adafruit-neopixel-uberguide/powering-neopixels)
