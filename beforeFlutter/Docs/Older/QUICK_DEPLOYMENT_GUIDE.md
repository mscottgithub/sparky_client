# ⚡ Quick Deployment Guide - PyQt6 Edition

## 🚀 Deploy in 5 Minutes

---

## Step 1: Install PyQt6 (2 minutes)

```powershell
cd D:\NCScott\VoiceAI-Client
pip install PyQt6
```

**Expected output:**
```
Successfully installed PyQt6-6.x.x PyQt6-sip-x.x.x
```

---

## Step 2: Backup Current Version (30 seconds)

```powershell
copy sparky_tray_client.py sparky_tray_client_v4.3.8_backup.py
```

---

## Step 3: Deploy New Version (1 minute)

**Option A: Download from browser**
1. Download `sparky_tray_client_pyqt6.py` from outputs
2. Copy to `D:\NCScott\VoiceAI-Client\`
3. Rename to `sparky_tray_client.py`

**Option B: Direct replace**
```powershell
# If you have the file locally
copy sparky_tray_client_pyqt6.py sparky_tray_client.py
```

---

## Step 4: Test (1 minute)

```powershell
python sparky_tray_client.py
```

**Expected:**
```
🚀 Starting Sparky Voice AI v5.0.0 (PyQt6 Edition)...
📂 Models: D:\NCScott\VoiceAI-Client\wake_models
🛑 Exit: Voice word OR ESC key
🔇 Echo cancellation: Enabled
⏳ Audio buffer: 4.0s + 1s wait

🔗 v5.0 PYQT6 TEXT CHAT + ORCHESTRATOR:
   ✓ Professional PyQt6 chat window
   ✓ Native right-click menus
   ✓ Perfect text selection
   ✓ Server-side conversation management
   ✓ Connected to: ws://10.6.1.15:8006/ws/conversation

🎤 Starting audio stream...
🎤 Calibrating microphone...
   Please remain quiet for 2.0 seconds...
✓ Calibration complete
👂 Listening for 'Hey Jarvis'...
```

---

## Step 5: Verify Chat Window (1 minute)

1. Right-click tray icon
2. Click "💬 Open Text Chat"
3. Window opens (PyQt6 style)
4. Type "Hello"
5. Press Enter
6. AI responds

**Success indicators:**
- ✅ Window looks modern (not Windows 95)
- ✅ Text selection works smoothly
- ✅ Right-click shows menu with Copy/Select All
- ✅ Copy actually works
- ✅ Theme toggle works

---

## ✅ Deployment Complete!

If all 5 steps passed: **YOU'RE DONE!** 🎉

---

## 🆘 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'PyQt6'"

```powershell
pip install PyQt6 --force-reinstall
```

### Chat window doesn't open

Check console for errors. Most common:
1. PyQt6 not installed → Run `pip install PyQt6`
2. Port 8006 not accessible → Check orchestrator is running
3. Config file missing → Copy config.ini from backup

### Right-click menu doesn't appear

**This should NEVER happen with PyQt6.** If it does:
1. Verify you're running the PyQt6 version:
   ```powershell
   python -c "from sparky_tray_client import VERSION; print(VERSION)"
   ```
   Should print: `5.0.0`

2. If not, you're running the old Tkinter version. Redeploy.

### Text selection doesn't work

**This should NEVER happen with PyQt6.** If it does:
1. Restart the app
2. Check PyQt6 is actually installed:
   ```powershell
   python -c "import PyQt6; print('OK')"
   ```

---

## 🔄 Rollback (if needed)

If something breaks:

```powershell
copy sparky_tray_client_v4.3.8_backup.py sparky_tray_client.py
python sparky_tray_client.py
```

You're back to Tkinter. No harm done.

---

## 🎯 What to Test

### Critical Path (must work):
1. [ ] App starts
2. [ ] Tray icon appears
3. [ ] Chat window opens
4. [ ] Can send text message
5. [ ] AI responds
6. [ ] Text selection works
7. [ ] Right-click menu works
8. [ ] Voice mode works

### Nice to Have (should work):
1. [ ] Theme switching
2. [ ] Export chat
3. [ ] Clear chat
4. [ ] New chat
5. [ ] Voice + text in same conversation
6. [ ] Quit cleanly

---

## 📊 Performance Check

After 10 minutes of use:

1. **Memory:** Should be ~120-150MB  
   Check: Task Manager → Details → python.exe
   
2. **CPU:** Should be <5% when idle  
   Check: Task Manager → Performance → CPU

3. **Response time:** <2 seconds for text messages  
   Test: Type message → measure until response starts

If any of these fail, report the specific issue.

---

## 🎨 Visual Verification

### Light Theme
- Background: Darker purple (#C4C4D8)
- User messages: Blue bubbles
- AI messages: Lighter purple bubbles
- Input: Light purple (NO WHITE)

### Dark Theme
- Background: Dark gray (#2B2B2B)
- User messages: Darker blue bubbles
- AI messages: Medium gray bubbles
- Input: Dark gray

Both should look **modern and professional**, NOT like Windows 95.

---

## 📝 Post-Deployment Checklist

- [ ] PyQt6 installed
- [ ] Backup created
- [ ] New version deployed
- [ ] App starts without errors
- [ ] Chat window works
- [ ] Right-click menu works
- [ ] Text selection works
- [ ] Voice mode still works
- [ ] Can quit cleanly
- [ ] Performance acceptable

**All checked?** Deployment successful! ✅

---

## 🔮 Next Steps

### Immediate (Today)
Use the new chat window. Get comfortable with it.

### This Week
Test all features:
- Voice conversations
- Text conversations
- Mixed mode (voice + text)
- Export/import
- Theme switching

### Next Session
Pick one:
1. **Fix AI rambling** (high impact, 1-2 hours)
2. **Optimize XTTS streaming** (original priority, 2-4 hours)
3. **Higgs streaming rewrite** (ambitious, 4-8 hours)

---

## 🎉 Welcome to PyQt6!

You now have:
- ✅ Professional UI that "just works"
- ✅ Native right-click menus (zero code)
- ✅ Perfect text selection (zero code)
- ✅ Modern Windows 11 styling
- ✅ Same rock-solid voice engine
- ✅ Foundation for future features

**Tkinter is history. PyQt6 is your future.** 🚀

---

**Questions?** Check the detailed migration guide or comparison document.

**Problems?** Rollback is one command away. Zero risk.

**Ready?** Let's deploy! ⚡

