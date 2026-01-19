# WaveAlert360 - Development Tools

## 🛠️ Purpose
This folder contains files used for **development and testing only**. These do NOT go on the Raspberry Pi.

## 📁 Contents

### **Testing Tools:**
- `test_led_demo.py` - LED pattern testing
- `test_mock_api.py` - Mock API testing  
- `test_scenarios.py` - Alert scenario testing

### **Development Utilities:**
- `coastal_alert_search.py` - Search coastal alerts manually
- `save_nws_data.py` - Save NWS data for analysis
- `fix_leds.py` / `update_leds.py` - LED debugging tools

### **Legacy Files:**
- `config_old.py` / `config_fixed.py` - Old configuration approaches
- `generate_audio.*` - Local audio generation (replaced by Azure Function)
- `gen_audio.py` / `quick_audio.py` - Audio generation scripts

### **Documentation:**
- `README_AUDIO.md` - Audio system documentation

## 🚫 Do NOT Deploy
These files should stay on development machines and NOT be copied to production Raspberry Pi devices.

## 🎯 Usage
Use these tools during development, testing, and debugging phases.
