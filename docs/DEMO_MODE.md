# WaveAlert360 Demo Mode

## Overview
Demo Mode is a presentation-ready mode that **works offline** using cached configuration - perfect for demos, presentations, and trade shows where internet connectivity may be unreliable or unavailable.

## How It Works

### Cloud Control + Local Cache
1. **Edit devices.json on GitHub** - Set `"operating_mode": "DEMO"`
2. **Pi fetches config** - Raspberry Pi downloads configuration from Azure
3. **Automatic caching** - Configuration saved locally as Last Known Good (LKG)
4. **Offline resilience** - If internet drops, Pi uses cached config

### Demo Behavior
- Automatically cycles: 🟢 SAFE → 🟡 CAUTION → 🔴 DANGER → repeat
- LED blinks during each alert
- Plays full audio message for each level
- 3-second pause between scenarios

## Quick Start

### Activate Demo Mode

**Step 1:** Edit [devices.json on GitHub](https://github.com/prasannapad/wavealert360/blob/main/devices.json):

```json
{
  "mac_address": "88:a2:9e:0d:fb:17",
  "operating_mode": "DEMO",
  "demo_pause_seconds": 3,
  ...
}
```

**Step 2:** Commit and push to GitHub

**Step 3:** Wait 15 seconds - Pi automatically fetches new config and enters DEMO mode

**Step 4:** Even if WiFi disconnects, DEMO mode continues from cache!

## Configuration

### demo_pause_seconds
Time between alert scenarios (in seconds):

```json
"demo_pause_seconds": 3  // 3 seconds between SAFE → CAUTION → DANGER
```

**Recommended values:**
- **3 seconds** - Quick paced, attention-grabbing (good for 8-minute talk)
- **5 seconds** - Medium pace, audience can process each message
- **10 seconds** - Slow, detailed walkthrough

## Presentation Tips

### For California Water Safety Summit (4/15-4/16, 8 minutes)

**Setup (Day Before):**
1. At home with WiFi, change devices.json to `"operating_mode": "DEMO"`
2. Restart Pi, verify it enters DEMO mode
3. Let it run through 2-3 cycles to confirm caching works
4. Disconnect WiFi - confirm it still cycles using cache

**At Venue (No WiFi):**
1. Power on Pi - it boots into DEMO mode from cache
2. System cycles automatically during your entire presentation
3. No manual intervention needed!

**Presentation Flow:**
- **Minutes 0-2:** Introduce problem while device shows GREEN (safe)
- **Minutes 2-4:** Explain solution as it cycles to YELLOW (caution)
- **Minutes 4-6:** Technical details during RED (danger) phase
- **Minutes 6-8:** Impact discussion, cycles continue in background

Each complete cycle (~2.5 minutes) means you'll see **3 full demonstrations** during your 8-minute talk.

## Operating Modes Comparison

| Mode | Control | Internet | Best For |
|------|---------|----------|----------|
| **LIVE** | devices.json | Required (NWS API) | Production deployment |
| **TEST** | devices.json | Required (Azure) | Development/testing |
| **DEMO** | devices.json | Optional (uses cache) | Presentations/trade shows |

## Switching Modes

All modes controlled via [devices.json](https://github.com/prasannapad/wavealert360/blob/main/devices.json):

**LIVE Mode:**
```json
"operating_mode": "LIVE"
```

**TEST Mode:**
```json
"operating_mode": "TEST",
"test_scenario": "DANGER"
```

**DEMO Mode:**
```json
"operating_mode": "DEMO",
"demo_pause_seconds": 3
```

Changes take effect in **15 seconds** (next check cycle).

## Cache Behavior

### Automatic Caching
Every successful Azure response is cached to `.azure_cache.json`:
- Contains full configuration including operating mode
- Updated every 15 seconds when online
- Used automatically when offline

### What Gets Cached
```json
{
  "alert_level": "DEMO",
  "device_mode": "DEMO",
  "demo_pause_seconds": 3,
  "scenarios": [...]
}
```

### Cache Location
```
device/.azure_cache.json
```

## Troubleshooting

### "Demo not cycling"
- Check devices.json: `"operating_mode": "DEMO"`?
- Look for cache file: `device/.azure_cache.json`
- Restart Pi to fetch fresh config

### "Works online but not offline"
- Ensure Pi ran successfully online at least once to create cache
- Check cache file exists and isn't corrupted
- Review console output for cache loading messages

### Audio not playing
- Verify Bluetooth speaker is paired and charged
- Check audio files exist in `device/alert_audio/`
- Test with: `cvlc --intf dummy --play-and-exit alert_audio/normal_alert.mp3`

## Console Output Example

```
🌊 WaveAlert360 SIMPLIFIED started at 2026-02-14 10:30:00
📍 Monitoring conditions for: Cowell Ranch State Beach (37.42, -122.43)

🌐 [SERVICE] Calling Azure Function: ...
✅ [SERVICE] Response: DEMO alert
💾 [CACHE] Saved Azure response to cache

🎭 [DEMO] Starting cycling demo with 3 scenarios
⏸️  [DEMO] 3s pause between scenarios

============================================================
🎭 [DEMO] Scenario: SAFE
============================================================
🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢 [LED] SAFE
[AUDIO] Playing: normal_alert.mp3
⏸️  [DEMO] Pausing 3 seconds before next scenario...

============================================================
🎭 [DEMO] Scenario: CAUTION
============================================================
🟡🟡🟡🟡🟡🟡🟡🟡🟡🟡 [LED] CAUTION
[AUDIO] Playing: caution_alert.mp3
⏸️  [DEMO] Pausing 3 seconds before next scenario...

============================================================
🎭 [DEMO] Scenario: DANGER
============================================================
🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴 [LED] DANGER
[AUDIO] Playing: high_alert.mp3
⏸️  [DEMO] Pausing 3 seconds before next scenario...

✅ [DEMO] Complete cycle finished, will repeat on next check
```

## Best Practices

1. **Test with WiFi first** - Verify mode switch and caching work
2. **Test offline second** - Confirm cache fallback functions
3. **Charge everything** - Pi power bank, Bluetooth speaker
4. **Arrive early** - Test at venue 30 minutes before presentation
5. **Have backup** - Phone video of working demo as last resort

---

**For Questions:** See [README.md](../README.md) or [OPERATION_MODES.md](OPERATION_MODES.md)
