---
name: rainbird
description: Control and monitor a Rain Bird ESP-Me irrigation system using the `rainbird` CLI. Use when the user wants to water a zone, run sprinklers, check if irrigation is active, stop watering, set or clear a rain delay, check the rain sensor, view the watering schedule, run a preset program, or ask about the irrigation controller. Triggers on phrases like "water zone 2", "run the sprinklers", "stop watering", "is irrigation running", "check sprinklers", "set rain delay", "clear rain delay", "run program B", "check rain sensor", "view watering schedule", "test zone 3", "rainbird", "irrigation".
allowed-tools: Bash
---

# Rain Bird CLI Skill

`rainbird` controls a Rain Bird ESP-Me controller. Credentials auto-load from `.env` in the project root — no setup needed.

## Device Facts

- Hardware: Rain Bird ESP-Me
- Zones: 1–4 only (zone numbers outside this range will error)
- Programs: A, B, C, D (letters only — A=index 0, B=1, C=2, D=3)
- Controller is single-connection: returns 503 if Rain Bird cloud app holds it

## Control Commands

```bash
# Irrigate a zone for N minutes
rainbird run <zone> <minutes>
rainbird run 2 15          # Water zone 2 for 15 minutes

# Stop all irrigation immediately
rainbird stop

# Quick zone test (brief burst)
rainbird test <zone>
rainbird test 3

# Run a preset program
rainbird program <letter>
rainbird program B

# Advance to next zone in active program
rainbird advance
```

## Status & Query Commands

```bash
# Full dashboard: irrigation state, rain sensor, delay, device time, configured zones
rainbird status

# Table of all zones with Active/Idle status
rainbird zones

# Rain sensor state (Triggered / Clear)
rainbird sensor

# Read current rain delay
rainbird delay

# Set rain delay (days); 0 clears it
rainbird delay 3
rainbird delay 0
```

## Info Commands

```bash
# Hardware model, firmware version, serial number
rainbird info

# Wi-Fi SSID, IP, netmask, gateway, MAC, signal strength
rainbird wifi

# Network and internet connectivity
rainbird network

# All configured programs: zones, durations, days, start times
rainbird schedule
```

## Global Flags

```bash
--host <ip>         # Override controller IP (default: RAINBIRD_HOST env var)
--password <pw>     # Override password (default: RAINBIRD_PASSWORD env var)
--debug             # Show full Python tracebacks on errors
```

## Error Reference

| Error message | Meaning | What to do |
|---|---|---|
| `Authentication failed. Check your password.` | Wrong password | Check `.env` RAINBIRD_PASSWORD |
| `Controller busy. Try again in a moment.` | 503 — cloud app holds connection | Wait a moment and retry |
| `Cannot reach controller at {HOST}. Check host/network.` | No TCP connection | Check host/network config |
| `Zone X is not configured on this controller.` | Zone not in 1–4 | Use zones 1–4 only |
| `Program must be A, B, C, or D.` | Invalid program letter | Use A, B, C, or D |

All errors exit with code 1.

## Usage Notes

- `rainbird status` makes 6 separate API calls — slowest command, most complete picture
- `rainbird zones` is faster if you only need zone states
- Rain delay of 0 clears any active delay
- `rainbird advance` only works when a program is actively running
- If controller returns busy errors repeatedly, close the Rain Bird mobile app
