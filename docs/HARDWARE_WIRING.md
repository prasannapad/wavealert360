# WaveAlert360 Hardware Wiring Guide

## LED Strip Wiring Diagram

### Overview
WaveAlert360 uses three independent WS2811/WS2812 addressable LED strips (48 LEDs each) controlled by a Raspberry Pi Zero 2 W.

### Pin Configuration

```
┌─────────────────────────────────────────────────────────────┐
│                    Raspberry Pi Zero 2 W                     │
│                      GPIO Pinout (Top View)                  │
│                                                              │
│   3V3  ●●  5V     Pin 1-2     Power Rails                   │
│   GPIO2 ●●  5V    Pin 3-4     (5V for LED strip power)      │
│   GPIO3 ●●  GND   Pin 5-6                                   │
│   GPIO4 ●●  GPIO14 Pin 7-8                                  │
│   GND   ●●  GPIO15 Pin 9-10                                 │
│   GPIO17●●  GPIO18 Pin 11-12  ◄── RED LED Strip Data        │
│   GPIO27●●  GND   Pin 13-14                                 │
│   GPIO22●●  GPIO23 Pin 15-16                                │
│   3V3   ●●  GPIO24 Pin 17-18                                │
│   GPIO10●●  GND   Pin 19-20                                 │
│   GPIO9 ●●  GPIO25 Pin 21-22                                │
│   GPIO11●●  GPIO8  Pin 23-24                                │
│   GND   ●●  GPIO7  Pin 25-26                                │
│   ID_SD ●●  ID_SC  Pin 27-28                                │
│   GPIO5 ●●  GND   Pin 29-30                                 │
│   GPIO6 ●●  GPIO12 Pin 31-32                                │
│   GPIO13●●  GND   Pin 33-34   ◄── GREEN LED Strip Data      │
│   GPIO19●●  GPIO16 Pin 35-36                                │
│   GPIO26●●  GPIO20 Pin 37-38                                │
│   GND   ●●  GPIO21 Pin 39-40  ◄── YELLOW LED Strip Data     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### LED Strip Connections

```
Raspberry Pi                    LED Strips (WS2811/WS2812)
━━━━━━━━━━━━━                  ━━━━━━━━━━━━━━━━━━━━━━━━━━━

Pin 12 (GPIO 18) ────────────► RED Strip Data Pin
                                (48 LEDs - DANGER Alert)
                                
Pin 40 (GPIO 21) ────────────► YELLOW Strip Data Pin
                                (48 LEDs - CAUTION Alert)
                                
Pin 33 (GPIO 13) ────────────► GREEN Strip Data Pin
                                (48 LEDs - SAFE Alert)

Pin 6, 9, 14, etc ────────────► Common Ground (GND)
(Any GND pin)                   Connect to all strip grounds

Pin 2 or 4 (5V) ──────────────► LED Strip Power (+5V)
                                Powered directly from Pi 5V rail
                                (Safe at low brightness, 1 strip active)
```

### Complete Wiring Schematic

```
                    ┌────────────────────────────────────────┐
                    │        Raspberry Pi Zero 2 W           │
                    │         Running WaveAlert360           │
                    │                                        │
                    │  5V (Pin 2/4)  GND (Pin 6/9/14/etc)   │
                    │      │              │                  │
                    │  GPIO18  GPIO21  GPIO13                │
                    │  (Pin12) (Pin40) (Pin33)               │
                    └────┬──────┬───────┬──────┬────────┬───┘
                         │      │       │     +5V      GND
                       Data    Data    Data    │        │
                         │      │       │      │        │
                         ▼      ▼       ▼      │        │
                    ┌──────┐┌──────┐┌──────┐   │        │
                    │ RED  ││YELLOW││GREEN │   │        │
                    │Strip ││Strip ││Strip │   │        │
                    │ 48   ││ 48   ││ 48   │   │        │
                    │ LEDs ││ LEDs ││ LEDs │   │        │
                    └──┬─┬─┘└──┬─┬─┘└──┬─┬─┘   │        │
                     +5V GND +5V GND +5V GND   │        │
                       │  │    │  │    │  │     │        │
                       └──┼────┘──┼────┘──┼─────┘        │
                          └───────┴───────┴──────────────┘

    All LED strip +5V lines connect to Pi 5V (Pin 2 or 4)
    All LED strip GND lines connect to Pi GND pins
    Only ONE strip is active at any time (safe for Pi power)
```

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
- **Power Source**: Raspberry Pi 5V rail (Pin 2 or Pin 4)
- **Current Draw**: ~240mA max (one strip active at 25% brightness)
- **Pi Power Adapter**: Use a quality 5V/2.5A+ USB adapter for the Pi
- **Wiring**:
  - Connect all strip +5V wires to Pi 5V pin (Pin 2 or 4)
  - Connect all strip GND wires to Pi GND pins
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
