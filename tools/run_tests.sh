#!/usr/bin/env bash
# One command: rebuild assets (with budget/geometry/audio asserts), import, compile-check, self-tests,
# good+bad bots on every level, screenshot tour. Prints a pass/fail table. Usage: tools/run_tests.sh [--no-shots]
cd "$(dirname "$0")/.." || exit 1
GODOT=${GODOT:-godot}
declare -a ROWS; FAIL=0
row() { ROWS+=("$(printf '%-26s %-5s %s' "$1" "$2" "$3")"); [ "$2" = PASS ] || FAIL=1; }

out=$(python3 tools/build_all.py 2>&1); echo "$out" | grep -q "BUILD OK" && row build PASS "budgets, gap sizes, rail curvature, audio peak/seam" || row build FAIL "$(echo "$out" | tail -3 | tr '\n' ' ')"
$GODOT --headless --path . --import >/dev/null 2>&1 && row import PASS "" || row import FAIL ""
out=$($GODOT --headless --path . -- --check 2>&1 | grep CHECK); [[ $out == *"failed=0"* ]] && row scripts PASS "$out" || row scripts FAIL "$out"
out=$($GODOT --headless --path . -- --test 2>&1 | grep "TEST"); [[ $out == *PASS* ]] && row "input+save fuzz" PASS "" || row "input+save fuzz" FAIL "$out"
for f in levels/level_*.json; do
  n=$(basename "$f" .json | cut -d_ -f2)
  for b in good bad; do
    out=$(timeout 600 $GODOT --headless --path . --fixed-fps 60 -- --level=$n --bot=$b --speed=1.0 2>&1)
    res=$(echo "$out" | grep BOT_RESULT | cut -d' ' -f2-)
    errs=$(echo "$out" | grep -c "SCRIPT ERROR")
    [[ $res == *'"ok":true'* && $errs == 0 ]] && row "level $n bot:$b" PASS "$res" || row "level $n bot:$b" FAIL "errors=$errs $res"
    echo "$res" > "docs/bot_level${n}_${b}.json"
  done
  if [ "$1" != "--no-shots" ]; then
    timeout 300 $GODOT --path . -- --level=$n --shots 2>&1 | grep -q SHOTS && row "level $n screenshots" PASS "docs/shots/level_${n}_*.png" || row "level $n screenshots" FAIL "(needs a display)"
  fi
done
echo; echo "== rail-shooter tests =="; printf '%s\n' "${ROWS[@]}"; echo
[ $FAIL = 0 ] && echo "ALL PASS" || echo "SOME FAILED"; exit $FAIL
