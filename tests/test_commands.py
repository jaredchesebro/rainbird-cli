"""Unit tests for commands/ — verify delegation to lib.py and error handling."""

import datetime
from unittest.mock import AsyncMock, patch

import pytest
from typer.testing import CliRunner

import commands.control
import commands.info
import commands.schedule
import commands.status
import lib as lib_module
from rainbird import app


runner = CliRunner()

HOST = "192.168.1.50"
PASSWORD = "secret"

# Patch credentials in _ctx before each test
@pytest.fixture(autouse=True)
def patch_ctx(monkeypatch):
    import core
    monkeypatch.setitem(core._ctx, "host", HOST)
    monkeypatch.setitem(core._ctx, "password", PASSWORD)
    monkeypatch.setitem(core._ctx, "debug", False)
    monkeypatch.setitem(core._ctx, "rain_sensor", False)


@pytest.fixture()
def mock_session(monkeypatch):
    """Patch aiohttp.ClientSession so no real network calls happen."""
    import aiohttp
    from unittest.mock import MagicMock

    session = MagicMock()
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=session)
    cm.__aexit__ = AsyncMock(return_value=False)

    monkeypatch.setattr(aiohttp, "ClientSession", MagicMock(return_value=cm))
    return session


# ── control: run ──────────────────────────────────────────────────────────────

def test_run_command_calls_lib(mock_session, monkeypatch):
    monkeypatch.setattr(lib_module, "irrigate_zone", AsyncMock())
    result = runner.invoke(app, ["run", "2", "10"])
    assert result.exit_code == 0
    lib_module.irrigate_zone.assert_awaited_once()
    call_args = lib_module.irrigate_zone.call_args
    assert call_args.args[3] == 2   # zone
    assert call_args.args[4] == 10  # minutes


def test_run_command_invalid_zone_exits_nonzero(mock_session, monkeypatch):
    monkeypatch.setattr(
        lib_module, "irrigate_zone",
        AsyncMock(side_effect=ValueError("Zone 9 is not configured on this controller")),
    )
    result = runner.invoke(app, ["run", "9", "5"])
    assert result.exit_code != 0


# ── control: stop ─────────────────────────────────────────────────────────────

def test_stop_command_calls_lib(mock_session, monkeypatch):
    monkeypatch.setattr(lib_module, "stop_irrigation", AsyncMock())
    result = runner.invoke(app, ["stop"])
    assert result.exit_code == 0
    lib_module.stop_irrigation.assert_awaited_once()


# ── control: advance ──────────────────────────────────────────────────────────

def test_advance_command_calls_lib(mock_session, monkeypatch):
    monkeypatch.setattr(lib_module, "advance_zone", AsyncMock())
    result = runner.invoke(app, ["advance"])
    assert result.exit_code == 0
    lib_module.advance_zone.assert_awaited_once()


# ── control: program ──────────────────────────────────────────────────────────

def test_program_command_calls_lib(mock_session, monkeypatch):
    monkeypatch.setattr(lib_module, "start_program", AsyncMock())
    result = runner.invoke(app, ["program", "B"])
    assert result.exit_code == 0
    lib_module.start_program.assert_awaited_once()
    assert lib_module.start_program.call_args.args[3] == 1  # B = program_num 1


def test_program_command_rejects_invalid_letter(mock_session, monkeypatch):
    result = runner.invoke(app, ["program", "Z"])
    assert result.exit_code != 0


# ── status: status ────────────────────────────────────────────────────────────

def test_status_command_calls_lib(mock_session, monkeypatch):
    monkeypatch.setattr(lib_module, "get_status", AsyncMock(return_value={
        "irrigating": False,
        "active_zones": [],
        "rain_delay_days": 0,
        "rain_sensor": None,
        "device_time": "2026-05-09T07:32:00",
        "configured_zones": [1, 2, 3, 4],
    }))
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    lib_module.get_status.assert_awaited_once()


def test_status_command_shows_active_zone(mock_session, monkeypatch):
    monkeypatch.setattr(lib_module, "get_status", AsyncMock(return_value={
        "irrigating": True,
        "active_zones": [2],
        "rain_delay_days": 0,
        "rain_sensor": None,
        "device_time": "2026-05-09T07:32:00",
        "configured_zones": [1, 2, 3, 4],
    }))
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "2" in result.output


# ── status: zones ─────────────────────────────────────────────────────────────

def test_zones_command_calls_lib(mock_session, monkeypatch):
    monkeypatch.setattr(lib_module, "get_zones", AsyncMock(return_value={
        "zones": [
            {"zone": 1, "active": False},
            {"zone": 2, "active": True},
        ]
    }))
    result = runner.invoke(app, ["zones"])
    assert result.exit_code == 0
    lib_module.get_zones.assert_awaited_once()


# ── status: delay ─────────────────────────────────────────────────────────────

def test_delay_read_calls_lib(mock_session, monkeypatch):
    monkeypatch.setattr(lib_module, "get_delay", AsyncMock(return_value={"days": 3}))
    result = runner.invoke(app, ["delay"])
    assert result.exit_code == 0
    lib_module.get_delay.assert_awaited_once()
    assert "3" in result.output


def test_delay_write_calls_lib(mock_session, monkeypatch):
    monkeypatch.setattr(lib_module, "set_delay", AsyncMock())
    result = runner.invoke(app, ["delay", "2"])
    assert result.exit_code == 0
    lib_module.set_delay.assert_awaited_once()
    assert lib_module.set_delay.call_args.args[3] == 2


def test_delay_zero_clears(mock_session, monkeypatch):
    monkeypatch.setattr(lib_module, "set_delay", AsyncMock())
    result = runner.invoke(app, ["delay", "0"])
    assert result.exit_code == 0
    assert "cleared" in result.output.lower()


# ── info: info ────────────────────────────────────────────────────────────────

def test_info_command_calls_lib(mock_session, monkeypatch):
    monkeypatch.setattr(lib_module, "get_info", AsyncMock(return_value={
        "model": "ESP-Me",
        "model_id": "0x0007",
        "protocol": "2.9",
        "firmware": "1.63.0",
        "serial": "12345678",
    }))
    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0
    assert "ESP-Me" in result.output


# ── info: wifi ────────────────────────────────────────────────────────────────

def test_wifi_command_calls_lib(mock_session, monkeypatch):
    monkeypatch.setattr(lib_module, "get_wifi", AsyncMock(return_value={
        "ssid": "MyNet",
        "ip": "192.168.1.50",
        "netmask": "255.255.255.0",
        "gateway": "192.168.1.1",
        "mac": "AA:BB:CC:DD:EE:FF",
        "rssi_dbm": -62,
    }))
    result = runner.invoke(app, ["wifi"])
    assert result.exit_code == 0
    assert "MyNet" in result.output


# ── info: network ─────────────────────────────────────────────────────────────

def test_network_command_calls_lib(mock_session, monkeypatch):
    monkeypatch.setattr(lib_module, "get_network", AsyncMock(return_value={
        "network_up": True,
        "internet_up": False,
    }))
    result = runner.invoke(app, ["network"])
    assert result.exit_code == 0


# ── schedule ──────────────────────────────────────────────────────────────────

def test_schedule_command_calls_lib(mock_session, monkeypatch):
    monkeypatch.setattr(lib_module, "get_schedule", AsyncMock(return_value={
        "programs": [
            {
                "letter": "A",
                "frequency": "Mon Wed Fri",
                "start_times": ["06:00", "18:00"],
                "zones": [
                    {"zone": 1, "duration_minutes": 10},
                    {"zone": 2, "duration_minutes": 15},
                ],
            }
        ]
    }))
    result = runner.invoke(app, ["schedule"])
    assert result.exit_code == 0
    assert "Program A" in result.output
    assert "Mon Wed Fri" in result.output
    assert "6:00 AM" in result.output
    assert "10 min" in result.output


def test_schedule_empty(mock_session, monkeypatch):
    monkeypatch.setattr(lib_module, "get_schedule", AsyncMock(return_value={"programs": []}))
    result = runner.invoke(app, ["schedule"])
    assert result.exit_code == 0
    assert "No programs" in result.output


# ── control: test ────────────────────────────────────────────────────────────

def test_test_command_calls_lib(mock_session, monkeypatch):
    monkeypatch.setattr(lib_module, "test_zone", AsyncMock())
    result = runner.invoke(app, ["test", "3"])
    assert result.exit_code == 0
    lib_module.test_zone.assert_awaited_once()
    assert lib_module.test_zone.call_args.args[3] == 3


def test_test_command_invalid_zone_exits_nonzero(mock_session, monkeypatch):
    monkeypatch.setattr(
        lib_module, "test_zone",
        AsyncMock(side_effect=ValueError("Zone 9 is not configured on this controller")),
    )
    result = runner.invoke(app, ["test", "9"])
    assert result.exit_code != 0


# ── status: sensor ────────────────────────────────────────────────────────────

def test_sensor_command_not_configured(mock_session, monkeypatch):
    """When rain_sensor=False, prints not-configured message without calling lib."""
    import core
    monkeypatch.setitem(core._ctx, "rain_sensor", False)
    monkeypatch.setattr(lib_module, "get_sensor", AsyncMock())
    result = runner.invoke(app, ["sensor"])
    assert result.exit_code == 0
    assert "Not configured" in result.output or "RAINBIRD_RAIN_SENSOR" in result.output
    lib_module.get_sensor.assert_not_awaited()


def test_sensor_command_clear(mock_session, monkeypatch):
    monkeypatch.setenv("RAINBIRD_RAIN_SENSOR", "true")
    monkeypatch.setattr(lib_module, "get_sensor", AsyncMock(return_value={"triggered": False}))
    result = runner.invoke(app, ["sensor"])
    assert result.exit_code == 0
    assert "Clear" in result.output
    lib_module.get_sensor.assert_awaited_once()


def test_sensor_command_triggered(mock_session, monkeypatch):
    monkeypatch.setenv("RAINBIRD_RAIN_SENSOR", "true")
    monkeypatch.setattr(lib_module, "get_sensor", AsyncMock(return_value={"triggered": True}))
    result = runner.invoke(app, ["sensor"])
    assert result.exit_code == 0
    assert "Triggered" in result.output


# ── schedule: _fmt_time ───────────────────────────────────────────────────────

def test_fmt_time_am():
    from commands.schedule import _fmt_time
    assert _fmt_time("06:00") == "6:00 AM"
    assert _fmt_time("00:00") == "12:00 AM"


def test_fmt_time_pm():
    from commands.schedule import _fmt_time
    assert _fmt_time("18:00") == "6:00 PM"
    assert _fmt_time("12:00") == "12:00 PM"
