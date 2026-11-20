#!/bin/sh
cd "/home/minotaur/hotrod-2026-11/U/src/terminal"
exec "/home/minotaur/hotrod-2026-11/U/src/terminal/.venv/bin/python" "/home/minotaur/hotrod-2026-11/U/src/terminal/serve/server.py" "--engine" "strata" "--config" "/home/minotaur/hotrod-2026-11/U/src/terminal/strata-iq3_s.json" "--port" "8080"
