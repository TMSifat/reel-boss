#!/usr/bin/env bash
# Reel Boss publish linter.
#
#   lint.sh "caption or hook text"     lint publishable text
#   lint.sh --cta VET                  check a CTA keyword against the burned list
#   lint.sh --file path.txt            lint the contents of a file
#   lint.sh --allow-free "text"        "free" warns instead of failing (a deliberate call)
#
# Exits 0 clean, 1 on any violation.

set -uo pipefail

# One ledger: the one newreel.py appends to. Bundled copy first, the old Mac
# install path second, so lint and the pipeline never read two different lists.
BUNDLED="$(cd "$(dirname "$0")/.." && pwd)/reel-system/keywords_burned.txt"
if [ -f "$BUNDLED" ]; then DEFAULT_BURNED="$BUNDLED"
else DEFAULT_BURNED="$HOME/Documents/Notes/reel-system/keywords_burned.txt"; fi
BURNED="${REEL_BURNED_KEYWORDS:-$DEFAULT_BURNED}"
fail=0
allow_free=0
if [ "${1:-}" = "--allow-free" ]; then allow_free=1; shift; fi

die() { printf 'FAIL  %s\n' "$1"; fail=1; }
ok()  { printf 'ok    %s\n' "$1"; }

lint_text() {
  local text="$1"

  # dashes: em dash, en dash, horizontal bar, minus sign, double hyphen
  local hits
  hits=$(printf '%s' "$text" | grep -o -e '—' -e '–' -e '―' -e '−' -e '--' | sort -u | tr '\n' ' ')
  if [ -n "$hits" ]; then
    die "dash characters found: $hits  (banned in anything published)"
  else
    ok "no em dash, en dash, horizontal bar, minus sign or double hyphen"
  fi

  # the word free, standalone, case insensitive
  if printf '%s' "$text" | grep -qiE '(^|[^[:alnum:]])free([^[:alnum:]]|$)'; then
    if [ "$allow_free" -eq 1 ]; then
      printf 'WARN  %s\n' 'the word "free" is present, allowed by --allow-free. Both hits said it; n = 2'
    else
      die 'the word "free" is present. Say the licence instead, or pass --allow-free if you decided to'
    fi
  else
    ok 'the word "free" is absent'
  fi

  # length sanity for a hook line
  local words
  words=$(printf '%s' "$text" | wc -w | tr -d ' ')
  ok "word count: $words"
}

lint_cta() {
  local kw="$1"
  local upper
  upper=$(printf '%s' "$kw" | tr '[:lower:]' '[:upper:]')

  if [ "$kw" != "$upper" ]; then
    die "CTA keyword must be uppercase: use $upper"
  else
    ok "CTA keyword is uppercase"
  fi

  if [ ! -f "$BURNED" ]; then
    die "burned keyword list not found at $BURNED. Copy reel-system/keywords_burned.template.txt there and seed it with every keyword ever used (or set REEL_BURNED_KEYWORDS)"
    return
  fi

  # Count real keyword lines only. grep -c . counted comment lines too, which
  # reported "11 keywords burned" for a file holding 7. A guard that misreports
  # its own coverage invites trust it has not earned.
  local n
  n=$(awk 'NF && $1 !~ /^#/ {c++} END {print c+0}' "$BURNED")

  if awk '$1 !~ /^#/ {print $1}' "$BURNED" | grep -qx "$upper"; then
    die "$upper is already burned in $BURNED. The automation routes on it. Pick another."
  else
    ok "$upper is not in the burned list ($n keywords burned so far)"
  fi
}

case "${1:-}" in
  --cta)
    [ $# -ge 2 ] || { echo "usage: lint.sh --cta KEYWORD" >&2; exit 2; }
    lint_cta "$2"
    ;;
  --file)
    [ $# -ge 2 ] || { echo "usage: lint.sh --file PATH" >&2; exit 2; }
    [ -f "$2" ] || { echo "no such file: $2" >&2; exit 2; }
    lint_text "$(cat "$2")"
    ;;
  "" )
    echo "usage: lint.sh \"text\" | lint.sh --cta KEYWORD | lint.sh --file PATH" >&2
    exit 2
    ;;
  *)
    lint_text "$*"
    ;;
esac

if [ "$fail" -ne 0 ]; then
  echo
  echo "Do not publish this. Fix the FAIL lines above."
  exit 1
fi
echo
echo "clean"
