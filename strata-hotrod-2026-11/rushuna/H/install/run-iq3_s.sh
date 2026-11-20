#!/bin/sh
cd "/home/minotaur/hotrod-2026-11/H/src"
exec "/home/minotaur/hotrod-2026-11/H/src/.venv/bin/python" "/home/minotaur/hotrod-2026-11/H/src/serve/server.py" "--engine" "strata" "--config" "/home/minotaur/hotrod-2026-11/H/src/strata-iq3_s.json" "--port" "8080"
