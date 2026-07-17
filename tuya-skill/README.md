# tuya-skill

> 🌐 *Version française : [README-FR.md](README-FR.md)*

Python CLI to interact with the **Tuya IoT** API — control smart devices (plugs, IR air conditioners, etc.).

## Installation

```bash
pip install tuya-connector-python
pip install tinytuya            # optional — only for local (LAN) mode
cp config.example.json config.json
# Edit config.json with your Tuya IoT credentials
```

## Project structure

The CLI is split into three modules (plus a compatibility shim):

| File | Role |
|------|------|
| `cloud.py` | Cloud commands (Tuya IoT API via `tuya-connector`) |
| `local.py` | Local commands (LAN via `tinytuya`) |
| `cmd.py` | Entry point — argparse + config loading + dispatch |
| `tuya.py` | Compatibility shim → runs `cmd.main()` (so `./tuya.py …` keeps working) |

`./tuya.py <command>` and `./cmd.py <command>` are equivalent.

## Create a Tuya account (get your credentials)

> ⚠️ Tuya often changes their portal and services. If these steps are outdated, please open an issue with screenshots so we can update them.

> **Prerequisite:** install the **Smart Life** app on your phone and pair all your devices in it *before* linking (the cloud project imports whatever is already in Smart Life).

1. Create a Tuya Developer account on [iot.tuya.com](https://iot.tuya.com). When it asks for the **"Account Type"**, select **"Skip this step..."**.
2. Click the **Cloud** icon → **Create Cloud Project**.
3. Pick the correct **Data Center "Region"** for your location (see the [Tuya data center list](https://developer.tuya.com/en/docs/iot/oem-app-data-center-distributed?id=Kafi0ku9l07qb)). This maps to the `region` field in `config.json` (`eu`, `us`, `cn`, `in`).
4. Skip the configuration wizard, but **remember the Authorization Key**: the **Access ID / Client ID** and **Access Secret / Client Secret** — you'll paste them into `config.json` (`access_id`, `access_secret`).
5. Click the **Cloud** icon → select your project → **Devices** → **Link Tuya App Account**.
6. Click **Add App Account** → a **"Link Tuya App Account"** dialog pops up. Choose **"Automatic"** and **"Read Only Status"** (commands will still work). Click **OK** — a **QR code** appears. Scan it with the **Smart Life** app: go to the **"Me"** tab → tap the QR/scan button **[..]** in the top-right corner. This links every device registered in your Smart Life app into your Tuya IoT project.
   - If the QR code won't scan, disable any browser theming plugins (e.g. **Dark Reader**) and try again.
7. **No devices?** If nothing shows up after scanning, select a **different data center** and edit your project (or create a new one) until your paired devices appear. The right data center isn't always the obvious one — e.g. some UK users report needing **"Central Europe"** instead of **"Western Europe"**.
8. **Service API:** under **"Service API"**, make sure both **IoT Core** and **Authorization** are listed. To be safe, click subscribe again on every service. **Disable popup blockers** — otherwise subscribing fails silently. Then authorize your project:
   - Click the **"Service API"** tab
   - Click **"Go to Authorize"**
   - Select the API Groups from the dropdown and click **Subscribe**

> **Renewal:** the **IoT Core** subscription expires after a while (1 month by default on first subscription). Once expired, the API can no longer talk to your Tuya account and must be renewed. As of November 12th 2024, it can be renewed for **1, 3 or 6 months** by filling a short form (project purpose, developer type).

Once you have the **Access ID**, **Access Secret**, **project code** and **region**, fill them into `config.json` (see below).

## Configuration

The `config.json` file (not versioned, `.gitignore`) contains:

| Field | Description |
|-------|-------------|
| `auth_key` | Authorization Key (Tuya IoT Platform) |
| `access_id` | Access ID / Client ID |
| `access_secret` | Access Secret / Client Secret |
| `project_code` | Project Code (Tuya IoT Platform) |
| `region` | Region: `eu`, `us`, `cn`, `in` |
| `use_local` | `true` to favor local (LAN) mode, `false` for cloud (default `false`) |
| `local_devices_file` | JSON file holding local keys (default `devices.json`) |

You can place the file elsewhere and point to it via the environment variable:

```bash
export TUYA_CONFIG_PATH=/root/.hermes/tuya-config.json
```

## Usage

```bash
# Generate an access token (authentication test)
./tuya.py token

# List all devices (name, ID, model, status)
./tuya.py devices

# Availability of a device (online / offline)
./tuya.py status <device_id>

# Detailed state with readable labels (mode, speed, temperature...)
./tuya.py state <device_id>

# Turn a device on
./tuya.py on <device_id>

# Turn a device off
./tuya.py off <device_id>

# Rename a device
./tuya.py rename <device_id> "New name"
```

## Available commands

| Command | Description |
|---------|-------------|
| `token` | Generate an access token (verifies credentials) |
| `devices` | List all devices on the account |
| `status <device_id>` | Availability: `🟢 online` / `🔴 offline` |
| `state <device_id>` | Detailed state (power, mode, temp, wind...) with labels |
| `on <device_id>` | Turn the device on |
| `off <device_id>` | Turn the device off |
| `rename <device_id> <name>` | Rename the device |

> `on` / `off` automatically detect the right command code:
> `switch_1` for plugs, `switch` for IR air conditioners.

## Local mode (LAN via tinytuya)

Local mode talks to devices **directly over your LAN**, without going through the cloud. To control a device locally you need its **local key** — which is *not* exposed by the LAN scan. The scan only reveals `ip` + `device_id` + `version`; the local keys are fetched from the **cloud** (`tinytuya.Cloud.getdevices()`, same mechanism as the tinytuya `wizard`).

> **Requirements:** run these from a machine on the **same LAN** as your devices, close the Smart Life app, and allow **UDP 6666/6667/7000** and **TCP 6668** through the firewall.

```bash
# 1) Scan the LAN → ip + device_id + version (no local keys)  → writes tuya-scan.json
./tuya.py local-scan
./tuya.py local-scan --seconds 50        # scan longer if devices are missing

# 2) Fetch local keys via the cloud, merge scan IPs  → writes devices.json
./tuya.py local-sync                      # keys masked in the output
./tuya.py local-sync --show-keys          # print keys in clear text
./tuya.py local-sync --no-scan --device-id <id>   # no LAN scan, provide a sample id

# 3) List devices from devices.json
./tuya.py local-devices
./tuya.py local-devices --show-keys
```

How `local-sync` works:

1. Scans the LAN to collect IPs (and picks a sample `device_id`).
2. Calls `Cloud.getdevices()` with your `access_id` / `access_secret` / `region` → gets `id` + `name` + `key` (local key).
3. Merges the scanned IP into each device → writes `devices.json`.

> ⚠️ `devices.json` and `tuya-scan.json` contain secrets (local keys). They are already in `.gitignore` — never commit them.

### Local commands

| Command | Description |
|---------|-------------|
| `local-scan [--seconds N]` | Scan the LAN → `ip` + `device_id` + `version` → `tuya-scan.json` |
| `local-sync [--device-id ID] [--seconds N] [--no-scan] [--show-keys]` | Fetch local keys via the cloud → `devices.json` |
| `local-devices [--show-keys]` | List devices from `devices.json` |

## Sample output

### devices
```
📱 Tuya devices (2):

  • Living room plug
    ID       : bfxxxxxxxxxxxxxxxxxx
    Model    : SP-01
    Status   : 🟢 online

  • Bedroom AC
    ID       : bfyyyyyyyyyyyyyyyyyy
    Model    : IR-AC
    Status   : 🔴 offline
```

### state
```
📊 State of "bfxxxxxxxxxxxxxxxxxx":

  🔌 Switch            : 🟢 ON
  🔄 Mode              : cool
  🌡️ Temp             : 22
  💨 Wind              : auto
```

## Value mapping

| Code | Values |
|------|--------|
| `mode` | `0` auto · `1` cool · `2` heat · `3` fan · `4` dry |
| `wind` / `fan` | `0` low · `1` mid · `2` high · `3` auto |

## Tuya regions (endpoints)

| Region | Base URL |
|--------|----------|
| `eu` | `https://openapi.tuyaeu.com` |
| `us` | `https://openapi.tuyaus.com` |
| `cn` | `https://openapi.tuyacn.com` |
| `in` | `https://openapi.tuyain.com` |

## Dependencies

See [`dependencies.md`](dependencies.md) for the full list.

## Tuya API used

- `GET /v2.0/cloud/thing/device` — device list
- `GET /v1.0/devices/{id}/status` — detailed state
- `POST /v1.0/devices/{id}/commands` — send commands (on/off)
- `PUT /v1.0/devices/{id}` — rename
