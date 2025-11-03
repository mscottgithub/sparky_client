# ðŸªŸ Flutter Setup Guide for Windows 11

**Version:** 1.0  
**Date:** November 2, 2025  
**Target:** Windows 11 development machine  
**Purpose:** Complete Flutter installation for Sparky client development

---

## ðŸ“‹ Table of Contents

1. [System Requirements](#system-requirements)
2. [Pre-Installation Checklist](#pre-installation-checklist)
3. [Install Flutter SDK](#install-flutter-sdk)
4. [Install Visual Studio 2022](#install-visual-studio-2022)
5. [Configure Flutter](#configure-flutter)
6. [Install Development Tools](#install-development-tools)
7. [Create First Flutter Project](#create-first-project)
8. [Troubleshooting](#troubleshooting)
9. [Verification Checklist](#verification-checklist)

---

## ðŸ’» System Requirements

### Minimum Requirements
- **OS:** Windows 10 (64-bit) or later (Windows 11 recommended)
- **CPU:** x64 (Intel/AMD) or ARM64
- **RAM:** 4 GB minimum, 8 GB recommended
- **Disk Space:** 10 GB free (2.5 GB for Flutter SDK, rest for tools)
- **PowerShell:** Version 5.0 or later (pre-installed on Windows 11)

### Check Your System

1. **Open PowerShell** (Win + X, then select "Windows PowerShell" or "Terminal")

2. **Check Windows version:**
   ```powershell
   winver
   ```
   Should show Windows 11 (or 10)

3. **Check PowerShell version:**
   ```powershell
   $PSVersionTable.PSVersion
   ```
   Should be 5.0 or higher

4. **Check available disk space:**
   ```powershell
   Get-PSDrive C | Select-Object Used,Free
   ```
   Should have at least 10 GB free on C: drive

---

## âœ… Pre-Installation Checklist

Before installing Flutter, ensure:

- [ ] You have **administrator access** on your Windows machine
- [ ] Your **internet connection** is stable (will download ~2 GB)
- [ ] Your **antivirus** is configured to allow downloads (may flag Flutter tools)
- [ ] You have a **code editor** ready (VS Code recommended)
- [ ] **Git** is installed (required for Flutter SDK management)

### Install Git (If Not Already Installed)

1. Download Git from: https://git-scm.com/download/win

2. Run installer with these options:
   - âœ… Use Git from the Windows Command Prompt
   - âœ… Checkout Windows-style, commit Unix-style line endings
   - âœ… Use Windows' default console window

3. Verify installation:
   ```powershell
   git --version
   ```
   Should show: `git version 2.x.x`

---

## ðŸ“¥ Install Flutter SDK

### Option A: Using Git Clone (Recommended)

This method makes updates easier.

1. **Choose installation location**
   
   Recommended: `C:\src\flutter`
   
   **âš ï¸ IMPORTANT:** 
   - Do NOT install in `C:\Program Files\` (permission issues)
   - Do NOT install in a path with spaces
   - Do NOT install in a path requiring special privileges

2. **Open PowerShell as Administrator**
   
   Win + X â†’ "Terminal (Admin)" or "Windows PowerShell (Admin)"

3. **Create source directory:**
   ```powershell
   New-Item -ItemType Directory -Path C:\src -Force
   cd C:\src
   ```

4. **Clone Flutter repository:**
   ```powershell
   git clone https://github.com/flutter/flutter.git -b stable
   ```
   
   This will take 5-10 minutes depending on internet speed.

5. **Verify download:**
   ```powershell
   dir C:\src\flutter
   ```
   Should see folders like: `bin`, `packages`, `examples`

### Option B: Using ZIP Download (Alternative)

If Git clone fails or you prefer ZIP:

1. Download Flutter SDK from: https://docs.flutter.dev/get-started/install/windows

2. Extract to `C:\src\flutter`

3. **âš ï¸ Important:** Right-click `flutter` folder â†’ Properties â†’ Unblock (if present)

---

## ðŸ”§ Configure Flutter

### Step 1: Add Flutter to PATH

1. **Open Environment Variables:**
   
   Win + R â†’ type `sysdm.cpl` â†’ Enter â†’ "Advanced" tab â†’ "Environment Variables"

2. **Find "Path" variable:**
   
   - Under "User variables" (top section), select "Path"
   - Click "Edit"

3. **Add Flutter bin directory:**
   
   - Click "New"
   - Enter: `C:\src\flutter\bin`
   - Click "OK" on all dialogs

4. **Verify PATH addition:**
   
   Close ALL PowerShell/Command Prompt windows, then open a new one:
   ```powershell
   flutter --version
   ```
   
   Should show something like:
   ```
   Flutter 3.x.x â€¢ channel stable
   Tools â€¢ Dart 3.x.x â€¢ DevTools 2.x.x
   ```

### Step 2: Run Flutter Doctor

This diagnostic tool checks your environment.

```powershell
flutter doctor
```

**Expected output (initial run):**
```
Doctor summary (to see all details, run flutter doctor -v):
[âœ“] Flutter (Channel stable, 3.x.x, on Microsoft Windows 11)
[âœ—] Windows Version (Unable to confirm if installed Windows version is 10 or greater)
[âœ—] Android toolchain - develop for Android devices
    âœ— Unable to locate Android SDK.
[âœ—] Chrome - develop for the web
[âœ—] Visual Studio - develop Windows apps
    âœ— Visual Studio not installed
[âœ“] Connected device (0 available)
```

**Don't worry about the âœ— marks yet!** We'll fix them.

### Step 3: Disable Analytics (Optional but Recommended)

```powershell
flutter config --no-analytics
dart --disable-analytics
```

This prevents Flutter from sending usage data to Google.

---

## ðŸ› ï¸ Install Visual Studio 2022

**Required for Windows desktop app development.**

### Why Visual Studio?

Flutter needs Visual Studio's C++ tools to compile Windows apps. You don't need the full IDE (just the build tools).

### Installation Steps

1. **Download Visual Studio 2022 Community**
   
   https://visualstudio.microsoft.com/downloads/
   
   Click "Free download" under "Community 2022"

2. **Run the installer**
   
   File: `VisualStudioSetup.exe`

3. **Select "Desktop development with C++"**
   
   In the "Workloads" tab, check:
   - âœ… **Desktop development with C++**
   
   This will install (~7 GB):
   - MSVC (Microsoft Visual C++)
   - Windows SDK
   - CMake
   - C++ build tools

4. **Individual Components** (verify these are selected)
   
   Switch to "Individual components" tab and ensure:
   - âœ… MSVC v143 - VS 2022 C++ x64/x86 build tools (Latest)
   - âœ… Windows 10/11 SDK (Latest version)
   - âœ… C++ CMake tools for Windows
   
   These should be auto-selected with the workload.

5. **Click "Install"**
   
   This will take 20-40 minutes depending on internet speed.

6. **Restart computer** when prompted

### Verify Visual Studio Installation

```powershell
flutter doctor
```

Should now show:
```
[âœ“] Visual Studio - develop Windows apps (Visual Studio Community 2022 17.x.x)
```

If still showing âœ—:

```powershell
flutter doctor -v
```

Look for errors. Common issues:
- Missing C++ tools â†’ Re-run VS installer, verify "Desktop development with C++" is checked
- Wrong version â†’ Flutter requires VS 2022, not 2019 or older

---

## ðŸŽ¨ Install Development Tools

### Option A: Visual Studio Code (Recommended)

**Why VS Code?**
- Lightweight
- Excellent Flutter/Dart extensions
- Hot reload support
- Integrated debugging

**Installation:**

1. **Download VS Code**
   
   https://code.visualstudio.com/
   
   Click "Download for Windows"

2. **Run installer**
   
   Recommended options:
   - âœ… Add "Open with Code" action to Windows Explorer context menu
   - âœ… Add to PATH
   - âœ… Register Code as editor for supported file types

3. **Install Flutter extension**
   
   Open VS Code:
   - Press `Ctrl + Shift + X` (Extensions)
   - Search "Flutter"
   - Install "Flutter" by Dart Code (includes Dart extension)
   - Reload VS Code

4. **Verify Flutter extension**
   
   - Press `Ctrl + Shift + P` (Command Palette)
   - Type "Flutter"
   - Should see "Flutter: New Project", "Flutter: Run Flutter Doctor", etc.

### Option B: Android Studio (Alternative)

**Why Android Studio?**
- Official Android development IDE
- Useful if planning mobile development soon
- More heavyweight than VS Code

**Installation:**

1. Download from: https://developer.android.com/studio

2. Run installer (default options are fine)

3. Install Flutter plugin:
   - File â†’ Settings â†’ Plugins
   - Search "Flutter"
   - Install and restart

**For Sparky development, VS Code is sufficient.**

---

## ðŸ§ª Create First Flutter Project

### Test the Installation

1. **Create a test project:**
   ```powershell
   cd C:\src
   flutter create test_app
   cd test_app
   ```

2. **Run the app:**
   ```powershell
   flutter run -d windows
   ```
   
   First run will take 2-5 minutes (compiling dependencies).

3. **Expected result:**
   
   A window should appear with "Flutter Demo Home Page" and a counter.
   
   In the terminal, you'll see:
   ```
   Flutter run key commands.
   r Hot reload.
   R Hot restart.
   h List all available interactive commands.
   d Detach (terminate "flutter run" but leave application running).
   c Clear the screen
   q Quit (terminate the application on the device).
   ```

4. **Test hot reload:**
   
   - In VS Code, open `lib/main.dart`
   - Change line ~11: `title: 'Flutter Demo Home Page',` to `title: 'My Test App',`
   - Press `r` in the terminal
   - App should update INSTANTLY without restart

5. **Quit the app:**
   
   Press `q` in terminal

**If this worked, you're ready to build Sparky! ðŸŽ‰**

---

## ðŸ©º Run Final Flutter Doctor

```powershell
flutter doctor
```

**Ideal output:**
```
Doctor summary (to see all details, run flutter doctor -v):
[âœ“] Flutter (Channel stable, 3.x.x, on Microsoft Windows 11)
[âœ“] Windows Version (Installed version of Windows is version 10 or higher)
[âœ“] Visual Studio - develop Windows apps (Visual Studio Community 2022)
[âœ“] VS Code (version x.x.x)
[âœ“] Connected device (1 available)
    â€¢ Windows (desktop)
[âœ“] Network resources
    â€¢ All expected network resources are available.

â€¢ No issues found!
```

**You can ignore these warnings (not needed for desktop):**
- `[âœ—] Android toolchain` - Only needed for Android apps
- `[âœ—] Chrome` - Only needed for web apps
- `[âœ—] Xcode` - Only needed for iOS apps (requires Mac)

---

## ðŸ› ï¸ Troubleshooting

### Issue: `flutter: command not found`

**Cause:** Flutter not in PATH

**Fix:**
1. Verify Flutter is at `C:\src\flutter`
2. Re-add to PATH (see "Configure Flutter" section)
3. **Restart ALL terminals** (must close and re-open)
4. If still not working, restart computer

### Issue: `Unable to locate Visual Studio`

**Cause:** Visual Studio not installed or wrong components

**Fix:**
1. Open Visual Studio Installer
2. Click "Modify" on Visual Studio 2022
3. Ensure "Desktop development with C++" is checked
4. Click "Modify" to install
5. Run `flutter doctor` again

### Issue: `Waiting for another flutter command to release the startup lock`

**Cause:** Another Flutter process is running

**Fix:**
```powershell
# Kill Flutter processes
taskkill /F /IM dart.exe
taskkill /F /IM flutter.exe

# Delete lock file
del $env:APPDATA\Pub\Cache\.flutter_tool_state
```

### Issue: `pub get failed` or package download errors

**Cause:** Network issues or antivirus blocking

**Fix:**
1. Check internet connection
2. Disable antivirus temporarily
3. Try again:
   ```powershell
   flutter pub get
   ```
4. If behind corporate firewall, configure proxy:
   ```powershell
   flutter config --no-analytics
   $env:HTTP_PROXY="http://proxy.company.com:port"
   $env:HTTPS_PROXY="http://proxy.company.com:port"
   ```

### Issue: `Error: Unable to find git in your PATH`

**Cause:** Git not installed or not in PATH

**Fix:**
1. Install Git (see Pre-Installation section)
2. Verify:
   ```powershell
   git --version
   ```
3. Restart terminal

### Issue: Slow `flutter run` on first launch

**Cause:** First-time compilation of Windows runner

**Expected behavior:** First launch is slow (2-5 minutes). Subsequent launches are fast (<30 seconds).

**Not a problem** - this is normal.

### Issue: Anti-virus flags Flutter tools

**Cause:** Some antivirus software flags Dart/Flutter binaries

**Fix:**
1. Add exceptions for:
   - `C:\src\flutter\bin`
   - `%LOCALAPPDATA%\Pub\Cache`
2. Or temporarily disable antivirus during installation

### Issue: Windows Defender SmartScreen warning

**Cause:** Flutter executables are not signed

**Fix:**
- Click "More info" â†’ "Run anyway"
- This is normal for unsigned executables

---

## âœ… Verification Checklist

Before starting Sparky development, verify:

- [ ] `flutter --version` shows Flutter version
- [ ] `flutter doctor` shows all âœ“ or only Android/Chrome/Xcode warnings
- [ ] `flutter create test_app` successfully creates project
- [ ] `flutter run -d windows` launches test app
- [ ] Hot reload works (press `r` after code change)
- [ ] VS Code has Flutter extension installed
- [ ] VS Code can create new Flutter project (Ctrl+Shift+P â†’ "Flutter: New Project")

**If all checked, you're ready to start building Sparky!**

---

## ðŸ“ Flutter Installation Summary

After installation, your system should have:

```
C:\src\flutter\          # Flutter SDK
    â”œâ”€â”€ bin\             # Flutter executables (in PATH)
    â”œâ”€â”€ packages\        # Flutter framework code
    â””â”€â”€ examples\        # Sample apps

C:\Program Files\Microsoft Visual Studio\2022\Community\
                         # Visual Studio 2022

C:\Users\<you>\AppData\Local\Pub\Cache\
                         # Dart packages cache

%LOCALAPPDATA%\.flutter  # Flutter settings
```

**Total disk usage:** ~10-15 GB

---

## ðŸš€ Next Steps

1. **Read the Flutter Migration Plan** (`FLUTTER_MIGRATION_PLAN.md`)

2. **Create Sparky Flutter project:**
   ```powershell
   cd C:\src
   flutter create sparky_flutter_client
   cd sparky_flutter_client
   ```

3. **Add dependencies to `pubspec.yaml`:**
   ```yaml
   dependencies:
     flutter:
       sdk: flutter
     flutter_bloc: ^8.1.3
     web_socket_channel: ^2.4.0
     record: ^5.0.4
     just_audio: ^0.9.36
     tray_manager: ^0.2.1
     window_manager: ^0.3.8
   ```

4. **Install dependencies:**
   ```powershell
   flutter pub get
   ```

5. **Start coding!** Follow Phase 1 of the migration plan.

---

## ðŸ“š Additional Resources

### Official Documentation
- Flutter Windows Setup: https://docs.flutter.dev/get-started/install/windows
- Flutter Desktop: https://docs.flutter.dev/platform-integration/windows/building
- Dart Language Tour: https://dart.dev/guides/language/language-tour

### Tutorials
- Flutter Codelabs: https://docs.flutter.dev/codelabs
- Flutter Widget Catalog: https://docs.flutter.dev/ui/widgets
- Flutter Cookbook: https://docs.flutter.dev/cookbook

### Community
- Flutter Discord: https://discord.gg/flutter
- Stack Overflow: https://stackoverflow.com/questions/tagged/flutter
- Reddit: https://www.reddit.com/r/FlutterDev/

### VS Code Shortcuts
- `Ctrl + Shift + P` - Command Palette
- `Ctrl + Space` - Auto-complete
- `F5` - Start Debugging
- `Shift + F5` - Stop Debugging
- `Ctrl + .` - Quick Fix

### Flutter Commands Quick Reference

```powershell
# Check environment
flutter doctor
flutter doctor -v          # Verbose output

# Create project
flutter create my_app

# Run app
flutter run                 # Default device
flutter run -d windows     # Windows desktop
flutter run --release      # Release mode (faster)

# Build release
flutter build windows      # Build for Windows

# Package management
flutter pub get            # Download dependencies
flutter pub upgrade        # Upgrade dependencies
flutter pub outdated       # Check for outdated packages

# Clean build
flutter clean              # Delete build artifacts
flutter pub cache repair   # Repair package cache

# Debugging
flutter logs               # View logs
flutter analyze            # Static analysis

# Updates
flutter upgrade            # Update Flutter SDK
flutter channel            # Show/switch channels (stable, beta, dev)
```

---

## ðŸŽ‰ Installation Complete!

You now have a complete Flutter development environment on Windows 11.

**What you can build:**
- âœ… Windows desktop apps
- âœ… Linux desktop apps (if you have Linux VM)
- âœ… macOS apps (if you have Mac)
- âœ… Web apps
- âœ… Android apps (requires Android SDK - optional)
- âœ… iOS apps (requires Mac + Xcode - optional)

**For Sparky, we're focused on Windows desktop first.**

---

## ðŸ“ž Getting Help

If you encounter issues during installation:

1. **Check Flutter doctor output:**
   ```powershell
   flutter doctor -v
   ```
   Shows detailed diagnostics

2. **Search Flutter issues:**
   https://github.com/flutter/flutter/issues

3. **Ask in Flutter Discord:**
   https://discord.gg/flutter

4. **Check this guide's troubleshooting section** (above)

**Common installation time:** 1-2 hours (depending on internet speed)

**You're now ready to build Sparky in Flutter! ðŸš€**
