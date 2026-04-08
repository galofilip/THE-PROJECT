# B33 - CLAUDE.md

## Project Overview
B33 is a portable penetration testing device for **educational purposes only**. Built on Raspberry Pi 4 (Python) as the main portable device, with a Raspberry Pi Pico 2WH as a USB HID dongle, and a Go C2 server backed by Cloudflare D1.

## Phase Status
- ✅ Phase 1: Cloudflare D1 database + schema
- ✅ Phase 2: Go server (REST API, JWT auth, D1 client)
- ✅ Phase 3: Web UI (SPA, dark theme, Bootstrap 5 + Chart.js 4)
- ✅ Phase 4: Cloud deployment (Render, Docker)
- ✅ Phase 5: Pi 4 firmware (Python) + Pico HID firmware (CircuitPython)
- ✅ Phase 5.5: Pi 4 hardware setup — OS flashed to USB stick, SSH working, OLED wired and confirmed working (SH1106 driver)
- ⏳ Phase 6+: Backdoor agent, public IP scanner

**Commit after every phase.**

## Hardware

| Device | Role |
|--------|------|
| Raspberry Pi 4 (2GB) | Main portable scanner — scanning, polling, display, buttons |
| Raspberry Pi Pico 2WH | USB HID dongle — plugged into target PC to type backdoor commands |
| SSD1306 OLED (128x64) | Display connected to Pi 4 via I2C |
| 2x Tactile buttons | Navigation (DOWN + ENTER), connected to Pi 4 GPIO |
| Micro SD card | OS storage for Pi 4 (unused — Pi boots from USB stick instead) |
| USB stick (14.3GB) | Pi 4 boot drive — Raspberry Pi OS Lite 64-bit flashed here |
| USB micro SD card reader | **NOT YET BOUGHT** — needed to flash OS onto micro SD from Windows laptop (laptop slot is full-size SD only) |

## Architecture

```
Pi 4 (Python, portable)  ──► Go Server (Render) ──► Cloudflare D1
  └── Pico 2WH (HID)         (via WiFi)
Web UI (browser/SPA)     ──► Go Server (Render) ──► Cloudflare D1
```

- **Pi 4** is the field device: scans LAN, polls server, shows OLED menu, controls Pico via USB serial
- **Pico 2WH** receives a command from Pi 4 over USB serial, then emulates a keyboard on the target PC
- Go server serves both API (`/api/*`) and static web UI (`/`)
- Auth: JWT (24h, web) + API key (Pi 4/backdoor)
- All DB access goes through Go server — no direct D1 from frontend

## Key Files

### Server
| File | Role |
|------|------|
| `server/main.go` | HTTP router, SPA handler, server entry |
| `server/config.go` | Env var loading (required + optional) |
| `server/d1_client.go` | Cloudflare D1 REST API client |
| `server/handlers_*.go` | Auth, scans, tasks, pico, c2, logs |
| `server/middleware.go` | JWT, API key, CORS, logging middleware |
| `server/models.go` | Shared structs |
| `web/index.html` | Single-page app shell |
| `web/js/api.js` | API wrapper (`_serverUrl: ''` = same-origin) |
| `web/js/app.js` | SPA routing + state |
| `web/js/pages/*.js` | Per-page logic |
| `database/schema.sql` | D1 schema (6 tables) |
| `Dockerfile` | Multi-stage Go build + web assets |

### Pi 4 Firmware (Python on Raspberry Pi OS Lite)
| File | Role |
|------|------|
| `pi4/main.py` | Entry point — asyncio event loop, menu, startup |
| `pi4/config.py` | Load config from `/boot/b33_settings.json` or env |
| `pi4/wifi_manager.py` | WiFi helpers using nmcli/subprocess |
| `pi4/api_client.py` | HTTP wrapper — poll, push_scan, health_check |
| `pi4/poller.py` | 30s poll loop, task dispatch, result accumulation |
| `pi4/task_runner.py` | Executes tasks by type, reports results |
| `pi4/scanner.py` | Host discovery, port scan, CVE lookup, risk level |
| `pi4/hid_controller.py` | Sends HID commands to Pico over USB serial (pyserial) |
| `pi4/display.py` | SSD1306 OLED wrapper (luma.oled + Pillow) |
| `pi4/buttons.py` | GPIO button handler (gpiozero) — DOWN + ENTER |
| `pi4/requirements.txt` | pip dependencies |
| `pi4/README.md` | Wiring diagram, setup steps |

### Pico 2WH Firmware (CircuitPython — HID only)
| File | Role |
|------|------|
| `pico/code.py` | Entry point — listens on USB serial for commands |
| `pico/hid_payload.py` | Windows + Linux keyboard sequences |
| `pico/README.md` | Library install, flashing instructions |

## API Endpoints

```
POST  /api/auth/login           no auth
GET   /api/health               no auth
GET   /api/scans/private        JWT
POST  /api/scans/private        JWT
GET   /api/scans/public         JWT
POST  /api/scans/public         JWT
GET/POST /api/tasks             JWT or API key
PATCH /api/tasks/{id}           JWT or API key
POST  /api/pico/poll            API key
POST  /api/c2/heartbeat         API key
GET   /api/c2/commands/{pc_id}  API key
GET   /api/c2/infected          JWT or API key
POST  /api/c2/infected/{id}/command  JWT
GET   /api/logs/exploits        JWT
GET   /api/logs/c2              JWT
```

## Database Tables (D1)
1. `private_ip_scans` — LAN scan results from Pi 4
2. `public_ip_scans` — Public IP scan results (server-side)
3. `infected_pcs` — Backdoor tracking
4. `task_queue` — Web→Pi 4 task coordination
5. `exploitation_logs` — Exploitation history
6. `c2_command_logs` — Backdoor command history

## Wiring (Pi 4 GPIO)

```
OLED SDA  → GPIO 2  (Pin 3)
OLED SCL  → GPIO 3  (Pin 5)
OLED VCC  → 3.3V   (Pin 1)
OLED GND  → GND    (Pin 6)
BTN DOWN  → GPIO 17 (Pin 11) + GND
BTN ENTER → GPIO 27 (Pin 13) + GND
Pico 2WH  → any USB-A port on Pi 4
```

## Environment Variables (server)

| Var | Required | Description |
|-----|----------|-------------|
| `CF_ACCOUNT_ID` | ✅ | Cloudflare account ID |
| `CF_API_TOKEN` | ✅ | Cloudflare API token |
| `D1_DATABASE_ID` | ✅ | D1 database ID |
| `B33_API_KEY` | ✅ | API key for Pi 4/backdoor |
| `B33_JWT_SECRET` | ✅ | JWT signing secret |
| `B33_USERNAME` | ✅ | Web UI login username |
| `B33_PASSWORD` | ✅ | Web UI login password |
| `PORT` | ❌ | Default: 8080 |
| `WEB_DIR` | ❌ | Default: "web" |

## Build & Run

```bash
# Local dev (from server/ dir)
cp .env.example .env  # fill in values
go run .

# Docker build
docker build -t b33-server .
docker run -p 8080:8080 --env-file server/.env b33-server

# Pi 4 setup
cd pi4 && pip install -r requirements.txt
python main.py
```

## Deployment (Render)
- URL: `https://the-project-gukh.onrender.com`
- Render auto-deploys on push to `main` (GitHub)
- Free tier sleeps after 15min, ~30-50s cold start
- Docker-based, env vars set in Render dashboard

## Tech Stack
- **Server**: Go 1.25, stdlib HTTP, `github.com/golang-jwt/jwt/v5`, `github.com/google/uuid`
- **Web**: Vanilla JS, Bootstrap 5 CDN, Chart.js 4 CDN
- **DB**: Cloudflare D1 (SQLite-compatible, REST API)
- **Pi 4**: Python 3, `requests`, `luma.oled`, `Pillow`, `gpiozero`, `pyserial`, `asyncio`
- **Pico**: CircuitPython 9.x, `adafruit_hid`

## Conventions
- Go: stdlib only where possible, no frameworks
- Web: no build step, pure vanilla JS + CDN libs
- All JSON responses: `{"success": bool, "data": ..., "message": "..."}`
- SPA: single `index.html`, sections shown/hidden via JS
- Commit after every completed phase
