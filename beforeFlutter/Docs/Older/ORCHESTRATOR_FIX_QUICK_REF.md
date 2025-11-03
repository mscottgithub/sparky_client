# 🎯 Quick Fix - Orchestrator WebSocket Disconnect

## THE PROBLEM
```
RuntimeError: Cannot call "receive" once a disconnect message has been received.
```

Happens when: User closes chat window → orchestrator tries to receive again → error

---

## THE FIX

### Line 545 - Add disconnect check

**Before:**
```python
while True:
    msg = await ws.receive()
    
    if "text" in msg:
        # process message
```

**After:**
```python
while True:
    msg = await ws.receive()
    
    # NEW: Check for disconnect
    if msg.get("type") == "websocket.disconnect":
        log.info(f"[{session.session_id}] Client disconnected")
        break  # Exit cleanly
    
    if "text" in msg:
        # process message
```

### Exception handler - Better logging

**Add RuntimeError catch:**
```python
except WebSocketDisconnect:
    log.info(f"[{session.session_id}] Client disconnected")
except RuntimeError as e:
    if "disconnect message has been received" in str(e):
        log.info(f"[{session.session_id}] Client disconnected (late detection)")
    else:
        log.error(f"[{session.session_id}] ❌ RuntimeError: {e}", exc_info=True)
```

---

## DEPLOY

```bash
# Backup
sudo cp /home/mintdude/Github/sparky/voice-ai-service/sparky_orchestrator_ws.py \
        /home/mintdude/Github/sparky/voice-ai-service/sparky_orchestrator_ws.py.backup

# Deploy
sudo cp sparky_orchestrator_ws_v2.3.1.py \
        /home/mintdude/Github/sparky/voice-ai-service/sparky_orchestrator_ws.py

# Restart
sudo systemctl restart sparky-orchestrator

# Watch logs
sudo journalctl -u sparky-orchestrator -f
```

---

## TEST

1. Open chat window
2. Send a message
3. Close chat window
4. **Expected:** No RuntimeError in logs
5. **Expected:** See "Client disconnected" message

---

## RESULT

**Before:**
```
[ERROR] ❌ Error: Cannot call "receive"...
RuntimeError: Cannot call "receive"...
```

**After:**
```
[INFO] Client disconnected (disconnect message received)
```

Clean logs! ✅

---

**File:** `sparky_orchestrator_ws_v2.3.1.py`  
**Version:** v2.3.0 → v2.3.1  
**Status:** Ready to deploy
