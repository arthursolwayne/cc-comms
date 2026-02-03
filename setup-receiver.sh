#!/bin/bash
# Setup receiver's Stop hook for cc-comms
# Usage: ./setup-receiver.sh CHANNEL

set -e

CHANNEL="$1"
SETTINGS="$HOME/.claude/settings.json"

if [ -z "$CHANNEL" ]; then
    echo "Usage: ./setup-receiver.sh CHANNEL"
    echo "Example: ./setup-receiver.sh cc-7f3a2b1c"
    exit 1
fi

# Create .claude dir if needed
mkdir -p "$HOME/.claude"

# Create or patch settings.json
if [ -f "$SETTINGS" ]; then
    # Check if hooks.Stop already exists
    if grep -q '"Stop"' "$SETTINGS" 2>/dev/null; then
        echo "Stop hook already exists in $SETTINGS"
        echo "Manually update the channel if needed."
        exit 1
    fi
    # Add hooks to existing file using python for safe JSON manipulation
    python3 -c "
import json
with open('$SETTINGS', 'r') as f:
    data = json.load(f)
data.setdefault('hooks', {})['Stop'] = [{'matcher': '', 'hooks': [{'type': 'command', 'command': 'curl -s -d done ntfy.sh/$CHANNEL'}]}]
with open('$SETTINGS', 'w') as f:
    json.dump(data, f, indent=2)
"
else
    # Create new settings.json
    cat > "$SETTINGS" << EOF
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "curl -s -d done ntfy.sh/$CHANNEL"
          }
        ]
      }
    ]
  }
}
EOF
fi

echo "Stop hook configured for channel: $CHANNEL"
echo "Restart Claude to apply."
