#!/bin/sh
cd "/home/minotaur/hotrod-2026-11/B/src"
exec "/home/minotaur/hotrod-2026-11/B/src/.venv/bin/python" "/home/minotaur/hotrod-2026-11/B/src/serve/server.py" "--engine" "strata" "--config" "/home/minotaur/hotrod-2026-11/B/src/strata-iq3_s.json" "--port" "8080"
