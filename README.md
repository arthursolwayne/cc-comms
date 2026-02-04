# cc-comms

Synchronous Claude-to-Claude messaging via tmux + ntfy.sh.

## Setup (5 minutes)

### Step 1: Generate a unique channel

```bash
CHANNEL="cc-$(openssl rand -hex 4)"
echo $CHANNEL  # e.g., cc-7f3a2b1c
```

Save this - both sender and receiver need the same channel.

### Step 2: Configure the RECEIVER

On the machine where the **receiving** Claude will run:

**Option A: Use setup script (recommended)**
```bash
git clone https://github.com/arthursolwayne/cc-comms.git
./cc-comms/setup-receiver.sh YOUR-CHANNEL
```

**Option B: Manual setup**

Add to `~/.claude/settings.json`:
```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "curl -s -d done ntfy.sh/YOUR-CHANNEL-HERE"
          }
        ]
      }
    ]
  }
}
```

**B. Start a tmux session and launch Claude:**

```bash
tmux new-session -d -s receiver
tmux send-keys -t receiver 'claude' Enter
```

### Step 3: Clone this repo on SENDER

```bash
git clone https://github.com/arthursolwayne/cc-comms.git
cd cc-comms
pip install requests  # if not already installed
```

### Step 4: Send messages

**Same machine (local):**
```bash
./send.py --local --session receiver --channel cc-7f3a2b1c "your message"
```

**Different machine (via SSH):**
```bash
./send.py --host user@remote --session receiver --channel cc-7f3a2b1c "your message"
```

## Critical: Channel Ownership

**The channel belongs to the RECEIVER, not the sender.**

The `--channel` argument in send.py specifies which ntfy channel to *listen on* for the receiver's "done" signal. This must match the channel configured in the *receiver's* Stop hook.

Common mistake: Using your own machine's channel when talking to a remote receiver. Your channel is for others to talk TO you, not for you to talk to others.

## Local vs Remote

| Mode | Sender | Receiver | Setup Required |
|------|--------|----------|----------------|
| **Local-to-local** | Machine A | Machine A | Both share same `~/.claude/settings.json` - one channel works |
| **Local-to-remote** | Machine A | Machine B | Receiver's settings.json must have Stop hook configured - verify via SSH first |

**Before sending to a remote receiver, always verify:**
```bash
# 1. Check receiver has cc-comms configured
ssh user@remote "grep ntfy ~/.claude/settings.json"

# 2. If not configured, set it up first
ssh user@remote "/path/to/setup-receiver.sh cc-NEWCHANNEL"
ssh user@remote "tmux send-keys -t SESSION C-c"  # restart Claude to apply
ssh user@remote "tmux send-keys -t SESSION 'claude' Enter"
```

## How It Works

```
┌─────────────┐      tmux send-keys      ┌─────────────┐
│   Sender    │ ──────────────────────▶  │  Receiver   │
│  (Claude)   │      (SSH or local)      │  (Claude)   │
└─────────────┘                          └─────────────┘
       │                                        │
       │                                        │ Stop hook fires
       │                                        ▼
       │              ntfy.sh/<channel>
       │◀────────────────────────────────────────
       │              "done" notification
       ▼
  tmux capture-pane (get response)
```

1. Sender sends message to receiver's tmux session
2. Receiver Claude processes and responds
3. When receiver finishes, Stop hook fires → sends "done" to ntfy
4. Sender receives notification → captures tmux pane → prints response

## Usage

```
./send.py [OPTIONS] "message"

Required:
  --session, -s    tmux session name on receiver
  --channel, -c    ntfy.sh channel (must match receiver's hook)

Choose one:
  --local, -l      Same machine (no SSH)
  --host, -H       SSH host for remote (user@host)
```

## Examples

### Two Claudes on same machine

```bash
# Terminal 1: Start receiver
tmux new-session -s agent1
claude

# Terminal 2: Send from sender
./send.py -l -s agent1 -c cc-abc123 "What's the status?"
```

### Two Claudes on different machines

```bash
# On remote (receiver):
tmux new-session -d -s worker
tmux send-keys -t worker 'claude' Enter

# On local (sender):
./send.py -H user@remote -s worker -c cc-abc123 "Run the tests"
```

## Verification

Test that ntfy is working:

```bash
# On receiver machine, manually trigger:
curl -s -d 'test' ntfy.sh/YOUR-CHANNEL

# On sender machine, verify receipt:
curl -s "ntfy.sh/YOUR-CHANNEL/raw?poll=1"
# Should print: test
```

## Troubleshooting

**Sender hangs forever:**
- Receiver's Stop hook not configured or wrong channel
- Check `~/.claude/settings.json` on receiver (NOT settings.local.json)
- Verify channel names match exactly
- Restart Claude after adding the hook

**Using wrong channel (remote receivers):**
- You used YOUR machine's channel instead of the RECEIVER's channel
- Your channel (in your settings.json) is for others to send TO you
- To send to a remote receiver, use THEIR channel: `ssh user@remote "grep ntfy ~/.claude/settings.json"`
- If they don't have one, set it up first with `setup-receiver.sh`

**Message not received by Claude:**
- Wrong tmux session name
- Claude not running in that session
- Check with: `tmux capture-pane -t SESSION -p`

**SSH errors:**
- Verify SSH access: `ssh user@host 'echo ok'`
- Check tmux session exists: `ssh user@host 'tmux list-sessions'`

**Permission denied on send.py:**
- Run: `chmod +x send.py`

## Pre-flight Checklist (Remote)

Before your first send to a remote receiver:

```bash
# 1. Verify SSH works
ssh user@remote "echo ok"

# 2. Check tmux session exists
ssh user@remote "tmux list-sessions"

# 3. Check if cc-comms is configured (look for ntfy in output)
ssh user@remote "cat ~/.claude/settings.json"

# 4. If no ntfy hook, configure it:
ssh user@remote "git clone https://github.com/arthursolwayne/cc-comms.git /tmp/cc-comms 2>/dev/null; /tmp/cc-comms/setup-receiver.sh cc-YOURCHANNEL"

# 5. Restart Claude to apply hook
ssh user@remote "tmux send-keys -t SESSION C-c; sleep 2; tmux send-keys -t SESSION 'claude' Enter"

# 6. Now send
./send.py -H user@remote -s SESSION -c cc-YOURCHANNEL "your message"
```

## Multiple Pairs

Each sender/receiver pair needs a unique channel:

| Pair | Channel | Receiver Session |
|------|---------|------------------|
| A → B | `cc-pair-ab` | `agent-b` |
| A → C | `cc-pair-ac` | `agent-c` |
| B → C | `cc-pair-bc` | `agent-c` |

## Dependencies

- Python 3 + `requests` (`pip install requests`)
- tmux
- curl (on receiver)
- SSH (for cross-machine only)
