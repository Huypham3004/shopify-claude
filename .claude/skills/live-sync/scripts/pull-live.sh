#!/usr/bin/env bash
# Pull the LIVE theme of each demo store into demo-live/<Label>/.
# Only template JSON is pulled — that is the entire comparison surface of /live-sync.
#
#   pull-live.sh                 # every preset in demo-live/stores.json
#   pull-live.sh Verso Wiggle    # only those labels (or preset ids: preset-1)
#   pull-live.sh --dry-run       # print the commands, download nothing
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
CONFIG="$ROOT/demo-live/stores.json"

DRY_RUN=0
FILTERS=()
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    -*) echo "unknown flag: $arg" >&2; exit 2 ;;
    *) FILTERS+=("$arg") ;;
  esac
done

if [[ ! -f "$CONFIG" ]]; then
  cat >&2 <<'MSG'
error: demo-live/stores.json not found.

Create it first (one entry per preset in src/config/settings_data.js):

{
  "presets": [
    { "preset": "preset-1", "label": "Verso",  "store": "verso-x1cydwte.myshopify.com" },
    { "preset": "preset-2", "label": "Timbre", "store": "timbre-cbtmc5nj.myshopify.com" },
    { "preset": "preset-3", "label": "Wiggle", "store": "wiggle-duviydn1.myshopify.com" }
  ]
}
MSG
  exit 1
fi

# rows: preset<TAB>label<TAB>store
ROWS="$(python3 - "$CONFIG" "${FILTERS[@]+"${FILTERS[@]}"}" <<'PY'
import json, sys
cfg = json.load(open(sys.argv[1], encoding="utf-8"))
filters = {f.lower() for f in sys.argv[2:]}
for e in cfg.get("presets", []):
    preset, label, store = e.get("preset", ""), e.get("label", ""), e.get("store", "")
    if not (preset and label and store):
        sys.exit(f"error: incomplete entry in stores.json: {e!r}")
    if filters and label.lower() not in filters and preset.lower() not in filters:
        continue
    print(f"{preset}\t{label}\t{store}")
PY
)" || exit 1

if [[ -z "$ROWS" ]]; then
  echo "error: no preset matched ${FILTERS[*]:-<all>} in demo-live/stores.json" >&2
  exit 1
fi

FAILED=()
while IFS=$'\t' read -r preset label store; do
  [[ -z "$preset" ]] && continue
  dest="$ROOT/demo-live/$label"
  echo ""
  echo "── $label ($preset) ← live theme of $store"
  cmd=(npx shopify theme pull --live --nodelete --store="$store" --path="$dest"
       --only "templates/*.json" --only "templates/customers/*.json")
  if [[ $DRY_RUN -eq 1 ]]; then
    printf '   [dry-run] %s\n' "${cmd[*]}"
    continue
  fi
  mkdir -p "$dest"
  if ! (cd "$ROOT" && "${cmd[@]}"); then
    echo "   ✗ pull failed for $label" >&2
    FAILED+=("$label")
  fi
done <<< "$ROWS"

echo ""
if [[ ${#FAILED[@]} -gt 0 ]]; then
  echo "✗ failed: ${FAILED[*]}" >&2
  exit 1
fi
echo "✓ pull complete → demo-live/"
