#!/usr/bin/env bash

input=$(cat)
source_name="${PROMPT_LOG_SOURCE:-claude}"
event_name=$(printf '%s' "$input" | jq -r '.hook_event_name // ""')

# Extract content based on hook event.
role="user"
case "$event_name" in
    Stop)
        role="assistant"
        content=$(printf '%s' "$input" | jq -r '.last_assistant_message // ""' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        ;;
    *)
        content=$(printf '%s' "$input" | jq -r '.prompt // ""' | perl -0777 -pe 's/<[a-z_]+>.*?<\/[a-z_]+>\n?//gs' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        ;;
esac

if [ -z "$content" ]; then
    exit 0
fi

# Git info
git_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
git_user_name=$(git config --get user.name 2>/dev/null || echo "unknown")

# Sanitize username for filename: lowercase, replace non-alphanumeric with hyphens, collapse consecutive hyphens
username_slug=$(printf '%s' "$git_user_name" \
    | python3 -c "
import sys, unicodedata, re
text = sys.stdin.read()
nfkd = unicodedata.normalize('NFKD', text)
ascii_text = nfkd.encode('ascii', 'ignore').decode('ascii')
slug = re.sub(r'[^a-z0-9]+', '-', ascii_text.lower()).strip('-')
print(slug)
")

# Date for filename (YYYY-MM-DD)
log_date=$(date -u +"%Y-%m-%d")

# Timestamp (ISO 8601 with milliseconds via python3 for macOS compatibility)
timestamp=$(python3 -c "from datetime import datetime, timezone; print(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.') + f'{datetime.now(timezone.utc).microsecond // 1000:03d}Z')")

# Call context (all fields except prompt and session_id)
call_context=$(printf '%s' "$input" | jq 'del(.prompt, .session_id)')

# Build entry
entry=$(jq -n \
    --arg timestamp "$timestamp" \
    --arg source "$source_name" \
    --arg git_branch "$git_branch" \
    --arg git_user_name "$git_user_name" \
    --argjson call_context "$call_context" \
    --arg role "$role" \
    --arg content "$content" \
    '{timestamp: $timestamp, source: $source, git_branch: $git_branch, git_user_name: $git_user_name, call_context: $call_context, role: $role, content: $content}')

# Determine log file path (.ai_log/ next to the repo root)
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
log_dir="$repo_root/.ai_log"
mkdir -p "$log_dir"
log_path="$log_dir/prompt_log_${log_date}_${username_slug}.json"

# Append to log file (append-only)
if [ -f "$log_path" ]; then
    updated=$(jq ". + [$entry]" "$log_path")
    printf '%s\n' "$updated" > "$log_path"
else
    printf '[%s]\n' "$entry" > "$log_path"
fi