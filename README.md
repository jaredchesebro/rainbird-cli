# rainbird-cli

Command-line interface for the Rain Bird ESP-Me irrigation controller.

## Requirements

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

## Installation

```bash
git clone git@github.com:jaredchesebro/rainbird-cli.git
cd rainbird-cli
python3.13 -m venv .venv
uv pip install -e . --python .venv/bin/python
```

Add to your PATH:

```bash
# ~/.local/bin/rainbird
#!/usr/bin/env zsh
exec /path/to/rainbird-cli/.venv/bin/rainbird "$@"
```

## Configuration

Create a `.env` file in the project root:

```
RAINBIRD_HOST=<controller-ip>
RAINBIRD_PASSWORD=<controller-password>
```

Credentials can also be passed per-command:

```bash
rainbird --host 192.168.1.100 --password secret status
```

## Usage

### Control

```bash
rainbird run <zone> <minutes>   # Water a zone
rainbird stop                   # Stop all irrigation
rainbird test <zone>            # Quick test burst
rainbird program <A|B|C|D>      # Run a preset program
rainbird advance                # Advance to next zone in active program
```

### Status

```bash
rainbird status    # Full dashboard
rainbird zones     # Zone states
rainbird sensor    # Rain sensor state
rainbird delay     # Current rain delay
rainbird delay 3   # Set rain delay (days); 0 clears it
```

### Info

```bash
rainbird info      # Hardware model, firmware, serial number
rainbird wifi      # Wi-Fi details
rainbird network   # Network connectivity
rainbird schedule  # All configured programs
```

### Global flags

```bash
--host <ip>       # Override RAINBIRD_HOST
--password <pw>   # Override RAINBIRD_PASSWORD
--debug           # Show full tracebacks on errors
```

## Device Notes

- Supported zones: 1–4
- Programs: A, B, C, D
- Controller is single-connection — close the Rain Bird mobile app if you get busy errors
