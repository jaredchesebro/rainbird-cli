"""Shared async pyrainbird functions for CLI and MCP server."""

import datetime

import aiohttp

from pyrainbird import async_client

from formatting import format_frequency


async def _controller(session: aiohttp.ClientSession, host: str, password: str):
    return await async_client.create_controller(session, host, password)


async def irrigate_zone(session: aiohttp.ClientSession, host: str, password: str, zone: int, minutes: int) -> None:
    controller = await _controller(session, host, password)
    available = await controller.get_available_stations()
    if zone not in available.active_set:
        raise ValueError(f"Zone {zone} is not configured on this controller")
    await controller.irrigate_zone(zone, minutes)


async def stop_irrigation(session: aiohttp.ClientSession, host: str, password: str) -> None:
    controller = await _controller(session, host, password)
    await controller.stop_irrigation()


async def test_zone(session: aiohttp.ClientSession, host: str, password: str, zone: int) -> None:
    controller = await _controller(session, host, password)
    available = await controller.get_available_stations()
    if zone not in available.active_set:
        raise ValueError(f"Zone {zone} is not configured on this controller")
    await controller.test_zone(zone)


async def start_program(session: aiohttp.ClientSession, host: str, password: str, program_num: int) -> None:
    controller = await _controller(session, host, password)
    await controller.set_program(program_num)


async def advance_zone(session: aiohttp.ClientSession, host: str, password: str) -> None:
    controller = await _controller(session, host, password)
    await controller.advance_zone(0)


async def get_status(session: aiohttp.ClientSession, host: str, password: str, rain_sensor: bool = False) -> dict:
    controller = await _controller(session, host, password)
    irrigating = await controller.get_current_irrigation()
    zone_states = await controller.get_zone_states()
    available = await controller.get_available_stations()
    sensor = await controller.get_rain_sensor_state() if rain_sensor else None
    rain_delay = await controller.get_rain_delay()
    device_time = await controller.get_current_time()
    device_date = await controller.get_current_date()

    dt = datetime.datetime.combine(device_date, device_time)
    active_zones = sorted(zone_states.active_set) if (irrigating and zone_states.active_set) else []

    return {
        "irrigating": bool(irrigating),
        "active_zones": active_zones,
        "rain_delay_days": rain_delay,
        "rain_sensor": sensor,
        "device_time": dt.isoformat(timespec="seconds"),
        "configured_zones": sorted(available.active_set),
    }


async def get_zones(session: aiohttp.ClientSession, host: str, password: str) -> dict:
    controller = await _controller(session, host, password)
    available = await controller.get_available_stations()
    states = await controller.get_zone_states()

    return {
        "zones": [
            {"zone": z, "active": z in states.active_set}
            for z in sorted(available.active_set)
        ]
    }


async def get_schedule(session: aiohttp.ClientSession, host: str, password: str) -> dict:
    controller = await _controller(session, host, password)
    sched = await controller.get_schedule()

    programs = []
    for prog in sched.programs:
        letter = chr(ord("A") + prog.program)
        freq_str = format_frequency(prog)
        start_times = [t.strftime("%H:%M") for t in prog.starts] if prog.starts else []
        zones = [
            {"zone": zd.zone, "duration_minutes": int(zd.duration.total_seconds() // 60)}
            for zd in prog.durations
        ]
        programs.append({
            "letter": letter,
            "frequency": freq_str,
            "start_times": start_times,
            "zones": zones,
        })

    return {"programs": programs}


async def get_delay(session: aiohttp.ClientSession, host: str, password: str) -> dict:
    controller = await _controller(session, host, password)
    days = await controller.get_rain_delay()
    return {"days": days}


async def set_delay(session: aiohttp.ClientSession, host: str, password: str, days: int) -> None:
    controller = await _controller(session, host, password)
    await controller.set_rain_delay(days)


async def get_sensor(session: aiohttp.ClientSession, host: str, password: str) -> dict:
    controller = await _controller(session, host, password)
    triggered = await controller.get_rain_sensor_state()
    return {"triggered": bool(triggered)}


async def get_info(session: aiohttp.ClientSession, host: str, password: str) -> dict:
    controller = await _controller(session, host, password)
    model = await controller.get_model_and_version()
    firmware = await controller.get_controller_firmware_version()
    serial = await controller.get_serial_number()

    return {
        "model": model.model_info.name,
        "model_id": f"0x{model.model:04X}",
        "protocol": f"{model.major}.{model.minor}",
        "firmware": f"{firmware.major}.{firmware.minor}.{firmware.patch}",
        "serial": str(serial),
    }


async def get_wifi(session: aiohttp.ClientSession, host: str, password: str) -> dict:
    controller = await _controller(session, host, password)
    params = await controller.get_wifi_params()

    return {
        "ssid": params.wifi_ssid or "",
        "ip": params.local_ip_address or "",
        "netmask": params.local_netmask or "",
        "gateway": params.local_gateway or "",
        "mac": params.mac_address or "",
        "rssi_dbm": params.rssi,
    }


async def get_network(session: aiohttp.ClientSession, host: str, password: str) -> dict:
    controller = await _controller(session, host, password)
    net_status = await controller.get_network_status()

    return {
        "network_up": bool(net_status.network_up),
        "internet_up": bool(net_status.internet_up),
    }
