#!/usr/bin/env python3
"""
Phone ↔ Claude bridge via ntfy

Listens for messages on arthur-cmd, sends to tmux, waits for completion,
sends response back to arthur.

Usage:
  ./phone-bridge.py --session tetra

Message format from phone:
  "do something"           -> sends to default session
  "@tetra do something"    -> sends to tetra session
  "@john do something"     -> sends to john session
"""

import argparse
import subprocess
import requests
import json
import re
import os

NTFY_SERVER = os.environ.get("NTFY_SERVER", "https://ntfy.dealglass.com")
NTFY_TOKEN = os.environ.get("NTFY_TOKEN", "tk_4ro4eehno2n9hcn2k74j17j9gzw3i")
CMD_TOPIC = "arthur"
RESPONSE_TOPIC = "arthur"

# Session name patterns - maps shorthand to actual tmux session
SESSION_MAP = {
    "tetra": "accumulator-tetra-sender",
    "john": "accumulator-john-receiver",
}


def get_headers():
    return {"Authorization": f"Bearer {NTFY_TOKEN}"}


def send_notification(topic, message):
    """Send a message to ntfy topic."""
    url = f"{NTFY_SERVER}/{topic}"
    resp = requests.post(url, data=message.encode('utf-8'), headers=get_headers())
    return resp.ok


def send_to_tmux(session, message):
    """Send message to tmux session."""
    # Strip to single line, remove problematic chars
    clean_msg = message.replace('\n', ' ').replace('\r', '').strip()[:500]

    TMUX = "/opt/homebrew/bin/tmux"

    # Use -l for literal to avoid escape interpretation
    r1 = subprocess.run([TMUX, "send-keys", "-t", session, "-l", clean_msg])
    print(f"   send-keys result: {r1.returncode}")

    import time
    time.sleep(0.3)

    r2 = subprocess.run([TMUX, "send-keys", "-t", session, "Enter"])
    print(f"   Enter result: {r2.returncode}")


def capture_tmux(session, lines=50):
    """Capture last N lines from tmux pane."""
    result = subprocess.run(
        ["tmux", "capture-pane", "-t", session, "-p", "-S", f"-{lines}"],
        capture_output=True, text=True
    )
    return result.stdout.strip()


def parse_message(msg):
    """Parse message for @session prefix."""
    match = re.match(r'^@(\w+)\s+(.+)$', msg, re.DOTALL)
    if match:
        return match.group(1), match.group(2)
    return None, msg


def listen_and_respond(default_session):
    """Main loop: listen for commands, execute, respond."""
    print(f"📱 Phone bridge started")
    print(f"   Listening on: {NTFY_SERVER}/{CMD_TOPIC}")
    print(f"   Responding to: {NTFY_SERVER}/{RESPONSE_TOPIC}")
    print(f"   Default session: {default_session}")
    print()

    url = f"{NTFY_SERVER}/{CMD_TOPIC}/json?poll=1"

    while True:
        try:
            # Long-poll for messages
            resp = requests.get(
                f"{NTFY_SERVER}/{CMD_TOPIC}/json",
                headers=get_headers(),
                stream=True,
                timeout=300
            )

            for line in resp.iter_lines():
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    if data.get("event") != "message":
                        continue

                    msg = data.get("message", "").strip()
                    if not msg:
                        continue

                    # Skip response messages and notification echoes
                    if msg.startswith("Done:") or msg.startswith("✓") or msg.startswith("Claude") or msg.startswith("⏳"):
                        continue

                    # Parse @session prefix
                    target, command = parse_message(msg)

                    if target and target in SESSION_MAP:
                        session = SESSION_MAP[target]
                    elif target:
                        session = target  # Use as-is if not in map
                    else:
                        session = default_session

                    print(f"📨 Received: {msg[:50]}...")
                    print(f"   → Sending to session: {session}")

                    # Send to tmux
                    send_to_tmux(session, command)

                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    print(f"Error processing message: {e}")
                    send_notification(RESPONSE_TOPIC, f"❌ Error: {e}")

        except requests.Timeout:
            continue  # Normal timeout, reconnect
        except requests.RequestException as e:
            print(f"Connection error: {e}, retrying...")
            import time
            time.sleep(5)


def main():
    parser = argparse.ArgumentParser(description="Phone ↔ Claude bridge")
    parser.add_argument("--session", "-s", default="accumulator-tetra-sender",
                        help="Default tmux session")
    args = parser.parse_args()

    # Resolve session name
    session = SESSION_MAP.get(args.session, args.session)

    listen_and_respond(session)


if __name__ == "__main__":
    main()
