#!/bin/bash
# Exercises tools/brain.py against tests/fake_brain_server.py (same rules as server/Code.gs).
# Two fake exec members race for the same contact; exactly one may win.
cd "$(dirname "$0")/.."
PORT=$((20000 + RANDOM % 20000)); KEY=test-key
python3 tests/fake_brain_server.py $PORT $KEY & SRV=$!
trap 'kill $SRV 2>/dev/null' EXIT
sleep 0.5
export NOBE_BRAIN_URL=http://127.0.0.1:$PORT NOBE_BRAIN_KEY=$KEY
B="python3 tools/brain.py"; fails=0
expect() { if [ "$2" = "$3" ]; then echo "ok    $1"; else echo "WRONG $1 (exit $3, wanted $2)"; fails=$((fails+1)); fi; }

$B claim --email Jane@Acme.com --name "Jane Doe" --company "Acme Robotics Inc" --committee tech >/dev/null; expect "claim new contact" 0 $?
$B claim --email jane@acme.com --name "Jane Doe" --company "Acme" --committee pd >/dev/null; expect "same person blocked" 3 $?
out=$($B claim --email ceo@acme.com --name "Sam Roe" --company "ACME Robotics, LLC" --committee consulting); expect "same company, new person allowed" 0 $?
echo "$out" | grep -q "WARN: 1 other" ; expect "same company warns" 0 $?
$B claim --email race@x.com --name R --company X --committee pd >/dev/null & P1=$!
$B claim --email race@x.com --name R --company X --committee pd >/dev/null & P2=$!
wait $P1; r1=$?; wait $P2; r2=$?
[ $((r1 + r2)) -eq 3 ]; expect "simultaneous race: one wins, one blocked ($r1/$r2)" 0 $?
$B set jane@acme.com sent >/dev/null; expect "set sent" 0 $?
$B set jane@acme.com released >/dev/null; expect "cannot release after sent" 1 $?
$B set race@x.com released >/dev/null && $B claim --email race@x.com --name R --company X --committee tech >/dev/null; expect "released contact can be reclaimed" 0 $?
NOBE_BRAIN_KEY=wrong $B check new@y.com >/dev/null; expect "wrong key blocks" 3 $?
NOBE_BRAIN_URL=http://127.0.0.1:1 $B check new@y.com >/dev/null; expect "server down blocks" 3 $?
$B sync >/dev/null && [ "$(ls brain/vault/Companies | wc -l | tr -d ' ')" = 2 ]; expect "vault merges company spellings" 0 $?
rm -rf brain/vault
echo "---"; [ $fails -eq 0 ] && echo "brain: all passed" || echo "brain: $fails wrong"
[ $fails -eq 0 ]
