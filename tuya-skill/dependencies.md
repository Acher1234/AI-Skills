# 📦 Dependencies — tuya-skill

| Package | Version | Install | Usage |
|---------|---------|---------|-------|
| `python3` | 3.11+ | `apt-get install python3` | Runtime Python |
| `tuya-connector-python` | 0.1.2+ | `pip install tuya-connector-python` | SDK Tuya IoT (auth, API calls) |
| `pycryptodome` | (auto) | installé avec tuya-connector | Crypto pour signatures |
| `websocket-client` | (auto) | installé avec tuya-connector | WebSocket pour MQTT Tuya |
| `tinytuya` | 1.15+ | `pip install tinytuya` | Mode local (LAN) : scan + récupération des local keys |