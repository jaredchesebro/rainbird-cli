"""Unit tests for lib.py — mock controller, verify dict shapes and logic."""

import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import lib


HOST = "192.168.1.50"
PASSWORD = "secret"


def make_session():
    return MagicMock()


def make_controller(**overrides):
    """Return an AsyncMock controller with sensible defaults."""
    ctrl = AsyncMock()

    stations = SimpleNamespace(active_set={1, 2, 3, 4})
    zone_states_idle = SimpleNamespace(active_set=set())
    zone_states_active = SimpleNamespace(active_set={2})

    ctrl.get_available_stations.return_value = stations
    ctrl.get_zone_states.return_value = zone_states_idle
    ctrl.get_current_irrigation.return_value = False
    ctrl.get_rain_sensor_state.return_value = False
    ctrl.get_rain_delay.return_value = 0
    ctrl.get_current_time.return_value = datetime.time(7, 32, 0)
    ctrl.get_current_date.return_value = datetime.date(2026, 5, 9)

    model_info = SimpleNamespace(name="ESP-Me")
    model = SimpleNamespace(model_info=model_info, model=0x0007, major=2, minor=9)
    ctrl.get_model_and_version.return_value = model

    firmware = SimpleNamespace(major=1, minor=63, patch=0)
    ctrl.get_controller_firmware_version.return_value = firmware
    ctrl.get_serial_number.return_value = 12345678

    wifi = SimpleNamespace(
        wifi_ssid="MyNetwork",
        local_ip_address="192.168.1.50",
        local_netmask="255.255.255.0",
        local_gateway="192.168.1.1",
        mac_address="AA:BB:CC:DD:EE:FF",
        rssi=-62,
    )
    ctrl.get_wifi_params.return_value = wifi

    net = SimpleNamespace(network_up=True, internet_up=True)
    ctrl.get_network_status.return_value = net

    from pyrainbird.const import DayOfWeek, ProgramFrequency
    prog = SimpleNamespace(
        program=0,
        frequency=ProgramFrequency.CUSTOM,
        days_of_week={DayOfWeek.MONDAY, DayOfWeek.WEDNESDAY, DayOfWeek.FRIDAY},
        period=None,
        starts=[datetime.time(6, 0), datetime.time(18, 0)],
        durations=[
            SimpleNamespace(zone=1, duration=datetime.timedelta(minutes=10)),
            SimpleNamespace(zone=2, duration=datetime.timedelta(minutes=15)),
        ],
    )
    sched = SimpleNamespace(programs=[prog])
    ctrl.get_schedule.return_value = sched

    for k, v in overrides.items():
        setattr(ctrl, k, v)

    return ctrl


@pytest.fixture
def mock_ctrl(monkeypatch):
    ctrl = make_controller()

    async def fake_create(session, host, password):
        return ctrl

    monkeypatch.setattr("lib.async_client.create_controller", fake_create)
    return ctrl


# ── get_status ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_status_idle(mock_ctrl):
    result = await lib.get_status(make_session(), HOST, PASSWORD)

    assert result["irrigating"] is False
    assert result["active_zones"] == []
    assert result["rain_delay_days"] == 0
    assert result["rain_sensor"] is None
    assert result["device_time"] == "2026-05-09T07:32:00"
    assert result["configured_zones"] == [1, 2, 3, 4]


@pytest.mark.asyncio
async def test_get_status_irrigating(monkeypatch):
    ctrl = make_controller()
    ctrl.get_current_irrigation.return_value = True
    ctrl.get_zone_states.return_value = SimpleNamespace(active_set={2})

    async def fake_create(session, host, password):
        return ctrl

    monkeypatch.setattr("lib.async_client.create_controller", fake_create)

    result = await lib.get_status(make_session(), HOST, PASSWORD)

    assert result["irrigating"] is True
    assert result["active_zones"] == [2]


@pytest.mark.asyncio
async def test_get_status_with_rain_sensor(mock_ctrl):
    mock_ctrl.get_rain_sensor_state.return_value = True

    result = await lib.get_status(make_session(), HOST, PASSWORD, rain_sensor=True)

    assert result["rain_sensor"] is True
    mock_ctrl.get_rain_sensor_state.assert_called_once()


@pytest.mark.asyncio
async def test_get_status_no_rain_sensor_skips_call(mock_ctrl):
    result = await lib.get_status(make_session(), HOST, PASSWORD, rain_sensor=False)

    assert result["rain_sensor"] is None
    mock_ctrl.get_rain_sensor_state.assert_not_called()


@pytest.mark.asyncio
async def test_get_status_rain_delay_passes_through(monkeypatch):
    """Non-zero rain_delay_days flows directly from controller into dict."""
    ctrl = make_controller()
    ctrl.get_rain_delay.return_value = 3

    async def fake_create(session, host, password):
        return ctrl

    monkeypatch.setattr("lib.async_client.create_controller", fake_create)

    result = await lib.get_status(make_session(), HOST, PASSWORD)
    assert result["rain_delay_days"] == 3


# ── get_zones ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_zones_all_idle(mock_ctrl):
    result = await lib.get_zones(make_session(), HOST, PASSWORD)

    assert result == {
        "zones": [
            {"zone": 1, "active": False},
            {"zone": 2, "active": False},
            {"zone": 3, "active": False},
            {"zone": 4, "active": False},
        ]
    }


@pytest.mark.asyncio
async def test_get_zones_one_active(monkeypatch):
    ctrl = make_controller()
    ctrl.get_zone_states.return_value = SimpleNamespace(active_set={3})

    async def fake_create(session, host, password):
        return ctrl

    monkeypatch.setattr("lib.async_client.create_controller", fake_create)

    result = await lib.get_zones(make_session(), HOST, PASSWORD)
    zones = {z["zone"]: z["active"] for z in result["zones"]}
    assert zones[3] is True
    assert zones[1] is False


# ── get_schedule ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_schedule_structure(mock_ctrl):
    result = await lib.get_schedule(make_session(), HOST, PASSWORD)

    assert "programs" in result
    assert len(result["programs"]) == 1
    prog = result["programs"][0]
    assert prog["letter"] == "A"
    assert "Mon" in prog["frequency"]
    assert "Wed" in prog["frequency"]
    assert "Fri" in prog["frequency"]
    assert prog["start_times"] == ["06:00", "18:00"]
    assert prog["zones"] == [
        {"zone": 1, "duration_minutes": 10},
        {"zone": 2, "duration_minutes": 15},
    ]


# ── get_delay / set_delay ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_delay_none(mock_ctrl):
    result = await lib.get_delay(make_session(), HOST, PASSWORD)
    assert result == {"days": 0}


@pytest.mark.asyncio
async def test_get_delay_set(monkeypatch):
    ctrl = make_controller()
    ctrl.get_rain_delay.return_value = 3

    async def fake_create(session, host, password):
        return ctrl

    monkeypatch.setattr("lib.async_client.create_controller", fake_create)

    result = await lib.get_delay(make_session(), HOST, PASSWORD)
    assert result == {"days": 3}


@pytest.mark.asyncio
async def test_set_delay_calls_controller(mock_ctrl):
    await lib.set_delay(make_session(), HOST, PASSWORD, 2)
    mock_ctrl.set_rain_delay.assert_called_once_with(2)


# ── get_sensor ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_sensor_clear(mock_ctrl):
    result = await lib.get_sensor(make_session(), HOST, PASSWORD)
    assert result == {"triggered": False}


@pytest.mark.asyncio
async def test_get_sensor_triggered(monkeypatch):
    ctrl = make_controller()
    ctrl.get_rain_sensor_state.return_value = True

    async def fake_create(session, host, password):
        return ctrl

    monkeypatch.setattr("lib.async_client.create_controller", fake_create)

    result = await lib.get_sensor(make_session(), HOST, PASSWORD)
    assert result == {"triggered": True}


# ── get_info ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_info(mock_ctrl):
    result = await lib.get_info(make_session(), HOST, PASSWORD)

    assert result == {
        "model": "ESP-Me",
        "model_id": "0x0007",
        "protocol": "2.9",
        "firmware": "1.63.0",
        "serial": "12345678",
    }


# ── get_wifi ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_wifi(mock_ctrl):
    result = await lib.get_wifi(make_session(), HOST, PASSWORD)

    assert result == {
        "ssid": "MyNetwork",
        "ip": "192.168.1.50",
        "netmask": "255.255.255.0",
        "gateway": "192.168.1.1",
        "mac": "AA:BB:CC:DD:EE:FF",
        "rssi_dbm": -62,
    }


@pytest.mark.asyncio
async def test_get_wifi_none_fields_become_empty_strings(monkeypatch):
    """pyrainbird can return None for wifi fields on some devices; ensure `or ""` guards work."""
    ctrl = make_controller()
    ctrl.get_wifi_params.return_value = SimpleNamespace(
        wifi_ssid=None,
        local_ip_address=None,
        local_netmask=None,
        local_gateway=None,
        mac_address=None,
        rssi=-45,
    )

    async def fake_create(session, host, password):
        return ctrl

    monkeypatch.setattr("lib.async_client.create_controller", fake_create)

    result = await lib.get_wifi(make_session(), HOST, PASSWORD)

    assert result["ssid"] == ""
    assert result["ip"] == ""
    assert result["netmask"] == ""
    assert result["gateway"] == ""
    assert result["mac"] == ""
    assert result["rssi_dbm"] == -45


# ── get_status: irrigating with empty active_set ──────────────────────────────

@pytest.mark.asyncio
async def test_get_status_irrigating_empty_active_set(monkeypatch):
    """Controller can report irrigating=True but active_set={} during zone transitions."""
    ctrl = make_controller()
    ctrl.get_current_irrigation.return_value = True
    ctrl.get_zone_states.return_value = SimpleNamespace(active_set=set())

    async def fake_create(session, host, password):
        return ctrl

    monkeypatch.setattr("lib.async_client.create_controller", fake_create)

    result = await lib.get_status(make_session(), HOST, PASSWORD)

    assert result["irrigating"] is True
    assert result["active_zones"] == []


# ── get_network ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_network(mock_ctrl):
    result = await lib.get_network(make_session(), HOST, PASSWORD)

    assert result == {"network_up": True, "internet_up": True}


# ── irrigate_zone ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_irrigate_zone_valid(mock_ctrl):
    await lib.irrigate_zone(make_session(), HOST, PASSWORD, zone=2, minutes=10)
    mock_ctrl.irrigate_zone.assert_called_once_with(2, 10)


@pytest.mark.asyncio
async def test_irrigate_zone_invalid_raises(mock_ctrl):
    with pytest.raises(ValueError, match="Zone 9"):
        await lib.irrigate_zone(make_session(), HOST, PASSWORD, zone=9, minutes=5)
    mock_ctrl.irrigate_zone.assert_not_called()


# ── stop_irrigation ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_stop_irrigation(mock_ctrl):
    await lib.stop_irrigation(make_session(), HOST, PASSWORD)
    mock_ctrl.stop_irrigation.assert_called_once()


# ── test_zone ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_test_zone_calls_controller(mock_ctrl):
    await lib.test_zone(make_session(), HOST, PASSWORD, zone=3)
    mock_ctrl.test_zone.assert_called_once_with(3)


@pytest.mark.asyncio
async def test_test_zone_invalid_raises(mock_ctrl):
    with pytest.raises(ValueError, match="Zone 9"):
        await lib.test_zone(make_session(), HOST, PASSWORD, zone=9)
    mock_ctrl.test_zone.assert_not_called()


@pytest.mark.asyncio
async def test_test_zone_invalid_does_not_call_get_available_stations_twice(mock_ctrl):
    """get_available_stations called exactly once — no extra controller round-trips on invalid zone."""
    with pytest.raises(ValueError):
        await lib.test_zone(make_session(), HOST, PASSWORD, zone=9)
    mock_ctrl.get_available_stations.assert_called_once()


# ── advance_zone ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_advance_zone(mock_ctrl):
    await lib.advance_zone(make_session(), HOST, PASSWORD)
    mock_ctrl.advance_zone.assert_called_once_with(0)


# ── start_program ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_start_program(mock_ctrl):
    await lib.start_program(make_session(), HOST, PASSWORD, program_num=1)
    mock_ctrl.set_program.assert_called_once_with(1)


# ── get_schedule: edge cases ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_schedule_program_letter_mapping(monkeypatch):
    """Programs B (1) and D (3) map to correct letters via chr(ord('A') + program)."""
    from pyrainbird.const import DayOfWeek, ProgramFrequency

    prog_b = SimpleNamespace(
        program=1,
        frequency=ProgramFrequency.CUSTOM,
        days_of_week={DayOfWeek.TUESDAY},
        period=None,
        starts=[datetime.time(7, 0)],
        durations=[SimpleNamespace(zone=2, duration=datetime.timedelta(minutes=5))],
    )
    prog_d = SimpleNamespace(
        program=3,
        frequency=ProgramFrequency.CYCLIC,
        days_of_week=set(),
        period=2,
        starts=[],
        durations=[],
    )
    ctrl = make_controller()
    ctrl.get_schedule.return_value = SimpleNamespace(programs=[prog_b, prog_d])

    async def fake_create(session, host, password):
        return ctrl

    monkeypatch.setattr("lib.async_client.create_controller", fake_create)

    result = await lib.get_schedule(make_session(), HOST, PASSWORD)

    letters = [p["letter"] for p in result["programs"]]
    assert letters == ["B", "D"]
    assert result["programs"][0]["start_times"] == ["07:00"]
    assert result["programs"][1]["start_times"] == []
    assert result["programs"][1]["zones"] == []


@pytest.mark.asyncio
async def test_get_schedule_none_starts_becomes_empty_list(monkeypatch):
    """prog.starts=None produces start_times=[] without raising."""
    from pyrainbird.const import DayOfWeek, ProgramFrequency

    prog = SimpleNamespace(
        program=2,
        frequency=ProgramFrequency.ODD,
        days_of_week=set(),
        period=None,
        starts=None,
        durations=[SimpleNamespace(zone=1, duration=datetime.timedelta(minutes=8))],
    )
    ctrl = make_controller()
    ctrl.get_schedule.return_value = SimpleNamespace(programs=[prog])

    async def fake_create(session, host, password):
        return ctrl

    monkeypatch.setattr("lib.async_client.create_controller", fake_create)

    result = await lib.get_schedule(make_session(), HOST, PASSWORD)

    assert result["programs"][0]["letter"] == "C"
    assert result["programs"][0]["start_times"] == []
    assert result["programs"][0]["zones"] == [{"zone": 1, "duration_minutes": 8}]


@pytest.mark.asyncio
async def test_get_schedule_empty_programs(monkeypatch):
    """Controller with no programs configured returns empty list."""
    ctrl = make_controller()
    ctrl.get_schedule.return_value = SimpleNamespace(programs=[])

    async def fake_create(session, host, password):
        return ctrl

    monkeypatch.setattr("lib.async_client.create_controller", fake_create)

    result = await lib.get_schedule(make_session(), HOST, PASSWORD)
    assert result == {"programs": []}
