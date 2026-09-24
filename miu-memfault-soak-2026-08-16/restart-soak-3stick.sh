#!/usr/bin/env bash
# Restart the bit-6 soak on Miu's THREE surviving sticks, 2026-08-18.
#
# This is a NEW RUN against DIFFERENT HARDWARE, not a resumption. The bad
# Samsung M378A2K43DB1-CTD was bisected out and physically removed on
# 2026-08-18; the box now runs 3 sticks in slots 0,1,2.
#
# The previous run asked "did the DIMM reseat fix it". This one asks "is a
# SECOND stick also bad". A clean result here is evidence about the three
# survivors — it is NOT evidence about a repair.
#
# Counters are reset because the old ~13.44 h of credited exposure describes a
# four-stick configuration and means nothing here. The old state file is
# archived into the repo first: it is the evidence record for events 1-5.
#
# Run:  sudo bash restart-soak-3stick.sh
set -euo pipefail

SOAKDIR="/home/minotaur/Desktop/InsiderLLM/docs/bench-results/miu-memfault-soak-2026-08-16"
LOG="$SOAKDIR/soak.log"
STATE_DIR="/var/lib/miu-memfault-soak"
STATE="$STATE_DIR/state.json"
ARCHIVE="$SOAKDIR/state-4stick-final-2026-08-18.json"
OWNER="minotaur:minotaur"

[ "$(id -u)" -eq 0 ] || { echo "must run as root (sudo bash $0)"; exit 1; }

TS="$(date +%Y-%m-%dT%H:%M:%S%z)"
MEMKB="$(awk '/MemTotal/{print $2}' /proc/meminfo)"
MEMGIB="$(awk '/MemTotal/{printf "%.1f", $2/1048576}' /proc/meminfo)"

# --- 1. refuse to run if the bad stick is somehow still installed -----------
# 4x16GB reported ~62 GiB; 3x16GB reports ~47 GiB. A 4-stick reading here means
# the physical removal did not happen and this run would be measuring the old
# configuration under a new label.
if [ "$MEMKB" -gt 56000000 ]; then
    echo "REFUSING: MemTotal ${MEMGIB} GiB looks like a 4-stick config."
    echo "This script is only valid with the bad DIMM removed. Aborting."
    exit 1
fi
echo "memory check: ${MEMGIB} GiB — consistent with 3 x 16 GB. proceeding."

# --- 2. archive the old state; never clobber an existing archive ------------
if [ -f "$ARCHIVE" ]; then
    echo "archive already exists, leaving it untouched: $ARCHIVE"
elif [ -f "$STATE" ]; then
    cp -p "$STATE" "$ARCHIVE"
    chown "$OWNER" "$ARCHIVE"
    echo "archived old state -> $ARCHIVE"
else
    echo "no existing state file at $STATE (nothing to archive)"
fi

# --- 3. record the run boundary in the log, not just in a report ------------
# Kinds here are deliberately NOT in soak.py's CYCLE_KINDS, so backfill() skips
# them rather than counting them as cycles.
{
  echo "$TS | RUN-BOUNDARY | ===== END OF 4-STICK RUN / START OF 3-STICK RUN ====="
  echo "$TS | HARDWARE-CHANGE | bad Samsung M378A2K43DB1-CTD bisected out and physically removed 2026-08-18 (bit 6, physaddr 0x56873d905, confirmed by memtest86+ 7.00 on bare metal, 22+ errors in one pass) | MemTotal now ${MEMGIB} GiB, was ~62 GiB"
  echo "$TS | COUNTER-RESET | credited/blind/cycle counters reset to zero — the prior 13.44h of credited exposure describes the FOUR-STICK configuration and does not transfer to this hardware | prior state archived at docs/bench-results/miu-memfault-soak-2026-08-16/state-4stick-final-2026-08-18.json"
  echo "$TS | PURPOSE | this run asks IS A SECOND STICK ALSO BAD — it does NOT ask whether a repair worked | a clean result here is evidence about the three surviving sticks only, and absence of an event still is not proof of a healthy machine"
  echo "$TS | CONFIG-WARNING | 3 sticks in slots 0,1,2 on a dual-channel board — ASYMMETRIC, not dual-channel symmetric | NO published benchmark numbers off this box until the replacement DIMM lands and all four pass a full memtest86+ pass"
} >> "$LOG"
echo "wrote run-boundary block to $LOG"

# --- 4. fresh state -------------------------------------------------------
# Every counter key is written explicitly, INCLUDING blind_s. soak.py's
# backfill() short-circuits on `if "blind_s" in st`; without that key it would
# rescan the whole soak.log and silently reconstruct the 4-stick run's
# cycles_credited / cycles_blind / blind_s / run_start_ts into this run.
# 'stopped' is omitted so main() no longer exits early, and boot_id is omitted
# so the first cycle emits its own DISCONTINUITY line.
mkdir -p "$STATE_DIR"
python3 - "$STATE" <<'PY'
import json, sys, time
json.dump({
    "run_start_ts": time.time(),
    "credited_s": 0.0,
    "blind_s": 0.0,
    "cycles": 0,
    "cycles_credited": 0,
    "cycles_blind": 0,
    "discontinuities": 0,
    "run_label": "3-stick post-removal soak, started 2026-08-18",
    "run_question": "is a second stick also bad",
}, open(sys.argv[1], "w"), indent=1)
PY
echo "fresh state written -> $STATE"
cat "$STATE"

# --- 5. re-enable the timer and take one cycle now -------------------------
systemctl enable miu-memfault-soak.timer
systemctl start  miu-memfault-soak.timer
echo "running one cycle now (blocks ~35s)..."
systemctl start  miu-memfault-soak.service

echo
echo "=== timer ==="
systemctl is-enabled miu-memfault-soak.timer
systemctl is-active  miu-memfault-soak.timer
systemctl list-timers miu-memfault-soak.timer --all --no-pager
echo
echo "=== first cycle ==="
tail -n 8 "$LOG"
