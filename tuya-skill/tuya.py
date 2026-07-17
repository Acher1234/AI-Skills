#!/usr/bin/env python3
"""
Shim de compatibilité — le CLI vit désormais dans cmd.py.

Découpage :
  - cloud.py → commandes Cloud (API Tuya IoT)
  - local.py → commandes Local (LAN via tinytuya)
  - cmd.py   → dispatch argparse (point d'entrée réel)

`./tuya.py <commande>` reste équivalent à `./cmd.py <commande>`.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cmd import main  # noqa: E402  (ajout du dossier au path avant import)

if __name__ == "__main__":
    main()
