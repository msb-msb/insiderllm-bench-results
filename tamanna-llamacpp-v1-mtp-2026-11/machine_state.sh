#!/bin/bash
date -Is; uname -r; free -g | head -2; df -h / | tail -1
nvidia-smi --query-gpu=name,driver_version,pcie.link.gen.max,pcie.link.width.max,power.limit,clocks.max.sm,clocks.max.mem,temperature.gpu,memory.used --format=csv
cat /sys/class/dmi/id/board_name /sys/class/dmi/id/bios_version; lscpu | grep "Model name"
swapon --show; cat /proc/sys/vm/swappiness
