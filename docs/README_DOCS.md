# Sparky Flutter Client - Documentation Package

This folder contains all the project documentation from Claude Projects. Copy this entire `docs` folder to your Flutter project.

## Installation

```bash
# Copy this docs folder to your project:
# From: (wherever you downloaded this)
# To: D:\NCScott\sparky_client\docs\
```

---

## 📋 Core Documentation Files

### **Architecture & Planning**

**FLUTTER_RIVERPOD_ARCHITECTURE_HANDOFF.md** (43KB) ⭐ **MOST IMPORTANT**
- Complete Riverpod architecture blueprint
- Provider structure and patterns
- Service layer design
- WebSocket message protocol
- Code examples and patterns
- **USE THIS:** When building any service or provider in Cursor

**FLUTTER_MIGRATION_PLAN_v1_1.md** (24KB) ⭐ **PHASE-BY-PHASE PLAN**
- 4-week migration plan with v1.1 adjustments
- Week-by-week implementation guide
- Critical checkpoints and blockers
- Audio latency testing (Day 3)
- Memory profiling (Week 2 Day 5)
- **USE THIS:** To know what to build next

**FLUTTER_QUICK_REFERENCE_v1_1.md** (17KB) ⭐ **QUICK LOOKUP**
- Package dependencies
- Project structure
- Commands and workflows
- Success criteria for each phase
- **USE THIS:** When you need quick answers

---

### **Storage & Data**

**FLUTTER_STORAGE_STRATEGY.md** (6KB)
- How to handle session persistence
- Conversation history storage
- Settings management
- SharedPreferences vs SQLite decisions

---

### **Setup & Installation**

**FLUTTER_SETUP_WINDOWS11.md** (17KB)
- Step-by-step Flutter installation on Windows 11
- Visual Studio requirements
- Troubleshooting common issues
- **Already completed** - kept for reference

---

### **Code Translation**

**FLUTTER_CODE_TRANSLATION_GUIDE.md** (22KB)
- PyQt6 → Flutter translation patterns
- Widget equivalents
- Threading → async/await conversions
- State management comparisons

---

### **Backend Reference**

**higgs_local_server.py** (28KB)
- Python orchestrator service code
- WebSocket protocol implementation
- Reference for understanding message formats
- **DON'T RUN THIS** - it's for reference only

---

### **Status & History**

**PROJECT_STATUS_SUMMARY.md** (11KB)
- Current project state
- Completed milestones
- Known issues

**SESSION_HANDOFF_FLUTTER_DECISION.md** (10KB)
- Why we chose Flutter over PyQt6
- Decision rationale
- Pros/cons analysis

**README_FLUTTER_MIGRATION.md** (14KB)
- Migration overview
- High-level strategy

**PLAN_ADJUSTMENTS_SUMMARY.md** (8KB)
- Changes made to original plan
- Why v1.1 adjustments were needed

**FLUTTER-PLAN-Adjustment.txt** (1KB)
- Brief adjustment notes

**SESSION_QUICK_START.md** (2KB)
- Quick start for new sessions

---

## 🎯 How to Use These in Cursor

### **When Starting a New Feature:**
```
You in Cursor: "Create the WebSocket service following the 
architecture in docs/FLUTTER_RIVERPOD_ARCHITECTURE_HANDOFF.md"
```

### **When Stuck:**
```
You in Cursor: "Check docs/FLUTTER_QUICK_REFERENCE_v1_1.md for 
the correct package to use for audio recording"
```

### **When Planning Next Steps:**
```
You in Cursor: "What should I build next according to 
docs/FLUTTER_MIGRATION_PLAN_v1_1.md?"
```

---

## 📁 Recommended Project Structure

After copying these docs, your project should look like:

```
D:\NCScott\sparky_client\
├── docs/                    # ← This folder!
│   ├── README_DOCS.md       # This file
│   ├── FLUTTER_RIVERPOD_ARCHITECTURE_HANDOFF.md  # ⭐
│   ├── FLUTTER_MIGRATION_PLAN_v1_1.md            # ⭐
│   ├── FLUTTER_QUICK_REFERENCE_v1_1.md           # ⭐
│   ├── FLUTTER_STORAGE_STRATEGY.md
│   ├── FLUTTER_CODE_TRANSLATION_GUIDE.md
│   ├── (... all other docs ...)
│   └── higgs_local_server.py
├── lib/                     # Flutter code
├── test/                    # Tests
├── pubspec.yaml
└── README.md
```

---

## 💡 Pro Tips for Cursor

1. **Reference docs explicitly:**
   - "Following the pattern in docs/FLUTTER_RIVERPOD_ARCHITECTURE_HANDOFF.md..."
   - This tells Cursor exactly which file to read

2. **Attach relevant docs:**
   - Use Cursor's @ symbol to attach specific docs to your chat
   - @docs/FLUTTER_MIGRATION_PLAN_v1_1.md

3. **Keep docs updated:**
   - As you make architectural decisions, update the docs
   - Cursor will always see the latest version

---

## 🔄 Keeping in Sync

**When architecture changes:**
1. Discuss in Claude Projects (claude.ai)
2. Update the relevant doc file
3. Copy updated file back to your project's docs folder
4. Cursor now sees the changes

---

## ⚠️ Important Notes

- **higgs_local_server.py**: This is backend code, don't try to run it in your Flutter project
- **Older versions**: Some files have v1.1 versions - always use the latest version
- **Don't delete**: Keep all docs even if you think you won't need them - disk space is cheap, context is valuable

---

## 🚀 Ready to Start

You now have all the documentation Cursor needs to help you build the Sparky Flutter client!

**First command to try in Cursor:**
```
"Review docs/FLUTTER_MIGRATION_PLAN_v1_1.md and tell me what 
we should build first for Week 1, Day 1"
```

---

**Total Documentation Size:** ~275KB
**Files:** 15 documents + this README
**Last Updated:** November 3, 2025
