#!/usr/bin/env bash
set -euo pipefail

# Attempt LFS pull if inside a git repo with git-lfs available
if [ -d .git ] && command -v git-lfs &>/dev/null; then
  echo "→ Pulling Git LFS objects"
  git lfs pull || echo "  git lfs pull failed — continuing with files as-is"
fi

# Diagnostic: show NDJSON file sizes so logs reveal if LFS files are real
echo "→ NDJSON file sizes:"
ls -lh ndjson/*.ndjson 2>/dev/null || echo "  (none found)"

readarray -t ARGS < <(python3 scripts/build_args.py | tr -d '\r')
printf '→ Sources:\n'
printf '  %s\n' "${ARGS[@]}"
node scripts/build.mjs "${ARGS[@]}"
