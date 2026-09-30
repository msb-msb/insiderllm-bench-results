#!/bin/bash
for f in skills/skill_*.md; do
  tag=$(basename "$f" .md | sed 's/^skill_//')
  echo -n "$tag  "
  python3 run_arm.py "sk_$tag" test 1 --skill "$f" --outdir scored 2>&1 | head -1
done
