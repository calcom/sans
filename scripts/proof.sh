#!/usr/bin/env bash
# proof.sh — run fontbakery (Google Fonts profile) and save a *dated* report under
# reference/proofs/, so every run is kept (never overwritten).
#
#   ./scripts/proof.sh                              # default: the gf-api fonts
#   ./scripts/proof.sh fonts/calsans-var-full/*.ttf # or any font paths you pass
#
# Works from whichever repo it lives in (calbuild or calcom/sans) — paths are
# resolved relative to the repo root.
set -euo pipefail
cd "$(cd "$(dirname "$0")/.." && pwd)"   # repo root

# protobuf 7.x (pulled in transitively by axisregistry) is incompatible with fontbakery's
# compiled protos — force the pure-Python parser so the checks run instead of crashing.
export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

# Locate fontbakery: PATH first, then the common framework-Python location.
FB="$(command -v fontbakery || true)"
[ -z "$FB" ] && FB="/Library/Frameworks/Python.framework/Versions/3.13/bin/fontbakery"
[ -x "$FB" ] || { echo "❌ fontbakery not found — 'pip install fontbakery' or edit the path in scripts/proof.sh"; exit 1; }

# Targets: passed args, else the gf-api fonts.
if [ "$#" -gt 0 ]; then TARGETS=("$@"); else TARGETS=(fonts/calsans-gf-api/*.ttf); fi

OUTDIR="reference/proofs"; mkdir -p "$OUTDIR"
STAMP="$(date +%Y-%m-%d_%H%M%S)"
OUT="$OUTDIR/fontbakery-${STAMP}.md"

echo "🔍 fontbakery (googlefonts) → $OUT"
printf '   targets:'; printf ' %s' "${TARGETS[@]}"; echo
# fontbakery exits non-zero when checks FAIL; keep going so the report always lands.
"$FB" check-googlefonts --loglevel WARN --succinct --ghmarkdown "$OUT" "${TARGETS[@]}" || true
if [ -s "$OUT" ]; then
    echo "✅ saved: $OUT"
else
    echo "❌ fontbakery produced no report (crashed — see errors above)"; exit 1
fi
