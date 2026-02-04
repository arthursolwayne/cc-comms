#!/bin/bash
# Capture full Claude response after last user message
# Captures both ⏺ lines and indented continuation text

/opt/homebrew/bin/tmux capture-pane -p -S -80 2>/dev/null | \
awk '
  /^❯ ./ {
    # User message - reset buffer
    response = ""
    in_response = 0
    next
  }
  /^⏺ [A-Za-z]/ && !/^⏺ (Bash|Write|Read|Edit|Update|Glob|Grep|Task|Ran|WebFetch|WebSearch)/ {
    # Response line (not a tool call) - start new block
    in_response = 1
    line = $0
    sub(/^⏺ /, "", line)
    if (response != "") response = response "\n\n"
    response = response line " "
    next
  }
  /^⏺ (Bash|Write|Read|Edit|Update|Glob|Grep|Task|Ran|WebFetch|WebSearch)/ || /^  ⎿/ {
    # Tool call or output - stop capturing continuation
    in_response = 0
    next
  }
  in_response && /^  [A-Za-z]/ {
    # Indented continuation text
    line = $0
    sub(/^  /, "", line)
    response = response line " "
  }
  END { print response }
' | \
sed 's/  */ /g' | \
head -c 800
