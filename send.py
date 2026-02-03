#!/usr/bin/env python3
"""
Claude-to-Claude communication via tmux + ntfy.sh

Usage:
  # Cross-machine (via SSH)
  ./send.py --host user@remote --session worker --channel myteam-abc "message"

  # Same-machine (local tmux)
  ./send.py --local --session worker --channel myteam-abc "message"

Receiver needs Stop hook configured - see README.md
"""

import argparse
import shlex
import subprocess
import sys
import time
import requests


def ssh(host, cmd):
    """Run command on remote host via SSH."""
    subprocess.run(["ssh", host, cmd], capture_output=True)


def local_tmux(args):
    """Run tmux command locally."""
    subprocess.run(["tmux"] + args, capture_output=True)


def send_and_wait(message, host, session, channel, local=False):
    # Get timestamp before sending
    ts = int(time.time())

    if local:
        # Same-machine: direct tmux commands
        local_tmux(["send-keys", "-t", session, message])
        local_tmux(["send-keys", "-t", session, "Enter"])
    else:
        # Cross-machine: via SSH
        if not host:
            print("Error: --host required for remote mode", file=sys.stderr)
            sys.exit(1)
        quoted_msg = shlex.quote(message)
        ssh(host, f"tmux send-keys -t {session} {quoted_msg}")
        ssh(host, f"tmux send-keys -t {session} Enter")

    # Block on ntfy until response
    url = f"https://ntfy.sh/{channel}/raw?since={ts}"
    try:
        resp = requests.get(url, stream=True, timeout=300)
        for line in resp.iter_lines():
            if line:
                break  # got notification, receiver is done
    except requests.Timeout:
        print("Timeout waiting for response", file=sys.stderr)
        sys.exit(1)

    # Capture and print response
    if local:
        result = subprocess.run(
            ["tmux", "capture-pane", "-t", session, "-p"],
            capture_output=True, text=True
        )
    else:
        result = subprocess.run(
            ["ssh", host, f"tmux capture-pane -t {session} -p"],
            capture_output=True, text=True
        )

    # Print last 3000 chars to avoid flooding
    output = result.stdout
    print(output[-3000:] if len(output) > 3000 else output)


def main():
    parser = argparse.ArgumentParser(description="Claude-to-Claude messaging")
    parser.add_argument("message", nargs="?", default="ping", help="Message to send")
    parser.add_argument("--host", "-H", help="SSH host (user@host) for remote mode")
    parser.add_argument("--session", "-s", required=True, help="tmux session name")
    parser.add_argument("--channel", "-c", required=True, help="ntfy.sh channel")
    parser.add_argument("--local", "-l", action="store_true", help="Local mode (same machine)")

    args = parser.parse_args()

    send_and_wait(
        message=args.message,
        host=args.host,
        session=args.session,
        channel=args.channel,
        local=args.local
    )


if __name__ == "__main__":
    main()
