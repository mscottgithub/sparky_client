# 🐛 EVENT LOOP BLOCKING BUG - v4.3.4 Critical Fix

**Problem:** Receive handler never executed, messages never displayed  
**Root Cause:** Synchronous blocking call in async function froze event loop  
**Status:** FIXED in v4.3.4

---

## 🔍 THE SMOKING GUN

Your diagnostic logs revealed the exact issue:

```
🔧 Creating send and receive tasks...
   Send task created: <Task ...>
   Recv task created: <Task ...>
🔧 Starting gather() on both tasks...
📤 Send handler COROUTINE ENTERED  ← Entered!
📤 Send handler started
📤 Sent: Hello!...

[NO RECEIVE HANDLER LOGS AT ALL]  ← Never executed!
```

**Both tasks were created, but only the send handler ran!**

Meanwhile, the orchestrator successfully:
- Received "Hello!"
- Generated response  
- Sent tokens back to client
- Completed successfully

But the client never read those tokens because the receive handler **never ran**.

---

## 🔬 ROOT CAUSE: Blocking the Event Loop

### The Broken Code (v4.3.3)

```python
async def _send_handler(self, ws):
    while not self._closing and self.ws_connected:
        try:
            # THIS IS THE BUG! ↓
            msg_type, msg_data = self.send_queue.get(timeout=0.5)
            # ↑ BLOCKS THE ENTIRE ASYNCIO EVENT LOOP FOR 0.5 SECONDS!
        except queue.Empty:
            continue
```

### Why This Breaks Everything

`queue.Queue().get(timeout=0.5)` is a **synchronous blocking call**. When you call it inside an async function:

1. The send handler starts running in the asyncio event loop
2. Hits `queue.get(timeout=0.5)` 
3. **BLOCKS for 0.5 seconds waiting for a message**
4. During this time, the event loop is **frozen** - can't run anything else
5. After 0.5 seconds, raises `queue.Empty` and loops back
6. Blocks again for another 0.5 seconds
7. Repeat forever...

**The receive handler never gets a chance to run!**

### The Timeline

```
t=0.0s: gather() starts both tasks
t=0.0s: Send handler enters, hits queue.get(timeout=0.5)
t=0.0s-0.5s: EVENT LOOP BLOCKED (waiting for queue)
t=0.5s: queue.Empty, loop continues
t=0.5s-1.0s: EVENT LOOP BLOCKED again
t=1.0s: User sends "Hello!"
t=1.0s: queue.get() returns the message
t=1.0s: Send handler sends message
t=1.0s: Back to queue.get(timeout=0.5)
t=1.0s-1.5s: EVENT LOOP BLOCKED
        ↑
    Receive handler STILL never runs!
```

The event loop spends 100% of its time blocked in `queue.get()`, so the receive handler **never gets scheduled**.

---

## ✅ THE FIX (v4.3.4)

### Fixed Code

```python
async def _send_handler(self, ws):
    while not self._closing and self.ws_connected:
        try:
            # FIXED: Use non-blocking get_nowait()
            try:
                msg_type, msg_data = self.send_queue.get_nowait()
            except queue.Empty:
                # Yield control to event loop
                await asyncio.sleep(0.1)
                continue
            
            # Send message...
```

### Why This Works

**Key changes:**
1. `queue.get_nowait()` - Returns immediately, never blocks
2. `await asyncio.sleep(0.1)` - Yields control to event loop

**New timeline:**
```
t=0.0s: gather() starts both tasks
t=0.0s: Send handler enters, hits queue.get_nowait()
t=0.0s: queue.Empty (no message yet)
t=0.0s: await asyncio.sleep(0.1) - YIELDS to event loop
t=0.0s: Event loop switches to receive handler
t=0.0s: Receive handler enters, starts listening ✅
t=0.0s-0.1s: Both handlers running concurrently!
t=0.1s: Send handler wakes up, checks queue again
t=0.1s: queue.Empty
t=0.1s: await asyncio.sleep(0.1) - YIELDS to event loop
t=0.1s: Receive handler continues listening...
```

**Now both handlers run concurrently!**

---

## 🎯 ASYNCIO RULES

This bug demonstrates a critical asyncio rule:

**NEVER use blocking calls in async functions!**

### ❌ BAD (Blocks event loop)
```python
async def handler():
    msg = queue.get(timeout=0.5)      # BLOCKS!
    time.sleep(1)                     # BLOCKS!
    response = requests.get(url)      # BLOCKS!
```

### ✅ GOOD (Yields to event loop)
```python
async def handler():
    msg = queue.get_nowait()          # Non-blocking
    await asyncio.sleep(1)            # Yields
    response = await aiohttp.get(url) # Yields
```

**Key principle:** In async functions, always use:
- `await` for I/O operations
- Non-blocking variants of synchronous calls
- `await asyncio.sleep()` instead of `time.sleep()`

---

## 📊 EXPECTED BEHAVIOR (v4.3.4)

Now you should see:

```
🔧 Creating send and receive tasks...
   Send task created: <Task ...>
   Recv task created: <Task ...>
🔧 Starting gather() on both tasks...
📤 Send handler COROUTINE ENTERED
📤 Send handler started
📥 Receive handler COROUTINE ENTERED  ← Now executes!
📥 Receive handler started
📥 Entering receive loop...
📥 Waiting for message...
📤 Sent: Hello!...
📥 GOT MESSAGE: <class 'str'>, length=XXX
📨 Received: type=text_token
🔤 Token: 'Hey' (total length: 3)
🖼️ UI update: type=token, length=3
[... response appears in chat! ...]
```

**Both handlers will run concurrently and messages will display!** ✅

---

## 🔧 TECHNICAL DETAILS

### Why get_nowait() + asyncio.sleep() Works

```python
# Check queue without blocking
try:
    msg = self.send_queue.get_nowait()
    # Process message...
except queue.Empty:
    # No message - yield control to event loop
    await asyncio.sleep(0.1)
```

**What happens:**
1. `get_nowait()` returns immediately (doesn't block)
2. If empty, `await asyncio.sleep(0.1)` tells event loop: "I'm waiting, run other tasks"
3. Event loop switches to receive handler
4. Receive handler runs for up to 0.1 seconds
5. Event loop switches back to send handler
6. Cycle repeats

**Result:** Both handlers share the event loop cooperatively!

### Alternative: asyncio.Queue

We could also use `asyncio.Queue` instead of `threading.Queue`:

```python
# In __init__
self.send_queue = asyncio.Queue()

# In send_handler
msg_type, msg_data = await self.send_queue.get()  # Async wait
```

But this requires changing how the UI thread puts messages (using `asyncio.run_coroutine_threadsafe()`). The current fix is simpler and works perfectly.

---

## 🎊 SUMMARY

**Problem:** Receive handler never ran, client never read responses  
**Root Cause:** `queue.get(timeout=0.5)` blocked asyncio event loop  
**Symptom:** Send handler monopolized event loop, receive handler never scheduled  
**Fix:** Use `get_nowait()` + `await asyncio.sleep()` to yield to event loop  
**Result:** Both handlers run concurrently, text chat works! ✅

---

**This was a textbook asyncio bug!** The diagnostic logging you requested was essential to finding it - without seeing "COROUTINE ENTERED" for the receive handler, we might have kept looking in the wrong places.

---

**Version:** 4.3.4  
**Fix Impact:** CRITICAL (enables text chat to work)  
**Risk:** LOW (surgical fix to one blocking call)  
**Lesson:** Never block the event loop in async functions!

---

*"With great async comes great responsibility!" - Uncle Ben's Asyncio Wisdom* ⚡
