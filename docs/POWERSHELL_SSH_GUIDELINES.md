# PowerShell SSH Command Guidelines
# =================================
# CRITICAL: Avoid quote hell when using SSH commands from PowerShell

## ❌ NEVER DO THIS (causes quote mangling):
```powershell
ssh pi@host "python3 -c 'print(\"hello\")'"
ssh pi@host "echo 'some text with \"quotes\"' > file.py"
```

## ✅ ALWAYS DO THIS INSTEAD:

### For Python commands:
```powershell
# Create a script file first, then run it
ssh pi@host "echo 'print(\"Hello World\")' > /tmp/test.py && python3 /tmp/test.py"

# Or use simple commands without nested quotes
ssh pi@host "python3 --version"
ssh pi@host "python3 main.py"
```

### For testing imports:
```powershell
# Create test script on Pi first
ssh pi@host "cat > /tmp/test.py << 'EOF'
import helpers
print('Import successful')
EOF"

# Then run it
ssh pi@host "python3 /tmp/test.py"
```

### For file creation:
```powershell
# Use heredoc instead of echo with quotes
ssh pi@host "cat > filename.py << 'EOF'
your python code here
no quote issues
EOF"
```

## Key Rules:
1. **Avoid nested quotes** in SSH commands from PowerShell
2. **Use heredoc (`<< 'EOF'`)** for multi-line content
3. **Create files first, then execute** instead of inline commands
4. **Test simple commands first** before complex ones
5. **Use background processes** (`isBackground: true`) for long-running commands

## Emergency Debugging:
```powershell
# Check if Python works at all
ssh pi@host "python3 --version"

# Check if file exists
ssh pi@host "ls -la /path/to/file"

# Check basic import without quotes
ssh pi@host "cd ~/WaveAlert360/device && python3 main.py"
```

## For WaveAlert360 specifically:
- Run `main.py` directly: `ssh pi@host "cd ~/WaveAlert360/device && python3 main.py"`
- Use background mode for continuous processes
- Check web dashboard: `curl http://192.168.86.38:5000/status`
