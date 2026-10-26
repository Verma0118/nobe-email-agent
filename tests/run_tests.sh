#!/bin/bash
# Runs lint_draft.py on every fixture. Name: <pass|fail>__<committee>__<what>.txt
# Uses tests/profile.test.json (fictional sender) so results never depend on a real profile.
cd "$(dirname "$0")"
rm -f fixtures/*.txt; python3 make_fixtures.py >/dev/null
ok=0; bad=0
for f in fixtures/*.txt; do
  b=$(basename "$f" .txt); expect=${b%%__*}; rest=${b#*__}; com=${rest%%__*}
  out=$(python3 ../tools/lint_draft.py "$f" --committee "$com" --profile profile.test.json); rc=$?
  if { [ "$expect" = pass ] && [ $rc -eq 0 ]; } || { [ "$expect" = fail ] && [ $rc -eq 1 ]; }; then
    ok=$((ok+1)); why=$(echo "$out" | grep -m1 FAIL | sed "s/^FAIL  //"); echo "ok    $b${why:+   <- $why}"
  else
    bad=$((bad+1)); echo "WRONG $b (expected $expect, exit $rc)"; echo "$out" | sed 's/^/      /'
  fi
done
echo "---"; echo "$ok passed, $bad wrong"
./brain_test.sh || bad=$((bad+1))
[ $bad -eq 0 ]
