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

**A. Create/edit `~/.claude/settings.local.json`:**

```json
{
  "hooks": {
    "Stop": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "curl -s -d 'done' ntfy.sh/YOUR-CHANNEL-HERE"
      }]
    }]
  }
}
```

Replace `YOUR-CHANNEL-HERE` with your channel from Step 1.

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
- Check `~/.claude/settings.local.json` on receiver
- Verify channel names match exactly

**Message not received by Claude:**
- Wrong tmux session name
- Claude not running in that session
- Check with: `tmux capture-pane -t SESSION -p`

**SSH errors:**
- Verify SSH access: `ssh user@host 'echo ok'`
- Check tmux session exists: `ssh user@host 'tmux list-sessions'`

**Permission denied on send.py:**
- Run: `chmod +x send.py`

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
