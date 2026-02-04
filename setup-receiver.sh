#!/bin/bash
# Setup receiver's Stop hook for cc-comms
# Usage: ./setup-receiver.sh CHANNEL [SERVER]

set -e

CHANNEL="$1"
SERVER="${2:-https://ntfy.dealglass.com}"
TOKEN="${3:-tk_4ro4eehno2n9hcn2k74j17j9gzw3i}"
SETTINGS="$HOME/.claude/settings.json"

if [ -z "$CHANNEL" ]; then
    echo "Usage: ./setup-receiver.sh CHANNEL [SERVER] [TOKEN]"
    echo "Example: ./setup-receiver.sh cc-7f3a2b1c"
    echo "Example: ./setup-receiver.sh cc-7f3a2b1c https://ntfy.dealglass.com tk_xxx"
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
data.setdefault('hooks', {})['Stop'] = [{'matcher': '', 'hooks': [{'type': 'command', 'command': 'curl -s -H \"Authorization: Bearer $TOKEN\" -d done $SERVER/$CHANNEL'}]}]
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
            "command": "curl -s -H \"Authorization: Bearer $TOKEN\" -d done $SERVER/$CHANNEL"
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
