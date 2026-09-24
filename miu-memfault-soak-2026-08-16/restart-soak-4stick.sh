#!/usr/bin/env bash
# Restart the bit-6 soak on Miu's FOUR sticks, one of them a replacement,
# 2026-08-24.
#
# This is a NEW RUN against DIFFERENT HARDWARE, not a resumption. The bad
# Samsung M378A2K43DB1-CTD removed on 2026-08-18 has been replaced with
# another M378A2K43DB1-CTD (ordered 2026-08-18, delivery window 08-21..08-25,
# arrived early). The new stick was tested alone, then all four together:
# full memtest86+ pass, zero errors.
#
# Third configuration, third question:
#   run 1 (four original sticks)  did the reseat fix it?      -> NO, event 5.
#   run 2 (three sticks, bad one removed)  is a second stick also bad?
#   run 3 (this one)  is the REPLACEMENT clean, and is the full four-stick
#                     config clean under sustained page-cache residency?
#
# Counters are reset because the three-stick run's exposure describes a
# different physical configuration and does not transfer. The old state file
# is archived into the repo first: it is the evidence record for that run.
#
# Run:  sudo bash restart-soak-4stick.sh
set -euo pipefail

SOAKDIR="/home/minotaur/Desktop/InsiderLLM/docs/bench-results/miu-memfault-soak-2026-08-16"
LOG="$SOAKDIR/soak.log"
STATE_DIR="/var/lib/miu-memfault-soak"
STATE="$STATE_DIR/state.json"
ARCHIVE="$SOAKDIR/state-3stick-final-2026-08-24.json"
OWNER="minotaur:minotaur"

[ "$(id -u)" -eq 0 ] || { echo "must run as root (sudo bash $0)"; exit 1; }

TS="$(date +%Y-%m-%dT%H:%M:%S%z)"
MEMKB="$(awk '/MemTotal/{print $2}' /proc/meminfo)"
MEMGIB="$(awk '/MemTotal/{printf "%.1f", $2/1048576}' /proc/meminfo)"

# --- 1. refuse to run if the replacement is not seated or not detected ------
# 4x16GB reports ~62 GiB; 3x16GB reports ~47 GiB. A 3-stick reading here means
# the replacement is absent, unseated, or not being trained, and this run would
# be measuring the OLD three-stick configuration under a new label. The guard
# is the inverse of the one in restart-soak-3stick.sh, deliberately.
if [ "$MEMKB" -le 56000000 ]; then
    echo "REFUSING: MemTotal ${MEMGIB} GiB looks like a 3-stick config."
    echo "The replacement DIMM is not seated or not detected. Aborting."
    exit 1
fi
echo "memory check: ${MEMGIB} GiB — consistent with 4 x 16 GB. proceeding."

# --- 2. stop the timer before touching state -------------------------------
# The three-stick run was still LIVE at restart time (it auto-resumed after the
# RAM-install reboot and logged cycle 415 against three-stick counters). Unlike
# the 08-18 restart, whose prior state carried "stopped": true, this one must
# be halted first or a firing cycle could rewrite the fresh state from under us.
systemctl stop miu-memfault-soak.timer   || true
systemctl stop miu-memfault-soak.service || true
echo "timer and service stopped"

# --- 3. archive the old state; never clobber an existing archive ------------
if [ -f "$ARCHIVE" ]; then
    echo "archive already exists, leaving it untouched: $ARCHIVE"
elif [ -f "$STATE" ]; then
    cp -p "$STATE" "$ARCHIVE"
    chown "$OWNER" "$ARCHIVE"
    echo "archived old state -> $ARCHIVE"
else
    echo "no existing state file at $STATE (nothing to archive)"
fi

# --- 4. record the run boundary in the log, not just in a report ------------
# Kinds here are deliberately NOT in soak.py's CYCLE_KINDS, so backfill() skips
# them rather than counting them as cycles.
{
  echo "$TS | RUN-BOUNDARY | ===== END OF 3-STICK RUN / START OF 4-STICK REPLACEMENT RUN ====="
  echo "$TS | HARDWARE-CHANGE | replacement Samsung M378A2K43DB1-CTD installed 2026-08-24, restoring slot 3 | ordered 2026-08-18, delivery window 08-21..08-25, arrived early | new stick tested alone, then all four together: full memtest86+ pass, zero errors | MemTotal now ${MEMGIB} GiB, was ~47 GiB"
  echo "$TS | COUNTER-RESET | credited/blind/cycle counters reset to zero — the three-stick run's exposure describes a DIFFERENT physical configuration and does not transfer | prior state archived at docs/bench-results/miu-memfault-soak-2026-08-16/state-3stick-final-2026-08-24.json"
  echo "$TS | PURPOSE | this run asks IS THE REPLACEMENT STICK CLEAN, AND IS THE FULL FOUR-STICK CONFIG CLEAN UNDER SUSTAINED RESIDENCY | it does not re-ask either earlier question: run 1 asked did the reseat fix it (answered NO, event 5), run 2 asked is a second stick also bad"
  echo "$TS | EVIDENCE-CAVEAT | the replacement is USED hardware from an eBay seller | a full memtest86+ pass is good evidence, not proof — it is a bounded-time test and the original fault took sustained page-cache residency to surface | the last two used-hardware purchases into this box were BOTH defective, which is precisely why this run matters"
  echo "$TS | HEADROOM | back to ~62 GiB from ~47 GiB, so expect a materially better credit ratio than the three-stick run (which ended at 0.0% credited over 142.32h blind) | Brave will still evict the mapped pages if it is running — a broken residency clock is a Brave problem, not a hardware signal"
} >> "$LOG"
echo "wrote run-boundary block to $LOG"

# --- 5. fresh state -------------------------------------------------------
# Every counter key is written explicitly, INCLUDING blind_s. soak.py's
# backfill() short-circuits on `if "blind_s" in st` (line 204); without that key
# it would rescan the whole soak.log and silently reconstruct the previous run's
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
    "run_label": "4-stick post-replacement soak, started 2026-08-24",
    "run_question": "is the replacement stick clean, and is the full four-stick config clean under sustained residency",
}, open(sys.argv[1], "w"), indent=1)
PY
echo "fresh state written -> $STATE"
cat "$STATE"

# --- 6. re-enable the timer and take one cycle now -------------------------
systemctl enable miu-memfault-soak.timer
systemctl start  miu-memfault-soak.timer
echo "running one cycle now (blocks ~45s)..."
systemctl start  miu-memfault-soak.service

echo
echo "=== timer ==="
systemctl is-enabled miu-memfault-soak.timer
systemctl is-active  miu-memfault-soak.timer
systemctl list-timers miu-memfault-soak.timer --all --no-pager
echo
echo "=== first cycle ==="
tail -n 10 "$LOG"
