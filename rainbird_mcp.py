"""Rain Bird MCP server — FastMCP entry point."""

import json
import os

import aiohttp
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from pyrainbird.exceptions import (
    RainbirdApiException,
    RainbirdAuthException,
    RainbirdConnectionError,
    RainbirdDeviceBusyException,
)

import lib

load_dotenv()

mcp = FastMCP("rainbird")

_HOST = os.environ.get("RAINBIRD_HOST", "")
_PASSWORD = os.environ.get("RAINBIRD_PASSWORD", "")
_RAIN_SENSOR = os.environ.get("RAINBIRD_RAIN_SENSOR", "").lower() == "true"
_DEBUG = os.environ.get("RAINBIRD_DEBUG", "").lower() == "true"


def _map_error(e: Exception) -> str:
    if isinstance(e, RainbirdAuthException):
        return "Authentication failed. Check your password."
    if isinstance(e, RainbirdDeviceBusyException):
        return "Controller busy. Try again in a moment."
    if isinstance(e, RainbirdConnectionError):
        return f"Cannot reach controller at {_HOST}. Check host/network."
    if isinstance(e, RainbirdApiException):
        return f"Controller error: {e}"
    return str(e)


# ── Tools ─────────────────────────────────────────────────────────────────────

@mcp.tool()
async def irrigate_zone(zone: int, minutes: int) -> dict:
    """Start irrigation on a specific zone for N minutes."""
    async with aiohttp.ClientSession() as session:
        try:
            await lib.irrigate_zone(session, _HOST, _PASSWORD, zone, minutes)
            s = "" if minutes == 1 else "s"
            return {"success": True, "message": f"Zone {zone} started — {minutes} minute{s}"}
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            if _DEBUG:
                raise
            return {"success": False, "error": _map_error(e)}


@mcp.tool()
async def stop_irrigation() -> dict:
    """Stop all irrigation immediately."""
    async with aiohttp.ClientSession() as session:
        try:
            await lib.stop_irrigation(session, _HOST, _PASSWORD)
            return {"success": True, "message": "Irrigation stopped"}
        except Exception as e:
            if _DEBUG:
                raise
            return {"success": False, "error": _map_error(e)}


@mcp.tool()
async def test_zone(zone: int) -> dict:
    """Run a quick test on a zone."""
    async with aiohttp.ClientSession() as session:
        try:
            await lib.test_zone(session, _HOST, _PASSWORD, zone)
            return {"success": True, "message": f"Zone {zone} test started"}
        except Exception as e:
            if _DEBUG:
                raise
            return {"success": False, "error": _map_error(e)}


@mcp.tool()
async def advance_zone() -> dict:
    """Advance to the next zone in the active program."""
    async with aiohttp.ClientSession() as session:
        try:
            await lib.advance_zone(session, _HOST, _PASSWORD)
            return {"success": True, "message": "Advanced to next zone"}
        except Exception as e:
            if _DEBUG:
                raise
            return {"success": False, "error": _map_error(e)}


@mcp.tool()
async def set_rain_delay(days: int) -> dict:
    """Set rain delay in days. Pass 0 to clear the delay."""
    async with aiohttp.ClientSession() as session:
        try:
            await lib.set_delay(session, _HOST, _PASSWORD, days)
            if days == 0:
                msg = "Rain delay cleared"
            else:
                s = "" if days == 1 else "s"
                msg = f"Rain delay set to {days} day{s}"
            return {"success": True, "message": msg}
        except Exception as e:
            if _DEBUG:
                raise
            return {"success": False, "error": _map_error(e)}


@mcp.tool()
async def start_program(letter: str) -> dict:
    """Start an irrigation program by letter (A/B/C/D).

    IMPORTANT: Before calling this tool, fetch the rainbird://schedule resource to show
    the user what program {letter} will run, then ask for explicit confirmation before proceeding.
    """
    letter = letter.upper().strip()
    if len(letter) != 1 or letter not in "ABCD":
        return {"success": False, "error": "Program must be A, B, C, or D"}
    program_num = ord(letter) - ord("A")
    async with aiohttp.ClientSession() as session:
        try:
            await lib.start_program(session, _HOST, _PASSWORD, program_num)
            return {"success": True, "message": f"Program {letter} started"}
        except Exception as e:
            if _DEBUG:
                raise
            return {"success": False, "error": _map_error(e)}


# ── Read-only tools ───────────────────────────────────────────────────────────

@mcp.tool()
async def get_status() -> dict:
    """Get controller status: active zones, irrigation state, rain delay, device time, configured zones."""
    async with aiohttp.ClientSession() as session:
        try:
            return await lib.get_status(session, _HOST, _PASSWORD, rain_sensor=_RAIN_SENSOR)
        except Exception as e:
            if _DEBUG:
                raise
            return {"error": _map_error(e)}


@mcp.tool()
async def get_zones() -> dict:
    """Get all configured zones and their active/idle state."""
    async with aiohttp.ClientSession() as session:
        try:
            return await lib.get_zones(session, _HOST, _PASSWORD)
        except Exception as e:
            if _DEBUG:
                raise
            return {"error": _map_error(e)}


@mcp.tool()
async def get_schedule() -> dict:
    """Get all irrigation programs: zones, durations, run days, start times."""
    async with aiohttp.ClientSession() as session:
        try:
            return await lib.get_schedule(session, _HOST, _PASSWORD)
        except Exception as e:
            if _DEBUG:
                raise
            return {"error": _map_error(e)}


@mcp.tool()
async def get_rain_delay() -> dict:
    """Get current rain delay in days."""
    async with aiohttp.ClientSession() as session:
        try:
            return await lib.get_delay(session, _HOST, _PASSWORD)
        except Exception as e:
            if _DEBUG:
                raise
            return {"error": _map_error(e)}


@mcp.tool()
async def get_rain_sensor() -> dict:
    """Get rain sensor state (triggered/clear). Requires RAINBIRD_RAIN_SENSOR=true."""
    if not _RAIN_SENSOR:
        return {"error": "Rain sensor not enabled. Set RAINBIRD_RAIN_SENSOR=true."}
    async with aiohttp.ClientSession() as session:
        try:
            return await lib.get_sensor(session, _HOST, _PASSWORD)
        except Exception as e:
            if _DEBUG:
                raise
            return {"error": _map_error(e)}


@mcp.tool()
async def get_device_info() -> dict:
    """Get device model, protocol version, firmware version, and serial number."""
    async with aiohttp.ClientSession() as session:
        try:
            return await lib.get_info(session, _HOST, _PASSWORD)
        except Exception as e:
            if _DEBUG:
                raise
            return {"error": _map_error(e)}


@mcp.tool()
async def get_wifi_info() -> dict:
    """Get Wi-Fi connection details: SSID, IP, netmask, gateway, MAC, signal strength."""
    async with aiohttp.ClientSession() as session:
        try:
            return await lib.get_wifi(session, _HOST, _PASSWORD)
        except Exception as e:
            if _DEBUG:
                raise
            return {"error": _map_error(e)}


@mcp.tool()
async def get_network_status() -> dict:
    """Get network and internet connectivity status."""
    async with aiohttp.ClientSession() as session:
        try:
            return await lib.get_network(session, _HOST, _PASSWORD)
        except Exception as e:
            if _DEBUG:
                raise
            return {"error": _map_error(e)}


# ── Resources ─────────────────────────────────────────────────────────────────

@mcp.resource("rainbird://status")
async def resource_status() -> str:
    """Irrigation state, rain delay, device time, configured zones."""
    async with aiohttp.ClientSession() as session:
        data = await lib.get_status(session, _HOST, _PASSWORD, rain_sensor=_RAIN_SENSOR)
    return json.dumps(data)


@mcp.resource("rainbird://zones")
async def resource_zones() -> str:
    """Configured zones with active/idle state per zone."""
    async with aiohttp.ClientSession() as session:
        data = await lib.get_zones(session, _HOST, _PASSWORD)
    return json.dumps(data)


@mcp.resource("rainbird://schedule")
async def resource_schedule() -> str:
    """All programs: zones, durations, run days, start times."""
    async with aiohttp.ClientSession() as session:
        data = await lib.get_schedule(session, _HOST, _PASSWORD)
    return json.dumps(data)


@mcp.resource("rainbird://delay")
async def resource_delay() -> str:
    """Current rain delay in days."""
    async with aiohttp.ClientSession() as session:
        data = await lib.get_delay(session, _HOST, _PASSWORD)
    return json.dumps(data)


@mcp.resource("rainbird://sensor")
async def resource_sensor() -> str:
    """Rain sensor state (triggered/clear). Requires RAINBIRD_RAIN_SENSOR=true."""
    if not _RAIN_SENSOR:
        return json.dumps({"error": "Rain sensor not enabled. Set RAINBIRD_RAIN_SENSOR=true."})
    async with aiohttp.ClientSession() as session:
        data = await lib.get_sensor(session, _HOST, _PASSWORD)
    return json.dumps(data)


@mcp.resource("rainbird://info")
async def resource_info() -> str:
    """Device model, protocol version, firmware, serial."""
    async with aiohttp.ClientSession() as session:
        data = await lib.get_info(session, _HOST, _PASSWORD)
    return json.dumps(data)


@mcp.resource("rainbird://wifi")
async def resource_wifi() -> str:
    """SSID, IP, netmask, gateway, MAC, RSSI."""
    async with aiohttp.ClientSession() as session:
        data = await lib.get_wifi(session, _HOST, _PASSWORD)
    return json.dumps(data)


@mcp.resource("rainbird://network")
async def resource_network() -> str:
    """Network up / internet up booleans."""
    async with aiohttp.ClientSession() as session:
        data = await lib.get_network(session, _HOST, _PASSWORD)
    return json.dumps(data)


def main():
    mcp.run()
