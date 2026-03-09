# B33 - Portable Penetration Testing Device

> **⚠️ EDUCATIONAL USE ONLY**: This device is built strictly for educational purposes and personal learning. It will NOT be sold or distributed to prevent misuse.

## Table of Contents

- [Project Overview](#project-overview)
- [Hardware Documentation](#hardware-documentation)
- [Features Documentation](#features-documentation)
- [Software Architecture](#software-architecture)
- [User Interface](#user-interface)
- [Vulnerability Database](#vulnerability-database)
- [Implementation Roadmap](#implementation-roadmap)
- [Legal and Ethical Guidelines](#legal-and-ethical-guidelines)
- [Testing and Verification](#testing-and-verification)
- [Cost and Time Estimates](#cost-and-time-estimates)
- [Future Enhancements](#future-enhancements)

---

## Project Overview

### What is B33?

B33 is a portable penetration testing device built on a Raspberry Pi 4 (main scanner/controller) and a Raspberry Pi Pico 2WH (USB HID dongle). It's designed as an educational tool for learning about cybersecurity, network vulnerabilities, and defensive security measures.

### Purpose

- **Educational security research** in controlled environments
- **Learning** about cybersecurity vulnerabilities and defense mechanisms
- **Testing** on systems you own or have explicit written permission to test
- **Understanding** how security tools work and how to defend against them

### ⚠️ Legal Disclaimer

**This tool is ONLY for:**
- Educational security research in controlled environments
- Testing on systems you own or have explicit written permission to test
- Learning about cybersecurity vulnerabilities and defense mechanisms

**WARNING**: Unauthorized use is illegal and unethical. User is fully responsible for all actions.

### Key Architecture

B33 uses a cloud-based architecture for scalability and flexibility:

```
┌──────────────────────────────┐
│   Raspberry Pi 4 (2GB)       │──┐
│   Main Scanner + Controller  │  │
│   - LAN scanning             │  │
│   - Server polling           │  │  WiFi
│   - OLED display + buttons   │  │
│  ┌───────────────────────┐   │  │
│  │  Pico 2WH (USB HID)   │   │  │
│  │  - USB keyboard emu   │   │  │
│  └───────────────────────┘   │  │
└──────────────────────────────┘  │
  (Pi 4 controls Pico via USB)    │
                                  ├──> ┌─────────────────┐
                                  │    │  Go Server      │
                                  │    │  - C2 Backend   │
                                  │    │  - Task Queue   │──┐
                                  │    │  - Public Scan  │  │
                                  │    └─────────────────┘  │
                                  │                         │
┌─────────────────┐               │                         │
│  Web Interface  │               │                         │
│  (PC/Phone)     │───────────────┘                         │
│  Static HTML/JS │                                         │
└─────────────────┘                                         │
                                                            │
                                              ┌─────────────▼──────┐
                                              │  Cloudflare D1     │
                                              │  - Findings        │
                                              │  - Backdoors       │
                                              │  - Tasks           │
                                              └────────────────────┘
```

**Key Features**:
- Microcontroller pushes scan data to Cloudflare D1 databases
- Static web interface reads from D1 databases (no server hosting needed)
- Go server coordinates backdoor C2, scan tasks, and exploitation requests
- Microcontroller polls server every 30 seconds for new tasks
- Vulnerability data fetched from internet APIs (not stored locally)

---

## Hardware Documentation

### 2.1 Current Hardware (What We Have)

✅ **Raspberry Pi 4 Model B (2GB RAM)**
- Main portable scanner and controller
- Quad-core ARM Cortex-A72 @ 1.8GHz, 2GB LPDDR4 RAM
- Built-in dual-band WiFi (2.4GHz + 5GHz)
- Boots from micro SD card, runs Raspberry Pi OS Lite (full Linux)
- Connects to OLED display + buttons via GPIO
- Controls Pico 2WH via USB serial

✅ **Raspberry Pi Pico 2WH**
- USB HID dongle — plugged into target PC for keyboard emulation
- CircuitPython support
- USB HID capabilities (emulates keyboard)
- 264KB RAM, 2MB flash
- Receives commands from Pi 4 over USB serial

✅ **Micro SD Card**
- OS storage for Raspberry Pi 4

✅ **ECO 600 PD Power Bank**
- Portable power supply
- USB-C PD support
- Provides 8-12 hours of runtime

### 2.2 Required Hardware (Must Acquire for MVP)

To build a functional B33 device, you'll need:

#### Display
**Option 1 (Recommended for MVP)**: SSD1306 OLED Display
- 128x64 pixels
- I2C interface
- Low power consumption
- Cost: $5-10

**Option 2**: ST7789 TFT LCD
- 240x240 pixels
- SPI interface
- Colorful display, better visibility
- Cost: $10-15

#### Input Buttons
- **2× Tactile Push Buttons**
  - One for ENTER
  - One for DOWN/navigation
- Pull-up/pull-down resistors (if not built-in)
- Cost: $1-2

#### Connectivity & Assembly
- **MicroUSB/USB-C Cable**: For connecting to PCs (backdoor feature)
- **Jumper Wires**: For prototyping connections
- **Breadboard**: For initial testing
- **Soldering Kit**: For permanent connections later
- Cost: $8-15

#### Enclosure
- 3D printed case or small project box
- Dimensions: 17cm × 8cm × 5cm
- Cost: $10-20 (material or purchase)

**Total MVP Cost**: ~$15-25 (excluding owned hardware)

### 2.3 Future Hardware Wishlist (Enhancements)

**Target Final Dimensions**: 17cm × 8cm × 5cm (length × width × height)
- ✅ **Reasonable size** - similar to a large smartphone or portable WiFi hotspot
- Comparable to: portable WiFi hotspot, power bank, or handheld game console
- Easily fits in a backpack or large pocket
- Enough space for all components with proper ventilation

**Future Hardware Upgrades**:

#### Network Interface
- External WiFi adapter with monitor mode support (for advanced WiFi scanning)
- Ethernet adapter for wired network testing
- Cost: $15-30

#### Better Display
- Larger touchscreen display (2.8" or 3.5" TFT) for easier navigation
- E-ink display for better battery life and outdoor visibility
- Cost: $15-25

#### Additional Input
- Rotary encoder for faster menu navigation
- Full mini keyboard (optional)
- Cost: $2-10

#### Power Management
- Rechargeable LiPo battery with charging circuit
- Solar panel charging option for extended field use
- Cost: $10-30

#### Sensors/Extras
- GPS module for geotagging scan locations
- Real-time clock (RTC) for accurate timestamps
- Buzzer for audio feedback
- Cost: $15-25

**Total Future Hardware Cost**: ~$75-135

---

## Features Documentation

### Feature 1: Private IP Vulnerability Scanner

**Description**: Scans the local area network (LAN) for devices and checks them against online vulnerability databases.

**Coordination**: Managed by Go server

#### How It Works

1. **Initiation**: User initiates scan via web interface OR Pico polls server and receives scan task
2. **Connection**: Pico connects to target WiFi network
3. **Network Discovery**:
   - Reads network mask to determine IP range (e.g., 192.168.1.0/24)
   - ICMP ping sweep to find active hosts
   - ARP scanning for MAC addresses
   - Port scanning (common ports: 21, 22, 23, 80, 443, 445, etc.)
4. **Service Detection**: Identifies services running on open ports
5. **Vulnerability Lookup**: Fetches vulnerability data from internet APIs (NVD, VulnDB)
6. **Matching**: Compares detected services/versions against vulnerability data
7. **Storage**: Pushes findings to Cloudflare D1 database via API

#### Extended Feature: WiFi Network Scanning

Can scan other WiFi networks in the area:
- WiFi scanning to detect nearby networks
- Attempt to connect (with authorization) or analyze from outside
- Reference: https://youtu.be/YB9kbVfNZjA?si=SOF137X24-t8av0b

#### Database Schema (PrivateIPFindings - Cloudflare D1)

```sql
CREATE TABLE private_ip_scans (
    scan_id TEXT PRIMARY KEY,
    timestamp INTEGER NOT NULL,
    target_ip TEXT NOT NULL,
    mac_address TEXT,
    open_ports TEXT, -- JSON array
    detected_services TEXT, -- JSON array
    vulnerabilities_found TEXT, -- JSON array with CVE IDs
    network_ssid TEXT,
    risk_level TEXT -- low/medium/high/critical
);
```

---

### Feature 2: Public IP Vulnerability Scanner

**Description**: Scans public IP addresses for vulnerabilities (configurable scope: worldwide or Israel-focused).

**Execution**: Coordinated and executed by Go server (more efficient than microcontroller for large-scale scanning)

#### How It Works

1. **Configuration**: User configures scan via web interface (target IP ranges, scope)
2. **Request**: Web interface sends scan request to Go server
3. **Scanning** (Go server performs):
   - Generate or load target IP ranges:
     - **Option A**: Specific ranges (e.g., Israeli IP blocks)
     - **Option B**: Random sampling from global IP space
   - Rate-limited scanning to avoid detection/blocking
   - Port scanning, service detection
   - Fetch vulnerability data from internet APIs
   - Vulnerability matching
4. **Storage**: Server pushes results to Cloudflare D1 database
5. **Display**: Web interface displays results in real-time

#### Important Considerations

⚠️ **Legal Warnings**:
- Scanning public IPs without authorization is illegal in many jurisdictions
- Implement rate limiting (e.g., max 1 scan per second)
- Add user confirmation before starting public scans
- Log all scan activity for accountability

#### Database Schema (PublicIPFindings - Cloudflare D1)

```sql
CREATE TABLE public_ip_scans (
    scan_id TEXT PRIMARY KEY,
    timestamp INTEGER NOT NULL,
    target_ip TEXT NOT NULL,
    country_code TEXT,
    open_ports TEXT, -- JSON array
    detected_services TEXT, -- JSON array
    vulnerabilities_found TEXT, -- JSON array with CVE IDs
    risk_level TEXT,
    last_scanned INTEGER
);
```

---

### Feature 3: Regular Backdoor

**Description**: Connect the Pico to a target PC via USB and deploy a persistent backdoor for later access.

**Implementation**: Backdoor written in **Go** for cross-platform compatibility and efficient execution

#### How It Works

1. **Connection**: Pico connects to target PC via USB
2. **HID Emulation**: Emulates a HID (keyboard/mouse) device using USB HID capabilities
3. **Payload Execution**: Types commands to execute backdoor payload:
   - Download and install Go backdoor binary
   - Configure persistence mechanisms:
     - **Windows**: Startup folders, scheduled tasks, registry keys
     - **Linux/macOS**: Cron jobs, systemd services
   - Establish command & control (C2) connection details
4. **C2 Connection**: Go backdoor establishes outbound connection to attacker's server
5. **Logging**: Store compromised PC information in database

#### Backdoor Features (Go Implementation)

- ✅ Remote command execution
- ✅ File upload/download
- ✅ Screenshot capture
- ✅ Keylogging capabilities
- ✅ Persistence across reboots
- ✅ Cross-platform support (Windows, Linux, macOS)
- ✅ Small binary size and fast execution

#### Database Schema (InfectedPCs - Cloudflare D1)

```sql
CREATE TABLE infected_pcs (
    pc_id TEXT PRIMARY KEY,
    timestamp_infected INTEGER NOT NULL,
    hostname TEXT,
    username TEXT,
    ip_address TEXT,
    operating_system TEXT,
    backdoor_version TEXT,
    last_contact INTEGER,
    status TEXT, -- active/inactive/removed
    notes TEXT
);
```

#### Critical Security Notes

⚠️ **Authorization Required**:
- This feature requires explicit written authorization
- Only use on systems you own or have permission to test
- Implement kill switch to remove backdoor on command
- Log all actions for audit trail

---

### Feature 4: Web Interface Dashboard

**Description**: Static HTML + JavaScript files that run on **PC or phone** (not on microcontroller). Reads data from Cloudflare D1 databases and sends commands to Go server.

#### Architecture

- **Static files** (HTML/CSS/JS) - no server hosting needed
- All data access goes through **Go server's REST API** (API tokens stay server-side)
- Send commands to **Go server** for exploitations, scan tasks, and database operations
- Can run from local filesystem (`file://`) or simple HTTP server
- Works on PC (browser) and phone (mobile browser)

#### Dashboard Features

##### Dashboard View
- Summary statistics (total scans, vulnerabilities found, active backdoors)
- Recent activity timeline
- Risk level distribution charts

##### Private IP Results
- Table view of all private IP scan results (from D1)
- Filter by date, risk level, network
- Export to CSV/JSON
- Delete individual records
- **🆕 Exploit & Deploy Button** - For each vulnerable device found

##### Public IP Results
- Similar to private IP view (from D1)
- Map visualization of scanned IPs (if GPS data available)
- **🆕 Exploit & Deploy Button** - Same automated exploitation feature

##### Automated Exploitation Feature (NEW!)

**How It Works**:
1. User clicks "Exploit & Deploy Backdoor" button in web interface
2. Web interface sends exploitation request to **Go server**
3. Go server queues the task
4. **Pico polls server every 30 seconds** (configurable) for new tasks
5. When Pico sees exploitation task:
   - Exploits the identified vulnerability
   - Deploys the Go backdoor to the target system
   - Reports success/failure back to server
   - Server updates D1 database
6. Web interface shows real-time status updates

**Safety Features**:
- ⚠️ **For Educational security research purposes only**
- Requires explicit confirmation before execution
- Logs all exploitation attempts to D1

##### Infected PCs Management
- List of compromised systems (from D1)
- Send commands to backdoors (via Go server C2)
- Remove backdoor remotely
- Update status

##### Settings
- Configure scan parameters
- Pico polling interval (default 30 seconds)
- Export/import databases
- Go server connection settings

#### Technical Implementation

```javascript
// Example: Fetching scans via Go server API
const SERVER_URL = 'http://your-go-server:8080';

async function fetchScans() {
    const response = await fetch(`${SERVER_URL}/api/scans/private`, {
        headers: {
            'Authorization': `Bearer ${JWT_TOKEN}`,
            'Content-Type': 'application/json'
        }
    });
    return await response.json();
}

async function requestExploit(targetIp, cveId) {
    const response = await fetch(`${SERVER_URL}/api/tasks`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${JWT_TOKEN}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            task_type: 'exploit',
            target_ip: targetIp,
            vulnerability_id: cveId,
            deploy_backdoor: true
        })
    });
    return await response.json();
}
```

**Stack**:
- **Frontend**: HTML/CSS/JavaScript (Bootstrap or similar)
- **Database Access**: All through Go server REST API (D1 tokens stay server-side)
- **Server Communication**: REST API calls to Go server
- **Authentication**: JWT tokens for web interface
- **No hosting required** - runs as static files on local device

---

## Software Architecture

### 4.1 Firmware

#### Raspberry Pi 4 (Python on Raspberry Pi OS Lite)

**Main components** (`pi4/` directory):

```
pi4/main.py              # Entry point, asyncio event loop, OLED menu
├── config.py           # Load settings from /boot/b33_settings.json
├── scanner.py          # Host discovery, port scan, CVE lookup (NVD API)
├── api_client.py       # HTTP client — poll, push_scan, health_check
├── poller.py           # 30s poll loop, receives tasks, dispatches them
├── task_runner.py      # Executes tasks by type, reports results
├── hid_controller.py   # Sends HID commands to Pico via USB serial (pyserial)
├── display.py          # SSD1306 OLED wrapper (luma.oled + Pillow)
├── buttons.py          # GPIO button handler (gpiozero) — DOWN + ENTER
├── wifi_manager.py     # WiFi helpers (nmcli / subprocess)
└── requirements.txt    # pip dependencies
```

Using `asyncio` for concurrent operations:
```python
import asyncio

async def main():
    asyncio.create_task(poller.run())   # background polling
    await menu_loop()                   # foreground UI

asyncio.run(main())
```

**Key Pi 4 libraries**:
- `requests` — HTTP to Go server
- `luma.oled` + `Pillow` — SSD1306 OLED display
- `gpiozero` — button GPIO input
- `pyserial` — USB serial to Pico

#### Raspberry Pi Pico 2WH (CircuitPython — HID only)

**Main components** (`pico/` directory):

```
pico/code.py             # Listens on USB serial, executes HID on command
└── hid_payload.py      # Windows + Linux keyboard sequences
```

The Pico sits connected to the Pi 4 via USB. When a backdoor deploy is triggered, Pi 4 unplugs the Pico from its own USB, plugs it into the target PC, and the Pico emulates a keyboard to type the backdoor deployment commands. (Alternatively, the Pico can be pre-staged and commanded via serial.)

**Key Pico libraries** (from Adafruit CircuitPython Bundle):
- `adafruit_hid/` — USB HID keyboard emulation

### 4.2 Web Interface Files

```
web/
├── index.html              # Main dashboard
├── private_scans.html      # Private IP results (with exploit buttons)
├── public_scans.html       # Public IP results (with exploit buttons)
├── infected_pcs.html       # Backdoor management
├── settings.html           # Configuration page
├── css/
│   └── styles.css          # Styling
└── js/
    ├── app.js              # Frontend logic, API calls, exploitation triggers
    ├── api.js              # API interface wrapper
    └── exploit.js          # Exploitation automation logic
```

### 4.3 Backdoor (Go)

**Main Go Files**:

```
backdoor/
├── backdoor.go         # Main C2 backdoor implementation
├── persistence.go      # OS-specific persistence mechanisms
├── commands.go         # Remote command execution handlers
├── network.go          # Network communication with C2 server
└── stealth.go          # Anti-detection and evasion techniques
```

**Compilation**:
```bash
# Build for different platforms
GOOS=windows GOARCH=amd64 go build -o backdoor_win.exe
GOOS=linux GOARCH=amd64 go build -o backdoor_linux
GOOS=darwin GOARCH=amd64 go build -o backdoor_mac
```

### 4.4 Go Server (Rewritten/Extended)

**Purpose**: Coordinate all B33 operations

**Main Go Files**:

```
server/
├── main.go              # Server entry point, HTTP/WebSocket server
├── c2_handler.go        # Backdoor C2 communication (existing)
├── scanner.go           # Public IP scanning engine
├── task_queue.go        # Task queue for Pico
├── pico_poller.go       # Handle Pico polling requests
├── cloudflare_d1.go     # Push/pull data from Cloudflare D1
├── web_api.go           # REST API for web interface
├── exploit_modules.go   # Exploitation logic
└── auth.go              # Authentication (JWT, API keys)
```

**Server Responsibilities**:
1. ✅ Backdoor C2 (existing functionality)
2. ✅ Public IP scanning coordination
3. ✅ Task queue management for Pico
4. ✅ Receive exploitation requests from web interface
5. ✅ Push all data to Cloudflare D1
6. ✅ Serve API for web interface

### 4.5 Database Structure (Cloudflare D1)

**One D1 database (`b33`)** with 6 tables. All access goes through the Go server (API tokens stay server-side).

**Database ID**: `4ad6c776-3c59-4c89-9c5a-068329278c30` | **Region**: WEUR

#### Table 1: `private_ip_scans` - LAN scan results
```sql
CREATE TABLE private_ip_scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    target_ip TEXT NOT NULL,
    mac_address TEXT,
    hostname TEXT,
    open_ports TEXT,              -- JSON array
    detected_services TEXT,      -- JSON array
    vulnerabilities_found TEXT,  -- JSON array with CVE data
    network_ssid TEXT,
    network_bssid TEXT,
    risk_level TEXT CHECK(risk_level IN ('none','low','medium','high','critical')),
    scan_source TEXT DEFAULT 'pico'
);
```

#### Table 2: `public_ip_scans` - Public IP scan results
```sql
CREATE TABLE public_ip_scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    target_ip TEXT NOT NULL,
    country_code TEXT,           -- ISO 3166-1 alpha-2
    city TEXT,
    open_ports TEXT,
    detected_services TEXT,
    vulnerabilities_found TEXT,
    risk_level TEXT CHECK(risk_level IN ('none','low','medium','high','critical')),
    scan_batch_id TEXT
);
```

#### Table 3: `infected_pcs` - Backdoor tracking
```sql
CREATE TABLE infected_pcs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pc_id TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    hostname TEXT,
    username TEXT,
    internal_ip TEXT,
    external_ip TEXT,
    operating_system TEXT,
    architecture TEXT,
    backdoor_version TEXT,
    last_heartbeat TEXT,
    status TEXT CHECK(status IN ('active','inactive','removed')) DEFAULT 'active',
    deployment_method TEXT,
    notes TEXT
);
```

#### Table 4: `task_queue` - Communication between web interface and Pico/server
```sql
CREATE TABLE task_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    task_type TEXT NOT NULL CHECK(task_type IN ('exploit','scan_private','scan_public','deploy_backdoor','command')),
    target_ip TEXT,
    vulnerability_id TEXT,
    payload TEXT,                -- JSON: task parameters
    status TEXT NOT NULL CHECK(status IN ('pending','assigned','in_progress','completed','failed')) DEFAULT 'pending',
    assigned_to TEXT,            -- 'pico' or 'server'
    result TEXT,
    error_message TEXT,
    completed_at TEXT
);
```

#### Table 5: `exploitation_logs` - Exploitation attempt history
```sql
CREATE TABLE exploitation_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    task_id TEXT REFERENCES task_queue(task_id),
    target_ip TEXT NOT NULL,
    vulnerability_id TEXT,
    exploit_method TEXT,
    success INTEGER NOT NULL DEFAULT 0,
    backdoor_deployed INTEGER DEFAULT 0,
    pc_id TEXT REFERENCES infected_pcs(pc_id),
    details TEXT,
    error_message TEXT
);
```

#### Table 6: `c2_command_logs` - Backdoor command history
```sql
CREATE TABLE c2_command_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    pc_id TEXT NOT NULL REFERENCES infected_pcs(pc_id),
    command_type TEXT NOT NULL,  -- 'shell','upload','download','screenshot','keylog','remove'
    command_data TEXT,
    status TEXT CHECK(status IN ('sent','received','completed','failed')) DEFAULT 'sent',
    result TEXT,
    completed_at TEXT
);
```

**Data flow**: Pico/Web Interface -> Go Server -> Cloudflare D1

**Note**: No local storage on Pico - all data in the cloud. Full schema with indexes in [database/schema.sql](database/schema.sql).

---

## User Interface

### Display Menu Structure

```
[Main Menu]
├── 1. Private IP Scan
│   ├── Start Scan
│   ├── View Results (last 10)
│   └── Back
├── 2. Public IP Scan
│   ├── Configure Range
│   ├── Start Scan
│   ├── View Results
│   └── Back
├── 3. Backdoor Mode
│   ├── Deploy Backdoor (USB HID)
│   ├── View Infected PCs
│   └── Back
├── 4. Server Status
│   ├── Connection Status
│   ├── Pending Tasks
│   └── Back
├── 5. Settings
│   ├── WiFi Config
│   ├── Server URL
│   ├── Polling Interval
│   └── Back
└── 6. About/Stats
    ├── Device Info
    ├── Total Scans
    └── Back
```

### Button Controls

- **DOWN Button**: Navigate menu items (cycles through options)
- **ENTER Button**: Select current item / confirm action

### Display Examples

**Main Menu**:
```
┌─────────────────────┐
│  B33 Pen-Test       │
│                     │
│ > Private IP Scan   │
│   Public IP Scan    │
│   Backdoor Mode     │
│   Server Status     │
│                     │
│ DOWN   |    ENTER   │
└─────────────────────┘
```

**Scanning**:
```
┌─────────────────────┐
│  Scanning...        │
│                     │
│  192.168.1.1  ✓     │
│  192.168.1.5  ✗     │
│  192.168.1.12 ...   │
│                     │
│  Progress: 45%      │
└─────────────────────┘
```

---

## Vulnerability Database

### Architecture

**Not stored locally** - fetched from internet APIs in real-time

### Data Source Options

#### 1. NVD (National Vulnerability Database) API (Recommended)
- **Free REST API** from NIST
- Query by CVE ID or search parameters
- Rate limits: 50 requests per 30 seconds (without API key)
- API Documentation: https://nvd.nist.gov/developers/vulnerabilities

**Example API Call**:
```python
import requests

def query_nvd(cpe_name):
    url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    params = {
        "cpeName": cpe_name  # e.g., "cpe:2.3:a:openbsd:openssh:7.4:*:*:*:*:*:*:*"
    }
    response = requests.get(url, params=params)
    return response.json()
```

#### 2. Alternative Sources
- **VulnDB**: More comprehensive but requires licensing
- **OpenCVE**: Community-driven CVE database
- **CVE Details**: Alternative free API

#### 3. Custom API Wrapper (Optimization)
Cache frequently accessed CVEs on Go server to:
- Reduce API calls
- Improve performance
- Respect rate limits

### How It Works

1. **Detection**: Pico detects service (e.g., "OpenSSH 7.4")
2. **Query**: Pico or Go server queries NVD API for vulnerabilities
3. **Matching**: Match results against detected service
4. **Storage**: Store matched vulnerabilities in D1 findings database

---

## Implementation Roadmap

> **Note**: Hardware setup happens **during the project** as components are acquired, not as a separate phase.

### Phase 1: Cloud Infrastructure Setup ✅ COMPLETE
- Cloudflare D1 database created with 6-table schema
- Cloudflare API access configured
- All database CRUD operations tested

### Phase 2: Go Server ✅ COMPLETE
- Go server with full REST API, JWT auth, API key auth
- Cloudflare D1 integration via REST client
- Deployed to Render: https://the-project-gukh.onrender.com

### Phase 3: Web UI ✅ COMPLETE
- Single-page app (SPA) with dark theme
- Dashboard, private scans, public scans, tasks, C2, logs pages
- Bootstrap 5 + Chart.js 4

### Phase 4: Cloud Deployment ✅ COMPLETE
- Docker multi-stage build (Go binary + web assets)
- Render auto-deploy from GitHub main branch

### Phase 5: Pi 4 + Pico Firmware ✅ COMPLETE
- Pi 4 Python firmware: `pi4/` directory
  - LAN scanner (TCP host discovery, port scan, NVD CVE lookup)
  - Server poller (30s background task)
  - OLED display driver (luma.oled, SSD1306/SH1106)
  - GPIO button handler (gpiozero)
  - HID controller (sends commands to Pico via pyserial)
- Pico CircuitPython firmware: `pico/` directory
  - USB HID keyboard emulator (Windows + Linux payloads)
  - Listens for commands from Pi 4 over USB serial

### Phase 6: Backdoor Agent (Planned)
- [ ] Go backdoor binary (Windows + Linux)
- [ ] Persistence mechanisms (scheduled tasks, cron)
- [ ] C2 communication with Go server
- [ ] Download endpoints on server (`/agent/windows`, `/agent/linux`)

### Phase 7: Web Interface (Week 9-10)
**Duration**: 20-30 hours

- [ ] Build static HTML/CSS frontend:
  - [ ] Dashboard view
  - [ ] Private IP results table
  - [ ] Public IP results table
  - [ ] Infected PCs management
  - [ ] Settings page
- [ ] Create JavaScript for D1 database access
- [ ] Implement Go server API integration
- [ ] Add Automated Exploitation feature UI:
  - [ ] Exploit button for each vulnerable device
  - [ ] Confirmation dialog
  - [ ] Real-time status updates
- [ ] Test on PC and phone browsers
- [ ] Add authentication (Cloudflare tokens, JWT)
- [ ] Implement export/import features

### Phase 7: Public IP Scanner (Week 11)
**Duration**: 10-15 hours

- [ ] Implement public IP scanning on Go server (not Pico)
- [ ] Add IP range configuration (worldwide/Israel-focused)
- [ ] Add rate limiting and ethical safeguards
- [ ] Implement user confirmation dialogs
- [ ] Test with authorization on owned IP ranges
- [ ] Add progress tracking and logging

### Phase 8: Polish and Enclosure (Week 12-13)
**Duration**: 15-20 hours

- [ ] **Acquire final hardware components** (touchscreen, case, etc.)
- [ ] Design enclosure (17×8×5 cm) in CAD software
- [ ] 3D print or build enclosure
- [ ] Assemble final device with permanent connections
- [ ] Optimize power consumption
- [ ] Add comprehensive error handling and logging
- [ ] Write user manual
- [ ] Final end-to-end testing
- [ ] Create backup/restore functionality

---

## Legal and Ethical Guidelines

### ⚠️ MANDATORY READING FOR ALL USERS

This device is a powerful security testing tool that **MUST** be used responsibly and legally.

### ✅ Authorized Use

You MAY use B33 for:
- ✅ Penetration testing **with written authorization**
- ✅ Testing **your own systems and networks**
- ✅ Educational environments **with proper oversight**
- ✅ Security research **in controlled settings**
- ✅ CTF (Capture The Flag) competitions

### ❌ ILLEGAL and PROHIBITED Use

You MUST NOT use B33 for:
- ❌ Scanning networks **without permission**
- ❌ Deploying backdoors on **unauthorized systems**
- ❌ Accessing computers **you don't own**
- ❌ Interfering with **critical infrastructure**
- ❌ **Any malicious or criminal activity**

### Legal Consequences

- Unauthorized access is a **crime** in most countries
- Penalties can include **fines and imprisonment**
- **You are responsible** for all actions performed with this device

### Best Practices

1. **Always obtain written authorization** before testing
2. **Document all testing activities** (dates, targets, findings)
3. **Report vulnerabilities responsibly** (coordinated disclosure)
4. **Never use findings for personal gain or harm**
5. **Respect privacy and data protection laws**
6. **Use the kill switch** to remove backdoors after testing
7. **Store all data securely** and encrypt sensitive information

### Educational Context

B33 is designed to help you:
- Understand how attackers think and operate
- Learn defensive security measures
- Practice ethical hacking techniques
- Build cybersecurity skills for a career in security

**Remember**: With great power comes great responsibility. Use B33 wisely and ethically.

---

## Testing and Verification

### How to Verify the System Works

#### 1. Hardware Test
```
✅ Power on device with ECO 600 PD power bank
✅ Verify OLED screen displays menu
✅ Test DOWN button navigates menu items
✅ Test ENTER button selects menu items
✅ Check WiFi connection works (connect to test network)
```

#### 2. Private IP Scanner Test
```
✅ Connect to a test network you own
✅ Run scan on your own devices (router, PC, phone)
✅ Verify scan completes successfully
✅ Check results appear in Cloudflare D1 database
✅ Open web interface and verify findings are displayed
✅ Test filtering and export features
```

#### 3. Public IP Scanner Test (with authorization)
```
✅ Configure small test range (1-10 IPs you own)
✅ Initiate scan from web interface
✅ Monitor Go server logs
✅ Verify findings stored correctly in D1
✅ Check rate limiting works (max 1 scan/second)
```

#### 4. Backdoor Test (on your own PC)
```
⚠️ Only test on systems you own!

✅ Connect Pico to test PC via USB
✅ Deploy backdoor via USB HID
✅ Verify persistence mechanisms (startup/cron)
✅ Test remote command execution via Go server C2
✅ Test file upload/download
✅ Test screenshot capture
✅ Successfully remove backdoor using kill switch
```

#### 5. Web Interface Test
```
✅ Open web interface in PC browser
✅ Open web interface in phone browser
✅ Test authentication (login with tokens)
✅ Navigate all pages (dashboard, scans, backdoors, settings)
✅ Test CRUD operations on databases:
   - View scan results
   - Delete old scans
   - Update backdoor status
   - Export data to CSV/JSON
✅ Test Automated Exploitation feature:
   - Click "Exploit & Deploy" button
   - Verify confirmation dialog appears
   - Confirm and verify task queued
   - Check Pico polls and receives task
   - Verify exploitation attempt logged
```

#### 6. Server Polling Test
```
✅ Verify Pico polls Go server every 30 seconds
✅ Queue an exploitation task from web interface
✅ Confirm Pico receives task within 30 seconds
✅ Verify task execution and status updates
✅ Test concurrent operations (scanning while polling)
```

#### 7. End-to-End Integration Test
```
✅ Scan local network from Pico
✅ View results in web interface
✅ Identify vulnerable device
✅ Click "Exploit & Deploy Backdoor"
✅ Pico polls server and receives task
✅ Pico exploits vulnerability and deploys backdoor
✅ Backdoor connects to Go server C2
✅ Send commands via web interface
✅ Verify commands execute on target
✅ Remove backdoor remotely
```

---

## Cost and Time Estimates

### Hardware Costs (USD)

#### Current (Already Owned / Ordered)
- ✅ Raspberry Pi 4 (2GB): **~$35** (ordered, arriving soon)
- ✅ Raspberry Pi Pico 2WH: **$7** (owned)
- ✅ ECO 600 PD Power Bank: **$50-80** (owned)
- ✅ SSD1306/SH1106 OLED (1.3", 128x64): **~$5** (ordered)
- ✅ Micro SD Card: **~$5** (ordered)
- ✅ Breadboard + Jumper Wires (30cm): **~$5** (ordered)

#### Still Needed
- 2× Tactile Push Buttons: **$1-2** (buy locally)
- **Remaining Total**: **~$1-2**

#### Future Enhancements (Complete device in enclosure)
- Better TFT Display (2.8" touchscreen): $15-25
- 3D Printed Enclosure (material): $10-20
- WiFi Adapter with monitor mode: $15-30
- GPS Module: $10-15
- RTC Module: $3-5
- Rotary Encoder: $2-5
- Rechargeable LiPo battery: $10-20
- Miscellaneous (wires, resistors, etc.): $10-15
- **Future Total**: **~$75-135**

#### Grand Total (Complete B33 device)
**$90-160 USD**

### Cloud/Software Costs

#### Cloudflare D1 Database
**Free Tier Includes**:
- 5GB storage
- 5 million reads/day
- 100k writes/day
- ✅ Should be sufficient for educational use

#### Go Server Hosting
- **VPS**: $5-10/month (if not already hosted)
- **Free Options**: Railway, Fly.io, Render (free tiers available)

#### Vulnerability APIs
- **NVD API**: Free (rate-limited)

**Total Monthly Cost**: **$0-10** (likely $0 if using free tiers)

### Time Estimates

**Development Time** (assuming part-time work, ~10-15 hours/week):

| Phase | Duration | Hours |
|-------|----------|-------|
| Phase 1: Cloud Infrastructure | Week 1 | 10-15 |
| Phase 2: Go Server Extension | Week 2-3 | 20-30 |
| Phase 3: Core Scanning | Week 4-5 | 20-30 |
| Phase 4: Server Polling | Week 6 | 10-15 |
| Phase 5: Backdoor Feature | Week 7-8 | 15-25 |
| Phase 6: Web Interface | Week 9-10 | 20-30 |
| Phase 7: Public IP Scanner | Week 11 | 10-15 |
| Phase 8: Polish & Enclosure | Week 12-13 | 15-20 |

**Total Development Time**:
- **120-180 hours** (~3-4.5 months part-time)
- **OR 3-4 weeks full-time** (40 hours/week)

**Hardware Assembly Time**:
- Basic breadboard setup: 2-4 hours
- Final enclosure build: 5-10 hours

### Summary

| Category | Estimate |
|----------|----------|
| **Total Hardware Cost** | $90-160 USD |
| **Monthly Software Cost** | $0-10 USD (likely $0) |
| **Development Time** | 120-180 hours (3-4.5 months part-time) |
| **Hardware Assembly** | 7-14 hours |
| **Final Device Size** | 17×8×5 cm (portable, pocket-sized) |

### Cost Reduction Tips

💡 **Save Money By**:
- Using cheaper OLED display instead of TFT
- 3D printing enclosure yourself (if you have access to a printer)
- Using free hosting tiers for Go server (Railway, Fly.io)
- Buying components in bulk from AliExpress (slower shipping but 30-50% cheaper)
- Using existing power bank (already owned)
- Starting with MVP and upgrading gradually

---

## Future Enhancements

### Potential Features to Add

#### Network Features
- 🔹 **Bluetooth scanning** for IoT devices
- 🔹 **Wireless packet sniffing** and analysis
- 🔹 **Metasploit integration** for automated exploitation
- 🔹 **WiFi deauthentication** testing (educational use only)

#### Reporting & Analysis
- 🔹 **PDF report generation** with scan findings
- 🔹 **Risk scoring algorithm** based on CVSS
- 🔹 **Trend analysis** (vulnerability trends over time)
- 🔹 **Automated recommendations** for remediation

#### Collaboration
- 🔹 **Team collaboration** features (multi-user access)
- 🔹 **Integration with SIEM** systems (Splunk, ELK)
- 🔹 **Slack/Discord notifications** for critical findings
- 🔹 **API access** for integration with other tools

#### UI/UX Improvements
- 🔹 **Dark mode** for web interface
- 🔹 **Mobile app** companion (iOS/Android)
- 🔹 **Voice alerts** for critical vulnerabilities
- 🔹 **Touchscreen support** on Pico display

#### Advanced Features
- 🔹 **AI-powered vulnerability prioritization**
- 🔹 **Anomaly detection** (machine learning)
- 🔹 **Automated patching suggestions**
- 🔹 **Integration with bug bounty platforms**

---

## Notes and Important Information

### Technical Limitations
- Pi 4 has 2GB RAM — sufficient for scanning and Python runtime
- Pico 2WH has limited resources (264KB RAM, 2MB flash) — used for HID only
- No local storage needed — all data stored in Cloudflare D1
- ECO 600 PD power bank provides approximately 8-12 hours of runtime
- Pi 4 WiFi supports both 2.4GHz and 5GHz

### Technology Choices
- **Python 3 (Pi 4)**: Full CPython on Raspberry Pi OS Lite for scanning and control
- **CircuitPython (Pico 2WH)**: Used for USB HID keyboard emulation only
- **Go**: Used for cross-platform backdoor and server implementation
- **Cloudflare D1**: Cloud database for scalability and accessibility
- **Static HTML/JS**: Web interface requires no server hosting

### Security Considerations
- The automated exploitation feature requires careful testing
- **Only use on authorized systems** with written permission
- Regular D1 database backups recommended
- Store API keys and tokens securely (use environment variables)
- Implement rate limiting to avoid triggering IDS/IPS systems

### Educational Purpose
- **Not for sale or distribution** - educational use only
- Designed to teach cybersecurity concepts and defensive measures
- Helps understand attacker methodologies and defense strategies
- Ideal for learning ethical hacking and penetration testing

### Device Dimensions
- **17×8×5 cm** is a reasonable and portable size
- Similar to a portable WiFi hotspot or large smartphone
- Fits comfortably in a backpack or large pocket
- Adequate space for all components with proper ventilation

---

## Contributing

This is a personal educational project and is not open for public contributions. However, you can:

1. **Fork the project** for your own learning
2. **Experiment** with modifications
3. **Share knowledge** responsibly within educational contexts
4. **Report security vulnerabilities** in the implementation

---

## License

**Educational Use Only**

This project is provided for educational purposes only. The creator assumes no liability for misuse. Users are solely responsible for ensuring their use complies with applicable laws and regulations.

---

## Credits

**Project Creator**: [Your Name]
**Project Name**: B33
**Start Date**: 2026
**Status**: In Development

### Technologies Used
- Raspberry Pi 4 (Python 3, Raspberry Pi OS Lite)
- Raspberry Pi Pico 2WH (CircuitPython — HID only)
- Go (Server + future backdoor agent)
- Cloudflare D1 (Database)
- HTML/CSS/JavaScript (Web Interface)
- NVD API (Vulnerability Data)

---

## Support and Contact

For questions about this project:
1. Review this documentation thoroughly
2. Check implementation roadmap for guidance
3. Test features in controlled environments
4. Document your findings and learnings

**Remember**: This tool is for educational purposes only. Always use responsibly and legally.

---

**Last Updated**: March 2026
**Version**: 1.5 (Phase 5 Complete — Pi 4 + Pico firmware written, hardware arriving)
