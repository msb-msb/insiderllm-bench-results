#!/usr/bin/env python3
"""power-01 run driver: one IDLE or GENERATE window on one board.

  run.py gen  --board s3|p4 --build B|D|P4 --rep N [--secs 300] [--no-logger] [--meter] [--reset] [--post-idle 60]
  run.py idle --board s3|p4 --build B|D|P4 --rep N [--secs 300] [--no-logger] [--meter] [--reset]

Energy comes from the USB power logger (tools/power-logger; INA226 on VBUS, high
side, between Miu and the board). The logger run starts just before the window
and stops just after it, so its energy, mean power, duration, sample count and
dropped frames go into runs.jsonl with the run. Raw frames and the plot go to
logs/<tag>.power/. In gen mode, with a SYNC_GPIO build on the board, each
generation is one sync-high window, and J/token = window energy / tokens, paired
generation by generation with gens.csv (a count mismatch refuses to pair).

--meter marks the one cross-check run per board that also has the cheap inline
meter in the chain: Mark reads its mWh and t just before and just after the run
(it can't be zeroed; never difference across a meter move). The meter's window is
longer than this script's by the two hand-off gaps; RESULTS charges those gaps at
the logger's measured idle power when it compares the two.

gen: back-to-back greedy generations through the interactive protocol (tools/chat.py
Board), compiled prompt 433 447 259 405, N=200, t=0, seed 42, eot=0, for at least
--secs; the generation running at the deadline finishes, and the window is recorded as
first send -> last D line. Every generation's firmware ms/token and token count is logged.
idle: the board sits at its prompt; '?' is sent once at the start and once at the end
to confirm the firmware is alive (the end ping is retried up to 3 times, ~5 s apart, reopening
the port; if all fail the rep is FAILED, liveness unconfirmed, but still recorded). Nothing
else touches the port. The logger run is always finalized and the record always written.
"""
import argparse, csv, datetime as dt, importlib.util, json, os, statistics, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
PORTS = {"s3": "/dev/serial/by-id/usb-Espressif_USB_JTAG_serial_debug_unit_10:51:DB:xx:xx:xx-if00",
         "p4": "/dev/serial/by-id/usb-1a86_USB_Single_Serial_5C93015982-if00"}
# Reference ms/token for the 3% gate: the benchmark figure for each build (see PREREG).
REF_MS = {"B": 32.7, "D": 25.8, "P4": 13.7}
PROMPT, N, SEED = [433, 447, 259, 405], 200, 42

spec = importlib.util.spec_from_file_location("chat", os.path.join(REPO, "tools", "chat.py"))
chat = importlib.util.module_from_spec(spec); spec.loader.exec_module(chat)
sys.path.insert(0, os.path.join(REPO, "tools", "power-logger", "host"))
# Logger summary fields copied into runs.jsonl.
LOGGER_KEYS = ["energy_J_firmware", "energy_J_host", "host_vs_firmware_pct", "agree_within_0p5pct",
               "mean_power_W", "duration_s", "samples_firmware", "samples_received", "effective_rate_Hz",
               "dropped_frames", "late_conversions", "bus_errors", "sync_energy_J", "sync_time_s"]


def reset_board(port, log):
    """Fresh reset (power-01 idle definition): an RTS pulse, then wait for the boot's R line.
    On the S3 the USB port drops during the pulse ([Errno 71] on the RTS release); that is
    the reset happening. Returns (Board, boot_seen): boot_seen means a boot banner line (fp=)
    reached the log after the pulse, i.e. the chip really rebooted."""
    t = time.time()
    s = chat.serial.Serial(port, 115200, timeout=0.05)
    try:
        s.dtr = False; s.rts = True; time.sleep(0.1); s.rts = False
    except OSError:
        pass
    try:
        s.close()
    except Exception:
        pass
    while time.time() - t < 120:
        try:
            board = chat.Board(port, log=log)
            break
        except (chat.serial.SerialException, OSError, SystemExit):
            time.sleep(0.2)
    else:
        sys.exit("board did not come back after the reset")
    lines = [l for l in open(log, "rb").read().split(b"\n") if l]
    return board, any(b"fp=" in l and float(l.split()[0]) > t for l in lines)


def ping_alive(board, tries=3, gap_s=5.0):
    """End-of-window liveness: '?' -> R line. On a miss, wait gap_s, reopen the port and ask
    again, up to `tries` attempts in all. Each attempt records how long the port had been open
    (to see whether misses follow long idle on the USB link). Returns (ok, attempts)."""
    attempts = []
    for k in range(tries):
        if k:
            time.sleep(gap_s)
            try:
                board.s.close()
            except Exception:
                pass
            try:
                board.s.open()
                board.buf = b""
                board.t_open = time.time()
            except (OSError, chat.serial.SerialException) as e:
                attempts.append({"ok": False, "reopened": False, "error": str(e)})
                continue
        att = {"at": stamp(), "port_open_s": round(time.time() - board.t_open, 1), "reopened": bool(k)}
        try:
            board.wait_ready(10.0, ping=True)
            attempts.append(dict(att, ok=True))
            return True, attempts
        except (SystemExit, OSError, chat.serial.SerialException) as e:
            attempts.append(dict(att, ok=False, error=str(e)))
    return False, attempts


def stamp():
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["gen", "idle"])
    ap.add_argument("--board", required=True, choices=PORTS)
    ap.add_argument("--build", required=True, choices=REF_MS)
    ap.add_argument("--rep", required=True, type=int)
    ap.add_argument("--secs", type=float, default=300.0)
    ap.add_argument("--no-logger", action="store_true", help="meter only (the old protocol)")
    ap.add_argument("--meter", action="store_true", help="cheap meter inline: the cross-check run")
    ap.add_argument("--app-sha", default="", help="sha256 of the flashed app, recorded with the run")
    ap.add_argument("--reset", action="store_true", help="fresh reset before the window (idle definition)")
    ap.add_argument("--suffix", default="", help="tag suffix, e.g. 'r' for a rerun (keeps the failed rep's logs)")
    ap.add_argument("--post-idle", type=float, default=0.0,
                    help="gen: a separate logger capture of this many seconds right after the window (exploratory)")
    a = ap.parse_args()
    tag = f"{a.build}_{a.mode}_{a.rep}{a.suffix}"
    log = os.path.join(HERE, "logs", f"{tag}.serial.log")
    pl = run = None
    if not a.no_logger:
        from powerlog import PowerLogger
        pl = PowerLogger()           # never opens the bench boards' ports (see powerlog/device.py)
    if a.reset:
        board, boot_seen = reset_board(PORTS[a.board], log)
        if not boot_seen:
            sys.exit("--reset: no boot banner after the pulse; the board may not have rebooted")
    else:
        board = chat.Board(PORTS[a.board], log=log)
    board.t_open = time.time()
    rec = {"tag": tag, "board": a.board, "build": a.build, "mode": a.mode, "rep": a.rep,
           "ready": board.ready, "meter_inline": a.meter, "app_sha256": a.app_sha, "start": stamp()}
    if a.reset:
        rec["reset"] = {"fresh_reset": True, "boot_seen": boot_seen}
    if pl:
        run = pl.start(tag, board=a.board, build=a.app_sha or a.build, notes=f"power-01 {a.mode}",
                       run_dir=os.path.join(HERE, "logs", f"{tag}.power"), ready=board.ready)
    t0 = time.time()
    rows, tokens = [], 0
    try:
        if a.mode == "idle":
            time.sleep(max(0.0, a.secs - (time.time() - t0)))
            rec.update(window_s=round(time.time() - t0, 3), tokens=0)
            ok, attempts = ping_alive(board)       # still alive at the end
            rec.update(ping_ok=ok, ping_attempts=attempts)
            if not ok:
                rec["status"] = "FAILED (liveness unconfirmed)"
        else:
            while time.time() - t0 < a.secs:
                r = board.generate(PROMPT, N, 0.0, 1.0, SEED, False)
                tokens += len(r["ids"])
                rows.append({"t_end_s": round(time.time() - t0, 3), "n": r["n"], "ids": len(r["ids"]),
                             "decode_ms_per_tok": r["decode_ms_per_tok"], "ttft_us": r["ttft_us"],
                             "ids_head": " ".join(map(str, r["ids"][:5]))})
            window = time.time() - t0
            with open(os.path.join(HERE, "logs", f"{tag}.gens.csv"), "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
            ms = statistics.median(x["decode_ms_per_tok"] for x in rows)
            dev = (ms - REF_MS[a.build]) / REF_MS[a.build]
            same_out = len({x["ids_head"] for x in rows}) == 1 and all(x["n"] == N for x in rows)
            rec.update(window_s=round(window, 3), tokens=tokens, generations=len(rows),
                       median_ms_per_tok=ms, ms_min=min(x["decode_ms_per_tok"] for x in rows),
                       ms_max=max(x["decode_ms_per_tok"] for x in rows), ref_ms=REF_MS[a.build],
                       ms_dev_pct=round(100 * dev, 2), gate_3pct="PASS" if abs(dev) <= 0.03 else "FAIL",
                       all_generations_identical=same_out)
    except BaseException as e:
        # the window broke off: keep and record what was measured
        rec.update(status=f"FAILED (window aborted: {type(e).__name__}: {e})",
                   window_s=round(time.time() - t0, 3), tokens=tokens, generations=len(rows))
        raise
    finally:
        # Always finalize the logger run (final snapshot, host-vs-firmware check, summary)
        # and write the record, whether or not the window or the end ping succeeded.
        rec["end"] = stamp()
        if run:
            s = run.stop()
            rec["logger"] = {k: s.get(k) for k in LOGGER_KEYS}
            rec["logger"].update(gaps=len(s["gaps"]), sync_windows=len(s.get("sync_windows", [])),
                                 sync_glitches=len(s.get("sync_glitches", [])),
                                 run_dir=os.path.relpath(run.dir, HERE), calibration=s["calibration"]["source"],
                                 logger_src=pl.cfg2.get("src"), logger_uid=pl.cfg2.get("uid"))
            if a.mode == "gen" and rows:
                from powerlog import joules_per_token
                toks = [x["ids"] for x in rows]
                if s.get("sync_windows"):
                    try:
                        rec["logger"]["j_per_token"] = joules_per_token(s, toks)
                    except ValueError as e:
                        rec["logger"]["j_per_token_error"] = str(e)
                else:
                    rec["logger"]["j_per_token"] = {"note": "no sync edges: whole window only (not a SYNC_GPIO build?)",
                                                    "J_per_token_whole_run": s["energy_J_firmware"] / tokens}
            if a.mode == "gen" and a.post_idle > 0 and "status" not in rec:
                # Exploratory (PREREG): the board idles right after the window; nothing touches its port.
                # Its own logger run and tag; never used for scoring, and a failure here doesn't fail the rep.
                try:
                    prun = pl.start(f"{tag}_postidle", board=a.board, build=a.app_sha or a.build,
                                    notes=f"power-01 post-generate idle, {a.post_idle:g} s (exploratory)",
                                    run_dir=os.path.join(HERE, "logs", f"{tag}_postidle.power"))
                    time.sleep(a.post_idle)
                    ps = prun.stop()
                    rec["post_idle"] = {"exploratory": True, "secs": a.post_idle,
                                        **{k: ps.get(k) for k in LOGGER_KEYS},
                                        "gaps": len(ps["gaps"]), "sync_windows": len(ps.get("sync_windows", [])),
                                        "sync_glitches": len(ps.get("sync_glitches", [])),
                                        "run_dir": os.path.relpath(prun.dir, HERE)}
                except Exception as e:
                    rec["post_idle"] = {"exploratory": True, "error": f"{type(e).__name__}: {e}"}
            pl.close()
        with open(os.path.join(HERE, "runs.jsonl"), "a") as f:
            f.write(json.dumps(rec) + "\n")
        print(json.dumps(rec, indent=1))
    if rec.get("status", "").startswith("FAILED"):
        sys.exit(f"{tag}: {rec['status']}")
    if rec.get("gate_3pct") == "FAIL":
        sys.exit("3% gate FAILED: stop")


if __name__ == "__main__":
    main()
