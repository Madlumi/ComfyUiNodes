#!/usr/bin/env bash
set -u

usage() {
  cat <<'USAGE'
Usage:
  fileToCiv.sh [-h] <lora_file> [more_files...]

For each LoRA file, resolves its Civitai modelVersionId via /model-versions/by-hash/<hash>
then calls civs.sh like:
  civs.sh "https://civitai.com/?modelVersionId=<id>" <lora_file>

Deps: curl jq sha256sum (optional: b3sum)
Env:
  CIVS_SH=/path/to/civs.sh   (optional override)
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then usage; exit 0; fi
if [[ $# -lt 1 ]]; then usage; exit 1; fi

for cmd in curl jq sha256sum; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "missing: $cmd" >&2; exit 1; }
done

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CIVS_SH="${CIVS_SH:-$SCRIPT_DIR/civs.sh}"
[[ -f "$CIVS_SH" ]] || { echo "civs.sh not found at: $CIVS_SH" >&2; exit 1; }

lookup_mv_id() {
  local h="$1" tmp
  tmp="$(mktemp)"
  if curl -fsSL "https://civitai.com/api/v1/model-versions/by-hash/$h" -o "$tmp"; then
    jq -r '.id // empty' "$tmp"
  fi
  rm -f "$tmp"
}

rc=0
for lora in "$@"; do
  if [[ ! -f "$lora" ]]; then
    echo "skip (not a file): $lora" >&2
    rc=1
    continue
  fi

  sha256="$(sha256sum "$lora" | awk '{print $1}')"
  mv_id="$(lookup_mv_id "$sha256" || true)"

  if [[ -z "$mv_id" ]] && command -v b3sum >/dev/null 2>&1; then
    blake3="$(b3sum "$lora" | awk '{print $1}')"
    mv_id="$(lookup_mv_id "$blake3" || true)"
  fi

  if [[ -z "$mv_id" ]]; then
    echo "no civitai match for: $lora" >&2
    rc=1
    continue
  fi

  civ_url="https://civitai.com/?modelVersionId=$mv_id"
  echo "[$lora] -> $civ_url" >&2

  if ! bash "$CIVS_SH" "$civ_url" "$lora"; then
    echo "civs.sh failed for: $lora" >&2
    rc=1
    continue
  fi

done

exit $rc
