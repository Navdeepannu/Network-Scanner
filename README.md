# Fast Network Scanner with Hostname Resolution

A powerful, multi-threaded network scanner that discovers active hosts and resolves their hostnames/device names.

## Features

### 🚀 Performance Optimizations

- **Multi-threading**: Parallel ping operations for speed (up to 200 threads)
- **Fast scanning**: Scan entire subnets in seconds instead of minutes
- **Progress tracking**: Real-time progress bar

### 🔍 Device Discovery

- **Host detection**: Ping sweep to find active devices
- **Hostname resolution**: Automatically resolves device names using `socket.gethostbyaddr()`
- **Device identification**: Shows friendly names like "printer.local", "router.home", etc.
- **Fallback resolution**: Uses multiple methods to get device names

### 🎨 Multiple Interface Options

- **Web Interface**: Modern, responsive web UI that works on any device (Recommended for macOS)
- **Command Line Interface**: Fast terminal-based scanning with colored output
- **Cross-platform**: Works on Windows, macOS, and Linux
- **Real-time updates**: Live progress and results in all interfaces
- **Export functionality**: Save results with hostname information

## Quick Start

### 🌐 Web Interface (Recommended):

```bash
# Option 1: Use the setup script
./run_web.sh

# Option 2: Manual setup
pip3 install flask
python3 app.py

# Then open your browser to: http://localhost:5000
```

### 💻 Command Line Interface:

```bash
python3 ping_scanner.py
# Enter subnet when prompted (e.g., 192.168.1.0/24)
```

## Web Interface Features

The modern web interface provides:

- **🎨 Beautiful Design**: Responsive, gradient-based UI that works on all devices
- **📱 Mobile Friendly**: Works perfectly on phones, tablets, and desktops
- **⚡ Real-time Updates**: Live progress bar and results as they're discovered
- **🎯 Easy Configuration**: Simple form to enter subnet and thread count
- **📊 Visual Progress**: Animated progress bar and status updates
- **📋 Formatted Results**: Clean table showing IP addresses and hostnames
- **💾 One-click Export**: Download results as formatted text files
- **🚀 No Installation Hassles**: Just open in any web browser

## What You'll See

### CLI Output Example:

```
Fast Network Scanner
====================
Enter subnet (e.g. 192.168.1.0/24): 192.168.1.0/24
Scanning subnet: 192.168.1.0/24
Found 254 hosts to scan using 50 threads
Note: Hostname resolution may take extra time for active hosts

[+] Active: 192.168.1.1 (router.home)
[+] Active: 192.168.1.10 (john-laptop.local)
[+] Active: 192.168.1.50 (printer.local)

Scan Summary:
Active hosts found: 3
Scan completed in: 15.32 seconds

Active Hosts:
IP Address      Hostname
--------------------------------------------------
192.168.1.1     router.home
192.168.1.10    john-laptop.local
192.168.1.50    printer.local
Results saved to results.txt
```

### GUI Features:

- **Device names in real-time**: See "printer.local", "router.home" as devices are found
- **Formatted results**: Clean display showing IP | Hostname
- **Export with hostnames**: Save detailed results including device names

## Interface Details

### Command Line Interface:

- **Colored output**: Green for active hosts, blue for info, red for errors
- **Progress bar**: Real-time scanning progress
- **Formatted table**: Clean IP and hostname display
- **Automatic export**: Results saved to timestamped file

### Graphical Interface:

- **Subnet input field** with example format
- **Thread count adjustment** (1-200 threads)
- **Start/Stop/Clear controls** for scan management
- **Real-time progress bar** and status updates
- **Scrollable results display** showing IP | Hostname
- **Export button** to save results with file dialog

## What It Does

1. **Input**: Enter a subnet in CIDR notation (e.g., 192.168.1.0/24)
2. **Configure**: Adjust thread count for speed vs. system load
3. **Scan**: Click start and watch real-time progress
4. **Results**: View active hosts as they're discovered
5. **Export**: Save results to a text file

## Example Workflow

1. Run: `python ping_scanner_gui.py`
2. Enter subnet: `192.168.1.0/24`
3. Set threads: `50` (or higher for speed)
4. Click "Start Scan"
5. Watch progress bar fill up
6. See active hosts appear in real-time
7. Click "Export Results" to save

## Performance

- **Original sequential**: ~4-5 minutes for /24 subnet
- **New multi-threaded**: ~10-20 seconds for /24 subnet
- **Speedup**: 10-30x faster!

## Project Structure

```
ping_scanner.py      # Original CLI version (optional)
ping_scanner_gui.py  # Main GUI application
README.md           # This documentation
requirements.md     # System requirements
results.txt         # Scan results (auto-generated)
```

## Requirements

- Python 3.6+
- tkinter (usually included with Python)
- No external dependencies needed!
  • 192.168.1.10
  • 192.168.1.50
  Results saved to results.txt

````

## Performance

- **Original sequential**: ~4-5 minutes for /24 subnet
- **New multi-threaded**: ~10-20 seconds for /24 subnet
- **Speedup**: 10-30x faster!

### 📊 Output Options

- **Multiple formats**: Export to TXT, JSON, or CSV
- **Timestamped results**: All exports include timestamps
- **Colored terminal output**: Easy-to-read console display
- **Progress tracking**: Real-time progress bar

### ⚙️ Configuration

- **Command-line interface**: Full argument parsing
- **Flexible subnet input**: Support for CIDR notation
- **Custom port lists**: Specify which ports to scan
- **Quiet mode**: Progress bar only output

## Usage

### Basic Usage

```bash
# Interactive mode
python ping_scanner.py

# Command line with subnet
python ping_scanner.py 192.168.1.0/24

# Fast scan with 100 threads
python ping_scanner.py 192.168.1.0/24 -w 100

# Include port scanning
python ping_scanner.py 192.168.1.0/24 -p

# Export to JSON
python ping_scanner.py 192.168.1.0/24 -f json
````

### Advanced Options

```bash
# Full feature scan
python ping_scanner.py 192.168.1.0/24 \
    --workers 100 \
    --timeout 0.5 \
    --port-scan \
    --ports 22 80 443 3389 \
    --format json \
    --output network_scan

# Quiet mode with custom timeout
python ping_scanner.py 10.0.0.0/16 -q -t 2.0 -w 200
```

### Command Line Arguments

| Argument          | Description                    | Default                       |
| ----------------- | ------------------------------ | ----------------------------- |
| `subnet`          | Subnet to scan (CIDR notation) | Interactive input             |
| `-t, --timeout`   | Ping timeout in seconds        | 1.0                           |
| `-w, --workers`   | Number of worker threads       | 50                            |
| `-r, --retries`   | Number of ping retries         | 1                             |
| `-o, --output`    | Output filename prefix         | "results"                     |
| `-f, --format`    | Output format (txt/json/csv)   | txt                           |
| `-p, --port-scan` | Enable port scanning           | False                         |
| `--ports`         | Ports to scan                  | [22,23,53,80,110,443,993,995] |
| `-q, --quiet`     | Quiet mode (progress bar only) | False                         |
| `--no-color`      | Disable colored output         | False                         |

## Examples

### Example 1: Quick Home Network Scan

```bash
python ping_scanner.py 192.168.1.0/24
```

### Example 2: Enterprise Network with Port Scan

```bash
python ping_scanner.py 10.10.0.0/16 -w 200 -p -f json -o enterprise_scan
```

### Example 3: Stealth Scan (Long Timeout, Low Threads)

```bash
python ping_scanner.py 192.168.1.0/24 -w 10 -t 3.0 -r 2
```

## Output Formats

### TXT Format

```
Network Scan Results - 2025-07-28 10:30:15
==================================================

IP: 192.168.1.1
Status: up
Response Time: 1.23ms
Hostname: router.local
Open Ports: 22, 80, 443
Timestamp: 2025-07-28T10:30:15.123456
------------------------------
```

### JSON Format

```json
{
  "scan_timestamp": "2025-07-28T10:30:15.123456",
  "total_hosts": 5,
  "hosts": [
    {
      "ip": "192.168.1.1",
      "status": "up",
      "response_time": 1.23,
      "hostname": "router.local",
      "open_ports": [22, 80, 443],
      "timestamp": "2025-07-28T10:30:15.123456"
    }
  ]
}
```

### CSV Format

```csv
ip,status,response_time,hostname,open_ports,timestamp
192.168.1.1,up,1.23,router.local,"[22, 80, 443]",2025-07-28T10:30:15.123456
```

## Performance Tips

1. **Adjust thread count**: More threads = faster scanning, but too many can overwhelm your network
2. **Optimize timeout**: Lower timeouts for local networks (0.5s), higher for WAN (2-3s)
3. **Use quiet mode**: For large subnets, use `-q` to avoid terminal spam
4. **Network considerations**: Be mindful of network load and firewall rules

## System Requirements

- Python 3.6+
- No external dependencies (uses only standard library)
- Works on Windows, macOS, and Linux

## Performance Comparison

| Feature             | Original     | Optimized         |
| ------------------- | ------------ | ----------------- |
| Scanning Method     | Sequential   | Multi-threaded    |
| 254 hosts (/24)     | ~4-5 minutes | ~10-20 seconds    |
| Thread Count        | 1            | 50 (configurable) |
| Output Formats      | 1 (TXT)      | 3 (TXT/JSON/CSV)  |
| Progress Tracking   | None         | Real-time         |
| Port Scanning       | No           | Yes               |
| Hostname Resolution | No           | Yes               |

## Security Notice

This tool is intended for network administration and security testing of networks you own or have permission to test. Unauthorized network scanning may violate terms of service or local laws.
