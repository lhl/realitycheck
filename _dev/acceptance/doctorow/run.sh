#!/usr/bin/env bash
# run-one.sh OUT MODELKEY
OUT="$1"; KEY="$2"
cd "$OUT/project" || exit 1
export PATH="$OUT/bin:$PATH" REALITYCHECK_DATA="$OUT/project/data/realitycheck.lance" REALITYCHECK_EMBED_SKIP=1
PROMPT="$(cat "$OUT/TASK.md")"
start=$(date +%s)
case "$KEY" in
  dsv41) timeout 3600 jouzu pi -p --no-session --model deepseek-v4.1-flash-1017 --thinking high "$PROMPT" ;;
  sol)   timeout 3600 jouzu pi -p --no-session --model office-pool/gpt-6.2-sol --thinking high "$PROMPT" ;;
  astra) timeout 3600 jouzu pi -p --no-session --model office-pool/gpt-6.2-astra --thinking high "$PROMPT" ;;
  opus)  printf '%s' "$PROMPT" | timeout 3600 env -u ANTHROPIC_API_KEY claude -p --model claude-opus-5-5 \
           --permission-mode acceptEdits --allowedTools=Bash,Read,Write,Edit,Glob,Grep \
           --disallowedTools=WebFetch,WebSearch ;;
esac > "$OUT/transcript.txt" 2>&1
echo "exit=$? seconds=$(( $(date +%s) - start ))" > "$OUT/run-status.txt"
