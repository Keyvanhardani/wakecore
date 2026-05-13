#!/usr/bin/env bash
# Push WakeCore artifacts to Hugging Face.
#
# Usage:
#   hf auth login                       # one time, opens browser
#   bash hf/push.sh                     # pushes README + hotwords/
#   bash hf/push.sh --with-engine       # also uploads engine/ binaries
#
# The HF repo is a "model" repo at https://huggingface.co/keyvan-ai/wakecore
set -euo pipefail

REPO="keyvan-ai/wakecore"
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"

# 1. Make sure repo exists (idempotent)
hf repos create "$REPO" --repo-type model --exist-ok 2>&1 || true

# 2. Upload the HF-style README (model card)
hf upload "$REPO" "$HERE/README.md" README.md \
    --commit-message "update model card" --repo-type model

# 3. Upload sample .wake files
hf upload "$REPO" "$ROOT/hotwords" hotwords \
    --commit-message "sync sample hotword files" --repo-type model

# 4. Optionally upload engine binaries
if [[ "${1:-}" == "--with-engine" ]]; then
    if [[ ! -d "$ROOT/dist/engine" ]]; then
        echo "no engine binaries staged under dist/engine/ — skipping" >&2
        exit 0
    fi
    hf upload "$REPO" "$ROOT/dist/engine" engine \
        --commit-message "upload engine binaries" --repo-type model
fi

echo "✓ pushed to https://huggingface.co/$REPO"
