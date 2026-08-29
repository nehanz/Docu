# Docu

Docu is a Python tool that logs terminal commands and outputs, lets you add comments, and can mask sensitive data with `docu mask`. Its AI assistant can summarize sessions, explain commands, and help debug, while saving everything in organized, custom directories for easy access.

## Features

- Logs commands and outputs automatically
- Add comments or notes to sessions
- Mask sensitive outputs when needed (`docu mask`)
- AI assistant for summaries, explanations, and debugging (supports Gemini, OpenAI GPT, and Anthropic Claude)
- Saves sessions in organized, custom directories

---

## Installation

### From PyPI (recommended)

```bash
pip install docu
```

### From source

```bash
git clone https://github.com/NehanZ/Docu.git
cd Docu
pip install -e .
```

### Run directly

```bash
python -m docu start --name my_session
```

---

## Quick Start

1. **Start a session:**

```bash
docu start --name session_name
```

2. **Use the terminal normally** — all commands and outputs are logged.

3. **Type `exit`** to stop logging and save your session.

---

## Commands

| Command | Description |
|---------|-------------|
| `docu start -n <name>` | Start a new logging session |
| `docu --comment "note"` | Add a comment to the current session |
| `docu askai` | Ask the AI assistant a question |
| `docu config` | Configure AI settings (first-time setup) |
| `docu mask` | Toggle output masking (use inside a session) |

---

## AI Setup

On first run of `docu askai`, you'll be guided through interactive setup:

1. Choose a provider (Gemini, OpenAI, or Anthropic)
2. Enter your API URL (defaults provided)
3. Enter your API key (hidden input)

Your config is saved to `~/.docu/config.toml` (mode 600).

If you skip setup, you'll be prompted again when using `docu askai`.

---

## Configuration

### Config file location

```
~/.docu/config.toml
```

### Manual config example

```toml
[ai]
provider = "openai"
api_url = "https://api.openai.com/v1/chat/completions"
api_key = "sk-..."
```

### Supported providers

| Provider | Default API URL |
|----------|-----------------|
| Gemini | `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent` |
| OpenAI | `https://api.openai.com/v1/chat/completions` |
| Anthropic | `https://api.anthropic.com/v1/messages` |

---

## Session Logs

By default, sessions are saved to `~/Documents/docu/<session_name>/`:

- `commands.txt` — numbered commands only
- `all.txt` — commands + full output

Custom save location:

```bash
docu start -n my_session -s /path/to/save/dir
```

---

## Notes

- Run `docu askai` outside a session to get AI help on any topic
- Run `docu askai` inside a session to include session logs in context
- All logs use best practices for terminal-friendly formatting