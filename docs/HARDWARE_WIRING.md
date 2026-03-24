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
   Pin 1 │  3V3 Power          │●      ●│  5V Power       ◄══│ Pin 2   ← +5V TO LED STRIPS
         ├─────────────────────┤        ├─────────────────────┤
   Pin 3 │  GPIO 2  (I2C SDA)  │●      ●│  5V Power       ◄══│ Pin 4   ← +5V TO LED STRIPS
         ├─────────────────────┤        ├─────────────────────┤
   Pin 5 │  GPIO 3  (I2C SCL)  │●      ●│  Ground          ■ │ Pin 6   ← GND TO LED STRIPS
         ├─────────────────────┤        ├─────────────────────┤
   Pin 7 │  GPIO 4  (GPCLK0)   │●      ●│  GPIO 14 (UART TX) │ Pin 8
         ├─────────────────────┤        ├─────────────────────┤
   Pin 9 │  Ground          ■  │●      ●│  GPIO 15 (UART RX) │ Pin 10
         ├─────────────────────┤        ├─────────────────────┤
  Pin 11 │  GPIO 17            │●      ●│  GPIO 18 (PWM0) ◄══│ Pin 12  ← 🔴 RED DATA
         ├─────────────────────┤        ├─────────────────────┤
  Pin 13 │  GPIO 27            │●      ●│  Ground          ■ │ Pin 14  ← GND TO LED STRIPS
         ├─────────────────────┤        ├─────────────────────┤
  Pin 15 │  GPIO 22            │●      ●│  GPIO 23            │ Pin 16
         ├─────────────────────┤        ├─────────────────────┤
  Pin 17 │  3V3 Power          │●      ●│  GPIO 24            │ Pin 18
         ├─────────────────────┤        ├─────────────────────┤
  Pin 19 │  GPIO 10 (SPI MOSI) │●      ●│  Ground          ■ │ Pin 20  ← GND TO LED STRIPS
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
         │  ← 🟢 GREEN DATA    │        │                     │
         ├─────────────────────┤        ├─────────────────────┤
  Pin 35 │  GPIO 19 (PCM FS)   │●      ●│  GPIO 16            │ Pin 36
         ├─────────────────────┤        ├─────────────────────┤
  Pin 37 │  GPIO 26            │●      ●│  GPIO 20 (PCM DIN)  │ Pin 38
         ├─────────────────────┤        ├─────────────────────┤
  Pin 39 │  Ground          ■  │●      ●│  GPIO 21 (PCM) ◄══ │ Pin 40
         │                     │        │  ← 🟡 YELLOW DATA   │
         └─────────────────────┘        └─────────────────────┘
```

### WaveAlert360 Pin Summary

| Physical Pin | BCM GPIO | Function | WaveAlert360 Connection |
|:---:|:---:|:---:|:---|
| **2** or **4** | — | 5V Power | +5V to all LED strip power (from Pi rail) |
| **6, 9, 14, 20, 25, 30, 34, 39** | — | Ground | GND to all LED strip grounds (use any/multiple) |
| **12** | GPIO 18 | PWM0 | 🔴 RED strip data (48 LEDs — DANGER) |
| **33** | GPIO 13 | PWM1 | 🟢 GREEN strip data (48 LEDs — SAFE) |
| **40** | GPIO 21 | PCM DOUT | 🟡 YELLOW strip data (48 LEDs — CAUTION) |

### LED Strip Wire Colors

Each WS2811/WS2812 LED strip has **3 wires**:

| Wire Color | Function | Description |
|:---:|:---:|:---|
| 🔴 **Red wire** | +5V Power | Powers the LEDs |
| ⚪ **White wire** | Ground (GND) | Common return / reference |
| 🟢 **Green wire** | Data (DIN) | Signal from Pi GPIO to strip |

### Complete Wiring Schematic

```
    ┌────────────────────────────────────────────────────────────────┐
    │                   Raspberry Pi Zero 2 W                        │
    │                    Running WaveAlert360                        │
    │                                                                │
    │   5V (Pin 2/4)    GND (Pin 6/9/14+)    GPIO Pins              │
    └───────┬──────────────────┬──────────────┬────────┬────────┬────┘
            │                  │              │        │        │
            │                  │          GPIO 18  GPIO 13  GPIO 21
            │                  │          (Pin 12) (Pin 33) (Pin 40)
            │                  │              │        │        │
            │                  │              │        │        │
     ┌──────┴──────┐    ┌──────┴──────┐       │        │        │
     │             │    │             │       │        │        │
     │  ┌──────────┼────┼─────────────┼───────┼────────┼────────┘
     │  │          │    │             │       │        │
     │  │    ┌─────┼────┼─────────────┼───────┼────────┘
     │  │    │     │    │             │       │
     │  │    │  ┌──┼────┼─────────────┼───────┘
     │  │    │  │  │    │             │
     ▼  ▼    ▼  ▼  ▼    ▼             ▼
    ┌──────────────────────────────────────────────────────────────┐
    │                                                              │
    │    🔴 RED STRIP (DANGER)        48 LEDs - GPIO 18            │
    │    ┌─────────────────────────────────────────────────────┐   │
    │    │  Red wire ──────► +5V  (from Pi Pin 2/4)            │   │
    │    │  White wire ────► GND  (from Pi GND pin)            │   │
    │    │  Green wire ────► DIN  (from Pi Pin 12 / GPIO 18)   │   │
    │    └─────────────────────────────────────────────────────┘   │
    │                                                              │
    │    🟢 GREEN STRIP (SAFE)        48 LEDs - GPIO 13            │
    │    ┌─────────────────────────────────────────────────────┐   │
    │    │  Red wire ──────► +5V  (from Pi Pin 2/4)            │   │
    │    │  White wire ────► GND  (from Pi GND pin)            │   │
    │    │  Green wire ────► DIN  (from Pi Pin 33 / GPIO 13)   │   │
    │    └─────────────────────────────────────────────────────┘   │
    │                                                              │
    │    🟡 YELLOW STRIP (CAUTION)    48 LEDs - GPIO 21            │
    │    ┌─────────────────────────────────────────────────────┐   │
    │    │  Red wire ──────► +5V  (from Pi Pin 2/4)            │   │
    │    │  White wire ────► GND  (from Pi GND pin)            │   │
    │    │  Green wire ────► DIN  (from Pi Pin 40 / GPIO 21)   │   │
    │    └─────────────────────────────────────────────────────┘   │
    │                                                              │
    └──────────────────────────────────────────────────────────────┘

    POWER FLOW:  USB adapter (5V/2.5A+) ──► Pi 5V rail ──► LED strips
    IMPORTANT:   Only ONE LED strip is ever active at a time.
```

### Per-Strip Wiring Table

| Strip | Red Wire (+5V) | White Wire (GND) | Green Wire (Data) |
|:---|:---:|:---:|:---:|
| 🔴 RED (DANGER) | Pi Pin 2 or 4 | Pi any GND pin | Pi Pin 12 (GPIO 18) |
| 🟢 GREEN (SAFE) | Pi Pin 2 or 4 | Pi any GND pin | Pi Pin 33 (GPIO 13) |
| 🟡 YELLOW (CAUTION) | Pi Pin 2 or 4 | Pi any GND pin | Pi Pin 40 (GPIO 21) |

> **Tip:** All three red wires can share the same 5V pin (Pin 2 or 4). Use separate GND pins
> (e.g., Pin 6, Pin 14, Pin 34) for each strip to distribute current, or share one if convenient.

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
