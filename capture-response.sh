#!/bin/bash
# Capture Claude response after last user message

/opt/homebrew/bin/tmux capture-pane -p -S -80 2>/dev/null | \
awk '
  /^❯ ./ {
    # User message with text - reset, wait for first ⏺
    buf = ""
    started = 0
    next
  }
  /^⏺ / {
    started = 1
    line = $0
    sub(/^⏺ /, "", line)
    if (buf != "") buf = buf "\n\n"
    buf = buf line
    next
  }
  started && /^  [A-Za-z]/ && !/^  ⎿/ {
    line = $0
    sub(/^  /, "", line)
    buf = buf " " line
  }
  END { print buf }
' | head -c 1000
