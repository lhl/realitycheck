#!/usr/bin/env bash
# judge.sh PACKETS_DIR JUDGE(astra|opus) — grade every packet, write <letter>.<judge>.json
P="$1"; J="$2"
cd "$P" || exit 1
for f in [A-Z].md; do
  L="${f%.md}"; outf="$L.$J.json"
  [[ -s "$outf" ]] && continue
  case "$J" in
    astra) timeout 900 jouzu pi -p --no-session --no-tools --model office-pool/gpt-6.2-astra --thinking high "$(cat "$f")" > "$outf" 2>&1 ;;
    opus)  timeout 900 env -u ANTHROPIC_API_KEY claude -p --model claude-opus-5-5 --tools "" < "$f" > "$outf" 2>&1 ;;
  esac &
done
wait
