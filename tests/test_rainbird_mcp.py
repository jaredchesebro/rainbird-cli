"""Unit tests for rainbird_mcp.py — mock lib functions, verify tool/resource shapes."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import rainbird_mcp as mcp_module


HOST = "192.168.1.50"
PASSWORD = "secret"


@pytest.fixture(autouse=True)
def patch_credentials(monkeypatch):
    monkeypatch.setattr(mcp_module, "_HOST", HOST)
    monkeypatch.setattr(mcp_module, "_PASSWORD", PASSWORD)
    monkeypatch.setattr(mcp_module, "_DEBUG", False)


@pytest.fixture()
def mock_session(monkeypatch):
    """Patch aiohttp.ClientSession to return a no-op async context manager."""
    session = MagicMock()
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=session)
    cm.__aexit__ = AsyncMock(return_value=False)
    monkeypatch.setattr(mcp_module.aiohttp, "ClientSession", MagicMock(return_value=cm))
    return session


# ── irrigate_zone ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_irrigate_zone_success(mock_session, monkeypatch):
    monkeypatch.setattr(mcp_module.lib, "irrigate_zone", AsyncMock())
    result = await mcp_module.irrigate_zone(zone=2, minutes=10)
    assert result["success"] is True
    assert "Zone 2" in result["message"]
    assert "10" in result["message"]


@pytest.mark.asyncio
async def test_irrigate_zone_singular_minute(mock_session, monkeypatch):
    monkeypatch.setattr(mcp_module.lib, "irrigate_zone", AsyncMock())
    result = await mcp_module.irrigate_zone(zone=1, minutes=1)
    assert result["success"] is True
    assert "1 minute" in result["message"]
    assert "minutes" not in result["message"]


@pytest.mark.asyncio
async def test_irrigate_zone_invalid_zone(mock_session, monkeypatch):
    monkeypatch.setattr(
        mcp_module.lib, "irrigate_zone",
        AsyncMock(side_effect=ValueError("Zone 9 is not configured on this controller"))
    )
    result = await mcp_module.irrigate_zone(zone=9, minutes=5)
    assert result["success"] is False
    assert "Zone 9" in result["error"]


@pytest.mark.asyncio
async def test_irrigate_zone_connection_error(mock_session, monkeypatch):
    from pyrainbird.exceptions import RainbirdConnectionError
    monkeypatch.setattr(
        mcp_module.lib, "irrigate_zone",
        AsyncMock(side_effect=RainbirdConnectionError("err"))
    )
    result = await mcp_module.irrigate_zone(zone=2, minutes=5)
    assert result["success"] is False
    assert HOST in result["error"]


# ── stop_irrigation ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_stop_irrigation_success(mock_session, monkeypatch):
    monkeypatch.setattr(mcp_module.lib, "stop_irrigation", AsyncMock())
    result = await mcp_module.stop_irrigation()
    assert result["success"] is True
    assert "stopped" in result["message"].lower()


@pytest.mark.asyncio
async def test_stop_irrigation_auth_error(mock_session, monkeypatch):
    from pyrainbird.exceptions import RainbirdAuthException
    monkeypatch.setattr(
        mcp_module.lib, "stop_irrigation",
        AsyncMock(side_effect=RainbirdAuthException("err"))
    )
    result = await mcp_module.stop_irrigation()
    assert result["success"] is False
    assert "Authentication" in result["error"]


# ── test_zone ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_test_zone_success(mock_session, monkeypatch):
    monkeypatch.setattr(mcp_module.lib, "test_zone", AsyncMock())
    result = await mcp_module.test_zone(zone=3)
    assert result["success"] is True
    assert "3" in result["message"]


@pytest.mark.asyncio
async def test_test_zone_invalid_zone(mock_session, monkeypatch):
    monkeypatch.setattr(
        mcp_module.lib, "test_zone",
        AsyncMock(side_effect=ValueError("Zone 9 is not configured on this controller"))
    )
    result = await mcp_module.test_zone(zone=9)
    assert result["success"] is False
    assert "Zone 9" in result["error"]


# ── advance_zone ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_advance_zone_success(mock_session, monkeypatch):
    monkeypatch.setattr(mcp_module.lib, "advance_zone", AsyncMock())
    result = await mcp_module.advance_zone()
    assert result["success"] is True


# ── set_rain_delay ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_set_rain_delay_sets_days(mock_session, monkeypatch):
    monkeypatch.setattr(mcp_module.lib, "set_delay", AsyncMock())
    result = await mcp_module.set_rain_delay(days=3)
    assert result["success"] is True
    assert "3" in result["message"]
    mcp_module.lib.set_delay.assert_called_once()


@pytest.mark.asyncio
async def test_set_rain_delay_zero_clears(mock_session, monkeypatch):
    monkeypatch.setattr(mcp_module.lib, "set_delay", AsyncMock())
    result = await mcp_module.set_rain_delay(days=0)
    assert result["success"] is True
    assert "cleared" in result["message"].lower()


@pytest.mark.asyncio
async def test_set_rain_delay_singular(mock_session, monkeypatch):
    monkeypatch.setattr(mcp_module.lib, "set_delay", AsyncMock())
    result = await mcp_module.set_rain_delay(days=1)
    assert "1 day" in result["message"]
    assert "days" not in result["message"]


# ── start_program ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_start_program_valid(mock_session, monkeypatch):
    monkeypatch.setattr(mcp_module.lib, "start_program", AsyncMock())
    result = await mcp_module.start_program(letter="B")
    assert result["success"] is True
    assert "B" in result["message"]
    mcp_module.lib.start_program.assert_called_once_with(mock_session, HOST, PASSWORD, 1)


@pytest.mark.asyncio
async def test_start_program_lowercase_normalized(mock_session, monkeypatch):
    monkeypatch.setattr(mcp_module.lib, "start_program", AsyncMock())
    result = await mcp_module.start_program(letter="c")
    assert result["success"] is True
    assert "C" in result["message"]


@pytest.mark.asyncio
async def test_start_program_invalid_letter(mock_session, monkeypatch):
    result = await mcp_module.start_program(letter="Z")
    assert result["success"] is False
    assert "A, B, C, or D" in result["error"]


@pytest.mark.asyncio
async def test_start_program_busy_error(mock_session, monkeypatch):
    from pyrainbird.exceptions import RainbirdDeviceBusyException
    monkeypatch.setattr(
        mcp_module.lib, "start_program",
        AsyncMock(side_effect=RainbirdDeviceBusyException("busy"))
    )
    result = await mcp_module.start_program(letter="A")
    assert result["success"] is False
    assert "busy" in result["error"].lower()


# ── _map_error ────────────────────────────────────────────────────────────────

def test_map_error_auth():
    from pyrainbird.exceptions import RainbirdAuthException
    msg = mcp_module._map_error(RainbirdAuthException("x"))
    assert "Authentication" in msg


def test_map_error_busy():
    from pyrainbird.exceptions import RainbirdDeviceBusyException
    msg = mcp_module._map_error(RainbirdDeviceBusyException("x"))
    assert "busy" in msg.lower()


def test_map_error_connection():
    from pyrainbird.exceptions import RainbirdConnectionError
    msg = mcp_module._map_error(RainbirdConnectionError("x"))
    assert HOST in msg or "reach" in msg


def test_map_error_api():
    from pyrainbird.exceptions import RainbirdApiException
    msg = mcp_module._map_error(RainbirdApiException("boom"))
    assert "Controller error" in msg


def test_map_error_generic():
    msg = mcp_module._map_error(RuntimeError("oops"))
    assert "oops" in msg


# ── Resources ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_resource_status_returns_json(mock_session, monkeypatch):
    expected = {"irrigating": False, "active_zones": [], "rain_delay_days": 0,
                "rain_sensor": None, "device_time": "2026-05-09T07:32:00",
                "configured_zones": [1, 2, 3, 4]}
    monkeypatch.setattr(mcp_module.lib, "get_status", AsyncMock(return_value=expected))
    result = await mcp_module.resource_status()
    assert json.loads(result) == expected


@pytest.mark.asyncio
async def test_resource_zones_returns_json(mock_session, monkeypatch):
    expected = {"zones": [{"zone": 1, "active": False}]}
    monkeypatch.setattr(mcp_module.lib, "get_zones", AsyncMock(return_value=expected))
    result = await mcp_module.resource_zones()
    assert json.loads(result) == expected


@pytest.mark.asyncio
async def test_resource_schedule_returns_json(mock_session, monkeypatch):
    expected = {"programs": []}
    monkeypatch.setattr(mcp_module.lib, "get_schedule", AsyncMock(return_value=expected))
    result = await mcp_module.resource_schedule()
    assert json.loads(result) == expected


@pytest.mark.asyncio
async def test_resource_delay_returns_json(mock_session, monkeypatch):
    monkeypatch.setattr(mcp_module.lib, "get_delay", AsyncMock(return_value={"days": 2}))
    result = await mcp_module.resource_delay()
    assert json.loads(result) == {"days": 2}


@pytest.mark.asyncio
async def test_resource_sensor_disabled_by_default(mock_session, monkeypatch):
    monkeypatch.setattr(mcp_module, "_RAIN_SENSOR", False)
    result = await mcp_module.resource_sensor()
    data = json.loads(result)
    assert "error" in data


@pytest.mark.asyncio
async def test_resource_sensor_enabled(mock_session, monkeypatch):
    monkeypatch.setattr(mcp_module, "_RAIN_SENSOR", True)
    monkeypatch.setattr(mcp_module.lib, "get_sensor", AsyncMock(return_value={"triggered": False}))
    result = await mcp_module.resource_sensor()
    assert json.loads(result) == {"triggered": False}


@pytest.mark.asyncio
async def test_resource_info_returns_json(mock_session, monkeypatch):
    expected = {"model": "ESP-Me", "model_id": "0x0007", "protocol": "2.9",
                "firmware": "1.63.0", "serial": "12345678"}
    monkeypatch.setattr(mcp_module.lib, "get_info", AsyncMock(return_value=expected))
    result = await mcp_module.resource_info()
    assert json.loads(result) == expected


@pytest.mark.asyncio
async def test_resource_wifi_returns_json(mock_session, monkeypatch):
    expected = {"ssid": "MyNet", "ip": "192.168.1.50", "netmask": "255.255.255.0",
                "gateway": "192.168.1.1", "mac": "AA:BB:CC:DD:EE:FF", "rssi_dbm": -62}
    monkeypatch.setattr(mcp_module.lib, "get_wifi", AsyncMock(return_value=expected))
    result = await mcp_module.resource_wifi()
    assert json.loads(result) == expected


@pytest.mark.asyncio
async def test_resource_network_returns_json(mock_session, monkeypatch):
    monkeypatch.setattr(mcp_module.lib, "get_network",
                        AsyncMock(return_value={"network_up": True, "internet_up": True}))
    result = await mcp_module.resource_network()
    assert json.loads(result) == {"network_up": True, "internet_up": True}


# ── MCP server registration (structural — equiv. of mcp dev inspector) ─────────

EXPECTED_TOOLS = {
    # Action tools
    "irrigate_zone": {"zone", "minutes"},
    "stop_irrigation": set(),
    "test_zone": {"zone"},
    "advance_zone": set(),
    "set_rain_delay": {"days"},
    "start_program": {"letter"},
    # Read-only tools (mirror the resources for tool-call access)
    "get_status": set(),
    "get_zones": set(),
    "get_schedule": set(),
    "get_rain_delay": set(),
    "get_rain_sensor": set(),
    "get_device_info": set(),
    "get_wifi_info": set(),
    "get_network_status": set(),
}

EXPECTED_RESOURCES = {
    "rainbird://status",
    "rainbird://zones",
    "rainbird://schedule",
    "rainbird://delay",
    "rainbird://sensor",
    "rainbird://info",
    "rainbird://wifi",
    "rainbird://network",
}


@pytest.mark.asyncio
async def test_mcp_tools_registered():
    tools = await mcp_module.mcp.list_tools()
    registered = {t.name: set(t.inputSchema.get("properties", {}).keys()) for t in tools}
    assert registered == EXPECTED_TOOLS


@pytest.mark.asyncio
async def test_mcp_resources_registered():
    resources = await mcp_module.mcp.list_resources()
    uris = {str(r.uri) for r in resources}
    assert uris == EXPECTED_RESOURCES


@pytest.mark.asyncio
async def test_mcp_start_program_confirmation_in_description():
    tools = await mcp_module.mcp.list_tools()
    sp = next(t for t in tools if t.name == "start_program")
    assert "schedule" in (sp.description or "").lower()
    assert "confirm" in (sp.description or "").lower()


# ── _DEBUG re-raise behavior ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_irrigate_zone_debug_reraises(mock_session, monkeypatch):
    """When _DEBUG=True, exceptions propagate instead of being caught."""
    from pyrainbird.exceptions import RainbirdConnectionError
    monkeypatch.setattr(mcp_module, "_DEBUG", True)
    monkeypatch.setattr(
        mcp_module.lib, "irrigate_zone",
        AsyncMock(side_effect=RainbirdConnectionError("timeout"))
    )
    with pytest.raises(RainbirdConnectionError):
        await mcp_module.irrigate_zone(zone=1, minutes=5)


@pytest.mark.asyncio
async def test_stop_irrigation_debug_reraises(mock_session, monkeypatch):
    from pyrainbird.exceptions import RainbirdAuthException
    monkeypatch.setattr(mcp_module, "_DEBUG", True)
    monkeypatch.setattr(
        mcp_module.lib, "stop_irrigation",
        AsyncMock(side_effect=RainbirdAuthException("bad password"))
    )
    with pytest.raises(RainbirdAuthException):
        await mcp_module.stop_irrigation()


@pytest.mark.asyncio
async def test_start_program_debug_reraises(mock_session, monkeypatch):
    from pyrainbird.exceptions import RainbirdDeviceBusyException
    monkeypatch.setattr(mcp_module, "_DEBUG", True)
    monkeypatch.setattr(
        mcp_module.lib, "start_program",
        AsyncMock(side_effect=RainbirdDeviceBusyException("busy"))
    )
    with pytest.raises(RainbirdDeviceBusyException):
        await mcp_module.start_program(letter="A")


# ── Resource error propagation ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_resource_status_propagates_connection_error(mock_session, monkeypatch):
    """Resources have no try/except — lib exceptions propagate to MCP framework."""
    from pyrainbird.exceptions import RainbirdConnectionError
    monkeypatch.setattr(
        mcp_module.lib, "get_status",
        AsyncMock(side_effect=RainbirdConnectionError("timeout"))
    )
    with pytest.raises(RainbirdConnectionError):
        await mcp_module.resource_status()


@pytest.mark.asyncio
async def test_resource_zones_propagates_auth_error(mock_session, monkeypatch):
    from pyrainbird.exceptions import RainbirdAuthException
    monkeypatch.setattr(
        mcp_module.lib, "get_zones",
        AsyncMock(side_effect=RainbirdAuthException("bad password"))
    )
    with pytest.raises(RainbirdAuthException):
        await mcp_module.resource_zones()


@pytest.mark.asyncio
async def test_resource_schedule_propagates_api_error(mock_session, monkeypatch):
    from pyrainbird.exceptions import RainbirdApiException
    monkeypatch.setattr(
        mcp_module.lib, "get_schedule",
        AsyncMock(side_effect=RainbirdApiException("nack"))
    )
    with pytest.raises(RainbirdApiException):
        await mcp_module.resource_schedule()


# ── Read-only tools ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_tool_get_status_success(mock_session, monkeypatch):
    expected = {"irrigating": False, "active_zones": [], "rain_delay_days": 0,
                "rain_sensor": None, "device_time": "2026-05-09T07:32:00",
                "configured_zones": [1, 2, 3, 4]}
    monkeypatch.setattr(mcp_module.lib, "get_status", AsyncMock(return_value=expected))
    result = await mcp_module.get_status()
    assert result == expected


@pytest.mark.asyncio
async def test_tool_get_status_error_returns_error_dict(mock_session, monkeypatch):
    from pyrainbird.exceptions import RainbirdConnectionError
    monkeypatch.setattr(
        mcp_module.lib, "get_status",
        AsyncMock(side_effect=RainbirdConnectionError("timeout"))
    )
    result = await mcp_module.get_status()
    assert "error" in result
    assert HOST in result["error"]


@pytest.mark.asyncio
async def test_tool_get_zones_success(mock_session, monkeypatch):
    expected = {"zones": [{"zone": 1, "active": False}]}
    monkeypatch.setattr(mcp_module.lib, "get_zones", AsyncMock(return_value=expected))
    result = await mcp_module.get_zones()
    assert result == expected


@pytest.mark.asyncio
async def test_tool_get_schedule_success(mock_session, monkeypatch):
    expected = {"programs": []}
    monkeypatch.setattr(mcp_module.lib, "get_schedule", AsyncMock(return_value=expected))
    result = await mcp_module.get_schedule()
    assert result == expected


@pytest.mark.asyncio
async def test_tool_get_rain_delay_success(mock_session, monkeypatch):
    monkeypatch.setattr(mcp_module.lib, "get_delay", AsyncMock(return_value={"days": 2}))
    result = await mcp_module.get_rain_delay()
    assert result == {"days": 2}


@pytest.mark.asyncio
async def test_tool_get_rain_sensor_disabled(mock_session, monkeypatch):
    monkeypatch.setattr(mcp_module, "_RAIN_SENSOR", False)
    result = await mcp_module.get_rain_sensor()
    assert "error" in result


@pytest.mark.asyncio
async def test_tool_get_rain_sensor_enabled(mock_session, monkeypatch):
    monkeypatch.setattr(mcp_module, "_RAIN_SENSOR", True)
    monkeypatch.setattr(mcp_module.lib, "get_sensor", AsyncMock(return_value={"triggered": False}))
    result = await mcp_module.get_rain_sensor()
    assert result == {"triggered": False}


@pytest.mark.asyncio
async def test_tool_get_device_info_success(mock_session, monkeypatch):
    expected = {"model": "ESP-Me", "model_id": "0x0007", "protocol": "2.9",
                "firmware": "1.63.0", "serial": "12345678"}
    monkeypatch.setattr(mcp_module.lib, "get_info", AsyncMock(return_value=expected))
    result = await mcp_module.get_device_info()
    assert result == expected


@pytest.mark.asyncio
async def test_tool_get_wifi_info_success(mock_session, monkeypatch):
    expected = {"ssid": "MyNet", "ip": "192.168.1.50", "netmask": "255.255.255.0",
                "gateway": "192.168.1.1", "mac": "AA:BB:CC:DD:EE:FF", "rssi_dbm": -62}
    monkeypatch.setattr(mcp_module.lib, "get_wifi", AsyncMock(return_value=expected))
    result = await mcp_module.get_wifi_info()
    assert result == expected


@pytest.mark.asyncio
async def test_tool_get_network_status_success(mock_session, monkeypatch):
    monkeypatch.setattr(mcp_module.lib, "get_network",
                        AsyncMock(return_value={"network_up": True, "internet_up": True}))
    result = await mcp_module.get_network_status()
    assert result == {"network_up": True, "internet_up": True}


@pytest.mark.asyncio
async def test_tool_get_status_debug_reraises(mock_session, monkeypatch):
    from pyrainbird.exceptions import RainbirdAuthException
    monkeypatch.setattr(mcp_module, "_DEBUG", True)
    monkeypatch.setattr(
        mcp_module.lib, "get_status",
        AsyncMock(side_effect=RainbirdAuthException("bad password"))
    )
    with pytest.raises(RainbirdAuthException):
        await mcp_module.get_status()


# ── start_program program_num mapping ────────────────────────────────────────

@pytest.mark.asyncio
async def test_start_program_all_letters_map_correctly(mock_session, monkeypatch):
    """Verify A→0, B→1, C→2, D→3 program_num calculation."""
    monkeypatch.setattr(mcp_module.lib, "start_program", AsyncMock())
    for letter, expected_num in [("A", 0), ("B", 1), ("C", 2), ("D", 3)]:
        mcp_module.lib.start_program.reset_mock()
        result = await mcp_module.start_program(letter=letter)
        assert result["success"] is True
        call_args = mcp_module.lib.start_program.call_args
        assert call_args.args[3] == expected_num, f"{letter} should map to program_num {expected_num}"
