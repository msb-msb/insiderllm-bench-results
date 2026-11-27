#!/bin/bash
# Hard stop for stream-2026-11-26.py: kill its process group on Miu, then confirm no curl is left on Tamanna.
pg=$(cat "$(dirname "$0")/stream.pgid" 2>/dev/null) && kill -TERM -- "-$pg" 2>/dev/null; sleep 3
[ -n "$pg" ] && kill -KILL -- "-$pg" 2>/dev/null
sleep 2; echo "tamanna curls left:"; ssh tamanna 'pgrep -a -x curl || echo none'
