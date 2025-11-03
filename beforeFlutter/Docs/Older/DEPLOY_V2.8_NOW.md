# ⚡ QUICK DEPLOY - Orchestrator v2.8

**Time to deploy:** 2 minutes  
**Risk level:** LOW (easy rollback)

---

## 🚀 DEPLOY NOW

```bash
# 1. Backup current version
cd /home/mintdude/Github/sparky/voice-ai-service
cp sparky_orchestrator_ws.py sparky_orchestrator_ws_v2.7_backup.py

# 2. Copy from Windows (or download from chat)
# Upload sparky_orchestrator_ws_v2.8.py to server, then:
cp sparky_orchestrator_ws_v2.8.py sparky_orchestrator_ws.py

# 3. Restart
sudo systemctl restart sparky-orchestrator

# 4. Verify
curl http://10.6.1.15:8006/health | jq '.version'
```

**Expected output:** `"2.8.0"`

---

## 🎯 WHAT IT FIXES

- ✅ AI self-conversations (hiking trails example)
- ✅ Special tokens (`<|reserved_special_token_92|>`)
- ✅ Responses too long (now 2-3 sentences max)
- ✅ Version reporting (now shows 2.8.0)

---

## 🔍 WATCH LOGS

```bash
sudo journalctl -u sparky-orchestrator -f
```

**Look for:** `🛑 LLM generation finished: reason=stop`

---

## 🔄 ROLLBACK (if needed)

```bash
cd /home/mintdude/Github/sparky/voice-ai-service
cp sparky_orchestrator_ws_v2.7_backup.py sparky_orchestrator_ws.py
sudo systemctl restart sparky-orchestrator
```

---

**Full details:** See ORCHESTRATOR_V2.8_CHANGES.md
