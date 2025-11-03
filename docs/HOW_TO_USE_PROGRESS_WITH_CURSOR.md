# How to Use PROGRESS.md with Cursor

This guide explains how to make Cursor automatically track your development progress.

---

## 🎯 The Problem This Solves

**Cursor doesn't remember between sessions.** Each time you close and reopen Cursor, it "forgets" what you've built. This makes it hard to pick up where you left off.

**Solution:** Use `PROGRESS.md` as Cursor's "memory" - a file it reads and updates to track what's done.

---

## 🚀 How It Works

### **Every Cursor Session:**

1. **Cursor reads** `docs/PROGRESS.md` to see what's already done
2. **Cursor works** on the next task in the list
3. **Cursor updates** `PROGRESS.md` to mark tasks complete
4. **You commit** the changes to git

**Result:** The file becomes the "memory" of what's been accomplished!

---

## 📋 Starting a New Cursor Session

### **Copy this prompt at the start of EVERY session:**

```
I'm working on the Sparky Flutter client.

SESSION RULES:
1. First, read docs/PROGRESS.md to see what's already completed
2. Then read docs/FLUTTER_MIGRATION_PLAN_v1_1.md to understand the full plan
3. Tell me what we should work on next
4. After completing EACH task:
   - Update docs/PROGRESS.md
   - Change [ ] to [x] for completed tasks
   - Add completion timestamp
   - Add brief notes about what was done
5. Always reference docs/FLUTTER_RIVERPOD_ARCHITECTURE_HANDOFF.md 
   for code patterns and architecture

Start by reading docs/PROGRESS.md and telling me our current status 
and what we should work on next.
```

---

## 💡 What Cursor Will Do

**Cursor will respond something like:**

```
I've reviewed PROGRESS.md. Current status:

✅ COMPLETED:
- Day 1: Project setup and structure (completed Nov 4, 10:30 AM)
- Day 2: WebSocket service (completed Nov 4, 3:45 PM)

🔄 IN PROGRESS:
- Day 2: Desktop UX - completed keyboard shortcuts, 
  still need right-click context menus

📋 NEXT UP:
- Complete right-click context menus for text fields
- Add connection status indicator
- Start Day 3: Text chat UI

Should I continue with the right-click context menus?
```

**Then you say:** "Yes, do it"

**Cursor will:**
1. Write the code
2. Test it works
3. Update `docs/PROGRESS.md` to mark it complete

---

## 📝 Example of Updated PROGRESS.md

**Before Cursor updates it:**
```markdown
### Day 2: WebSocket Connection + Desktop UX
- [x] Create text_websocket_service.dart
- [ ] Desktop UX Foundation:
  - [x] Keyboard shortcuts
  - [ ] Right-click context menus
```

**After Cursor completes the task:**
```markdown
### ✅ Day 2: WebSocket Connection + Desktop UX (Status: COMPLETED)
- [x] Create text_websocket_service.dart
- [x] Desktop UX Foundation:
  - [x] Keyboard shortcuts (completed Nov 4, 2:15 PM)
  - [x] Right-click context menus (completed Nov 4, 4:30 PM)

**Completion Notes:**
Right-click context menus implemented with Copy, Paste, Cut, 
Select All options. Tested on Windows 11. Works with all text fields.
```

---

## 🔄 Daily Workflow

### **Morning - Start of Day:**

1. Open Cursor
2. Open `D:\NCScott\sparky_client`
3. Press `Ctrl+L` to open chat
4. Paste the session rules prompt (see above)
5. Cursor tells you where you left off
6. Continue working

### **During the Day:**

- Ask Cursor to build features
- Cursor automatically updates PROGRESS.md
- Check PROGRESS.md occasionally to see what's done

### **End of Day:**

```bash
# Commit your progress
git add .
git commit -m "Day 2: Completed WebSocket service and desktop UX"
git push
```

**That's it!** Tomorrow, Cursor reads PROGRESS.md and knows exactly where to pick up.

---

## 🎯 Pro Tips

### **1. Be Specific About Updates**

When asking Cursor to do something:
```
✅ GOOD: "Create the WebSocket service following 
docs/FLUTTER_RIVERPOD_ARCHITECTURE_HANDOFF.md, 
then update PROGRESS.md"

❌ BAD: "Make a WebSocket thing"
```

### **2. Check Progress Regularly**

```
You: "Show me what's completed today"
Cursor: [reads PROGRESS.md and summarizes]
```

### **3. Use for Planning**

```
You: "What are our blockers according to PROGRESS.md?"
Cursor: [reads blockers section, tells you what's blocking]
```

### **4. Reference Specific Days**

```
You: "Read Day 3 tasks from PROGRESS.md and start working on them"
Cursor: [reads Day 3, starts first incomplete task]
```

---

## 🚨 Important Reminders

### **Always Include the Session Rules**

Start EVERY Cursor session with the session rules prompt. Otherwise Cursor won't know to:
- Read PROGRESS.md
- Update it after completing tasks
- Follow the project architecture

### **Commit Regularly**

```bash
# After completing each major feature
git add docs/PROGRESS.md
git commit -m "Updated progress: completed WebSocket service"
git push
```

This ensures:
- Progress is backed up
- You have history of what was built when
- You can roll back if needed

### **Review Weekly**

At the end of each week:
1. Read through PROGRESS.md
2. Verify everything marked complete is actually working
3. Update any missing notes
4. Plan next week's tasks

---

## 📊 Example Full Session

**You open Cursor and paste:**
```
I'm working on Sparky Flutter client.
SESSION RULES: [paste the full rules from above]
```

**Cursor responds:**
```
Current status from PROGRESS.md:
- Week 1 Day 1: ✅ Complete
- Week 1 Day 2: 🔄 75% complete, missing right-click menus
- Week 1 Day 3: ⏸️ Not started

Next task: Complete Day 2 right-click context menus.
Should I proceed?
```

**You:** "Yes"

**Cursor:** *creates the code, tests it*
```
I've implemented right-click context menus with Copy, Paste, 
Cut, Select All. Updated PROGRESS.md to mark Day 2 complete.

Next up: Day 3 - Text Chat UI. Ready to start?
```

**You:** "Yes, let's do it"

**And so on...**

---

## ✅ You're All Set!

With this system:
- ✅ Cursor always knows what's done
- ✅ Cursor always knows what's next
- ✅ You never lose track of progress
- ✅ You can pick up exactly where you left off

**Just remember:** Start every session with the session rules prompt!

---

**Questions?** Come back to Claude Projects and ask! I remember everything we discuss and can help guide you through using this system.
