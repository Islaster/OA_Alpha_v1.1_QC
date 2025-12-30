# License Integration Guide

## ✅ What's Ready

The license system is fully functional:
- `src/licensing/lemonsqueezy.py` - API client
- `src/licensing/license_storage.py` - Local storage
- `src/gui/license_dialog.py` - Beautiful UI dialog

---

## 🚀 Quick Integration (3 Lines)

### Option 1: Show dialog on startup

Add to `gui_new.py` (before showing main window):

```python
from src.gui.license_dialog import LicenseDialog

app = QApplication(sys.argv)

# Show license dialog
license_dialog = LicenseDialog()
license_dialog.exec()

# Continue with main window
window = MainWindow()
window.show()
```

### Option 2: Check license status without dialog

```python
from src.gui.license_dialog import LicenseChecker

# Check if licensed
if LicenseChecker.has_valid_license():
    print("✅ Full version")
else:
    print("🔓 Trial mode")
```

---

## 📋 Example: Gate Features

```python
from src.gui.license_dialog import LicenseChecker

def process_file(self):
    # Check license
    if not LicenseChecker.has_valid_license():
        # Show trial warning
        reply = QMessageBox.question(
            self,
            "Trial Mode",
            "Upgrade to unlock all features?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            # Show purchase link
            LicenseChecker.show_purchase_dialog(self)
            return
        # Or allow limited processing
    
    # Continue with full processing...
```

---

## 🎨 What the Dialog Looks Like

```
┌────────────────────────────────────┐
│   🎯 OA - Orientation Automator   │
│   Version 1.1.0 - Professional    │
├────────────────────────────────────┤
│                                    │
│ 🔓 Free Trial: Basic features     │
│ 🔑 Licensed: Full features         │
│                                    │
│ Purchase: yourstore.lemonsqueezy..│
├────────────────────────────────────┤
│ [License Key Input Field]          │
│                                    │
│ This device: Mac.lan-Darwin        │
├────────────────────────────────────┤
│ [Continue with Trial] [Activate]   │
└────────────────────────────────────┘
```

---

## 🔑 License Storage Location

- **macOS**: `~/Library/Application Support/OA_OrientationAutomator/license.json`
- **Windows**: `%APPDATA%\OA_OrientationAutomator\license.json`
- **Linux**: `~/.local/share/OA_OrientationAutomator/license.json`

---

## ✨ Features Included

1. **Auto-checks** existing license on startup
2. **Validates** with Lemon Squeezy API
3. **Stores** license + instance_id locally
4. **Shows status** (Trial vs Licensed)
5. **Easy activation** - just enter key
6. **Deactivation** - move to another machine
7. **Purchase link** - direct to your store

---

## 🧪 Test It

```bash
python gui_new.py
```

Or standalone:

```python
from PySide6.QtWidgets import QApplication
from src.gui.license_dialog import LicenseDialog
import sys

app = QApplication(sys.argv)
dialog = LicenseDialog()
dialog.exec()

print(f"Licensed: {dialog.is_activated()}")
```

---

## 📝 Update Purchase URL

Edit `src/gui/license_dialog.py` line 44:

```python
<a href='https://YOUR-ACTUAL-LEMONSQUEEZY-STORE-URL'>Purchase a license</a>
```

Replace with your real Lemon Squeezy product URL!

---

## 🎯 That's It!

Your license system is ready. Users can:
- ✅ Try for free (trial mode)
- ✅ Enter license key to unlock
- ✅ Move license between machines
- ✅ Auto-validated on every start

