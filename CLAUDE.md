# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment

- Python 3.13 via Homebrew (`/opt/homebrew/bin/python3.13`)
- Venv at `.venv/` — always use `.venv/bin/python` or activate first
- Credentials in `.env`: `RAINBIRD_HOST=<host>`, `RAINBIRD_PASSWORD=<password>`
- Optional: `RAINBIRD_RAIN_SENSOR=true` — enables rain sensor API calls and output (default: disabled; device can't detect sensor presence)

## Running the CLI

```bash
# Via global wrapper (no activate needed):
rainbird <command>

# Or directly from venv:
.venv/bin/rainbird <command>
```

## Installing

```bash
# Initial install (creates .venv/bin/rainbird entry point):
/opt/homebrew/bin/uv pip install -e . --python .venv/bin/python

# Add a new dependency:
/opt/homebrew/bin/uv pip install <package> --python .venv/bin/python
# Then add it to pyproject.toml [project.dependencies]
```

## Global wrappers

`~/.local/bin/rainbird` delegates to `.venv/bin/rainbird` — the installed entry point from `pyproject.toml`.
`~/.local/bin/rainbird-mcp` delegates to `.venv/bin/rainbird-mcp` — used by Claude Desktop config.

## Architecture

```
rainbird.py              — entry point: imports command modules, exposes main() for pyproject.toml script entry
rainbird_mcp.py          — MCP server entry point: FastMCP tools and resources
core.py                  — app instance, _ctx, consoles, run_async, handle_errors, get_controller
lib.py                   — shared async pyrainbird functions (used by CLI commands and MCP server)
formatting.py            — format_frequency, format_duration, DAY_ABBREV/DAY_ORDER constants
commands/
  control.py             — run, stop, test, program, advance
  status.py              — status, zones, sensor, delay
  info.py                — info, wifi, network
  schedule.py            — schedule
```

Stack: **typer** (CLI), **rich** (output), **pyrainbird** (device), **python-dotenv** (config).

### Key patterns

**Command registration** — `app` defined in `core.py`. Each `commands/*.py` imports `app` from `core` and uses `@app.command()`. `rainbird.py` imports all command modules (triggering registration), then calls `app()`.

**Async bridge** — typer commands are sync; each defines an inner `async def _run()` and calls `run_async(_run())` → `asyncio.run()`.

**Config** — `--host`/`--password` resolved via typer `@app.callback()` in `core.py` from env vars or CLI flags, stashed in module-level `_ctx` dict. All command modules read from `_ctx` via `get_controller()`.

**Error handling** — `async with handle_errors():` in `core.py` wraps all controller calls, mapping pyrainbird exceptions to clean user-facing messages. `--debug` re-raises for full tracebacks.

**Controller init** — each command opens a fresh `aiohttp.ClientSession`, calls `async_client.create_controller(session, host, password)`, makes API calls, then closes — all within the same `async with` block.

### pyrainbird notes

- Device: Rain Bird ESP-Me (model `0x0007`, protocol 2.9)
- `get_combined_controller_state()` returns NACK on this device — not supported; `status` uses individual calls instead
- `get_serial_number()` returns `int`, not `str` — cast with `str()`
- Controller is single-connection; returns 503 busy if Rain Bird cloud app holds the connection
- Key methods: `irrigate_zone(zone, minutes)`, `stop_irrigation()`, `get_zone_states()`, `get_available_stations()`, `get_schedule()`, `get_current_irrigation()`, `get_rain_sensor_state()`, `get_rain_delay()`, `set_rain_delay(days)`
- Available stations on this device: zones 1–4

## MCP Server

`rainbird_mcp.py` exposes the controller as a FastMCP server over stdio for Claude Desktop/Code.

### Running

```bash
# Via global wrapper:
rainbird-mcp

# Or directly:
.venv/bin/rainbird-mcp
```

### Config

Same env vars as CLI: `RAINBIRD_HOST`, `RAINBIRD_PASSWORD`, `RAINBIRD_RAIN_SENSOR`.
Additional: `RAINBIRD_DEBUG=true` — include full traceback in tool errors.

### Claude Desktop config

`~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "rainbird": {
      "command": "~/.local/bin/rainbird-mcp",
      "env": {
        "RAINBIRD_HOST": "<host>",
        "RAINBIRD_PASSWORD": "<password>"
      }
    }
  }
}
```

### Tools

**Action tools** (execute immediately):

| Tool | Args | Notes |
|---|---|---|
| `irrigate_zone` | `zone: int`, `minutes: int` | Start zone immediately |
| `stop_irrigation` | — | Stop all irrigation |
| `test_zone` | `zone: int` | Quick zone test |
| `advance_zone` | — | Advance to next zone in active program |
| `set_rain_delay` | `days: int` | 0 clears delay |
| `start_program` | `letter: str` (A/B/C/D) | Claude must fetch `rainbird://schedule` and confirm with user before calling |

Action tools return `{"success": True, "message": "..."}` or `{"success": False, "error": "..."}`.

**Read-only tools** (return data dicts):

| Tool | Description |
|---|---|
| `get_status` | Irrigation state, rain delay, device time, configured zones |
| `get_zones` | All zones with active/idle state |
| `get_schedule` | All programs: zones, durations, run days, start times |
| `get_rain_delay` | Current rain delay in days |
| `get_rain_sensor` | Rain sensor state (requires `RAINBIRD_RAIN_SENSOR=true`) |
| `get_device_info` | Model, protocol, firmware, serial |
| `get_wifi_info` | SSID, IP, netmask, gateway, MAC, RSSI |
| `get_network_status` | Network up / internet up |

### Resources

| URI | Description | Gated? |
|---|---|---|
| `rainbird://status` | Irrigation state, rain delay, device time, configured zones | No |
| `rainbird://zones` | Active/idle state per zone | No |
| `rainbird://schedule` | Programs: zones, durations, run days, start times | No |
| `rainbird://delay` | Current rain delay in days | No |
| `rainbird://sensor` | Rain sensor state | `RAINBIRD_RAIN_SENSOR=true` |
| `rainbird://info` | Device model, protocol, firmware, serial | No |
| `rainbird://wifi` | SSID, IP, netmask, gateway, MAC, RSSI | No |
| `rainbird://network` | Network up / internet up | No |

### Shared logic

`lib.py` contains all async pyrainbird functions. Both CLI commands and MCP server import from it.
