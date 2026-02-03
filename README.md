# Claude-to-Claude Communication

Synchronous messaging between Claude Code instances using tmux + ntfy.sh.

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

## Quick Start

### 1. Generate a unique channel name

```bash
echo "myteam-$(openssl rand -hex 4)"
# e.g., myteam-7f3a2b1c
```

### 2. Configure receiver's Stop hook

On the **receiving** Claude instance, add to `~/.claude/settings.local.json`:

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

### 3. Start receiver's tmux session

```bash
tmux new-session -d -s worker
tmux send-keys -t worker 'claude' Enter
```

### 4. Send messages

**Same machine (two tmuxes):**
```bash
./send.py --local --session worker --channel myteam-7f3a2b1c "your message"
```

**Cross machine (via SSH):**
```bash
./send.py --host user@remote --session worker --channel myteam-7f3a2b1c "your message"
```

## Usage

```
./send.py [OPTIONS] "message"

Options:
  --host, -H     SSH host (user@host) for remote mode
  --session, -s  tmux session name (required)
  --channel, -c  ntfy.sh channel (required)
  --local, -l    Local mode (same machine, no SSH)
```

## Examples

### Local: Two Claude instances on same machine

```bash
# Terminal 1: Start receiver
tmux new-session -s agent1
claude  # receiver runs here

# Terminal 2: Send from another session
./send.py -l -s agent1 -c team-abc123 "What files have you modified?"
```

### Remote: Cross-machine communication

```bash
# On remote machine: Start receiver
tmux new-session -d -s worker
tmux send-keys -t worker 'claude' Enter

# On local machine: Send message
./send.py -H user@remote -s worker -c team-abc123 "Run the tests"
```

## Gotchas

1. **Unique channels** - Each sender/receiver pair needs its own ntfy channel
2. **Stop hook required** - Receiver must have the hook configured or sender blocks forever
3. **Escape quotes** - Avoid nested quotes in messages; they get mangled by shell escaping
4. **Timeout** - Sender waits up to 5 minutes for response

## Creating Multiple Pairs

For teams with multiple Claude pairs:

| Pair | Channel | Session |
|------|---------|---------|
| A ↔ B | `team-pair-ab` | `agent-b` |
| A ↔ C | `team-pair-ac` | `agent-c` |
| B ↔ C | `team-pair-bc` | `agent-c` |

Each receiver configures their Stop hook with their incoming channel(s).

## Dependencies

- Python 3
- `requests` library (`pip install requests`)
- tmux
- SSH (for cross-machine only)
- curl (on receiver, for Stop hook)
