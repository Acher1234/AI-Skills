# tuya-skill

> 🌐 *Version française : [README-FR.md](README-FR.md)*

Python CLI to interact with the **Tuya IoT** API — control smart devices (plugs, IR air conditioners, etc.).

## Installation

```bash
pip install tuya-connector-python
cp config.example.json config.json
# Edit config.json with your Tuya IoT credentials
```

## Configuration

The `config.json` file (not versioned, `.gitignore`) contains:

| Field | Description |
|-------|-------------|
| `auth_key` | Authorization Key (Tuya IoT Platform) |
| `access_id` | Access ID / Client ID |
| `access_secret` | Access Secret / Client Secret |
| `project_code` | Project Code (Tuya IoT Platform) |
| `region` | Region: `eu`, `us`, `cn`, `in` |

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
