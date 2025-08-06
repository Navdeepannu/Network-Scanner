# Fast Network Scanner Requirements

## System Requirements

- Python 3.6 or higher
- Operating System: Windows, macOS, or Linux

## Python Libraries

All required libraries are part of Python's standard library:

### For CLI Version (ping_scanner.py):

- subprocess (built-in)
- platform (built-in)
- ipaddress (built-in)
- time (built-in)
- concurrent.futures (built-in)

### For GUI Version (ping_scanner_gui.py):

- tkinter (built-in with most Python installations)
- All CLI libraries above

## Installation Check

To verify tkinter is available for the GUI:

```python
import tkinter
print("GUI ready!")
```

If tkinter is missing:

- **Ubuntu/Debian**: `sudo apt-get install python3-tk`
- **CentOS/RHEL**: `sudo yum install tkinter`
- **macOS**: Usually included with Python
- **Windows**: Usually included with Python

## No External Dependencies Required!

This project uses only Python's standard library for maximum compatibility.
