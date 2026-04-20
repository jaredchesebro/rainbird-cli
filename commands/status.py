"""Status commands: status, zones, sensor, delay."""

import datetime
from typing import Optional

import aiohttp
import typer
from rich.panel import Panel
from rich.table import Table

from core import app, console, err_console, get_controller, handle_errors, run_async


@app.command()
def status():
    """Dashboard: active zones, rain sensor, delay, device time."""
    async def _run():
        async with handle_errors():
            async with aiohttp.ClientSession() as session:
                controller = await get_controller(session)
                irrigating = await controller.get_current_irrigation()
                zone_states = await controller.get_zone_states()
                available = await controller.get_available_stations()
                rain_sensor = await controller.get_rain_sensor_state()
                rain_delay = await controller.get_rain_delay()
                device_time = await controller.get_current_time()
                device_date = await controller.get_current_date()

        if irrigating and zone_states.active_set:
            active_zones = ", ".join(str(z) for z in sorted(zone_states.active_set))
            irrigation_str = f"[green]Active[/green] — Zone {active_zones}"
        elif irrigating:
            irrigation_str = "[green]Active[/green]"
        else:
            irrigation_str = "[dim]Idle[/dim]"

        sensor_str = "[yellow]Triggered[/yellow]" if rain_sensor else "[dim]Clear[/dim]"
        delay_str = f"{rain_delay} day{'s' if rain_delay != 1 else ''}" if rain_delay else "[dim]None[/dim]"

        dt = datetime.datetime.combine(device_date, device_time)
        time_str = dt.strftime("%-I:%M %p  %a %b %-d")

        configured = sorted(available.active_set)
        zones_str = ", ".join(str(z) for z in configured) if configured else "[dim]None[/dim]"

        table = Table.grid(padding=(0, 2))
        table.add_column(style="bold", min_width=18)
        table.add_column()
        for label, value in [
            ("Irrigation", irrigation_str),
            ("Rain sensor", sensor_str),
            ("Rain delay", delay_str),
            ("Device time", time_str),
            ("Configured zones", zones_str),
        ]:
            table.add_row(label, value)

        console.print(Panel(table, title="[bold]Controller Status[/bold]", expand=False))

    run_async(_run())


@app.command()
def zones():
    """List all configured zones and their active/idle state."""
    async def _run():
        async with handle_errors():
            async with aiohttp.ClientSession() as session:
                controller = await get_controller(session)
                available = await controller.get_available_stations()
                states = await controller.get_zone_states()

        table = Table(show_header=True, header_style="bold")
        table.add_column("Zone", style="bold", width=6)
        table.add_column("Status")
        for zone in sorted(available.active_set):
            if zone in states.active_set:
                table.add_row(str(zone), "[green]Active[/green]")
            else:
                table.add_row(str(zone), "[dim]Idle[/dim]")
        console.print(table)

    run_async(_run())


@app.command()
def sensor():
    """Show rain sensor state."""
    async def _run():
        async with handle_errors():
            async with aiohttp.ClientSession() as session:
                controller = await get_controller(session)
                active = await controller.get_rain_sensor_state()

        if active:
            console.print("Rain sensor: [yellow]Triggered[/yellow] (irrigation may be paused)")
        else:
            console.print("Rain sensor: [green]Clear[/green]")

    run_async(_run())


@app.command()
def delay(
    days: Optional[int] = typer.Argument(None, help="Days to delay (0 = clear). Omit to read current delay."),
):
    """Get or set rain delay. Pass days to set (0 clears it)."""
    async def _run():
        async with handle_errors():
            async with aiohttp.ClientSession() as session:
                controller = await get_controller(session)
                if days is None:
                    current = await controller.get_rain_delay()
                    if current:
                        console.print(f"Rain delay: {current} day{'s' if current != 1 else ''} remaining")
                    else:
                        console.print("Rain delay: [dim]None[/dim]")
                else:
                    await controller.set_rain_delay(days)
                    if days == 0:
                        console.print("[green]✓[/green] Rain delay cleared.")
                    else:
                        console.print(f"[green]✓[/green] Rain delay set to {days} day{'s' if days != 1 else ''}.")

    run_async(_run())
