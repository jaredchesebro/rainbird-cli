"""Status commands: status, zones, sensor, delay."""

import datetime
from typing import Optional

import aiohttp
import typer
from rich.panel import Panel
from rich.table import Table

import lib
from core import _ctx, app, console, handle_errors, run_async


@app.command()
def status():
    """Dashboard: active zones, rain sensor, delay, device time."""
    async def _run():
        async with handle_errors():
            async with aiohttp.ClientSession() as session:
                data = await lib.get_status(
                    session, _ctx["host"], _ctx["password"],
                    rain_sensor=_ctx.get("rain_sensor", False),
                )

        if data["irrigating"] and data["active_zones"]:
            active_zones_str = ", ".join(str(z) for z in data["active_zones"])
            irrigation_str = f"[green]Active[/green] — Zone {active_zones_str}"
        elif data["irrigating"]:
            irrigation_str = "[green]Active[/green]"
        else:
            irrigation_str = "[dim]Idle[/dim]"

        if data["rain_sensor"] is None:
            sensor_str = None
        elif data["rain_sensor"]:
            sensor_str = "[yellow]Triggered[/yellow]"
        else:
            sensor_str = "[dim]Clear[/dim]"

        rain_delay = data["rain_delay_days"]
        delay_str = f"{rain_delay} day{'s' if rain_delay != 1 else ''}" if rain_delay else "[dim]None[/dim]"

        dt = datetime.datetime.fromisoformat(data["device_time"])
        time_str = dt.strftime("%-I:%M %p  %a %b %-d")

        configured = data["configured_zones"]
        zones_str = ", ".join(str(z) for z in configured) if configured else "[dim]None[/dim]"

        table = Table.grid(padding=(0, 2))
        table.add_column(style="bold", min_width=18)
        table.add_column()
        rows = [
            ("Irrigation", irrigation_str),
            ("Rain delay", delay_str),
            ("Device time", time_str),
            ("Configured zones", zones_str),
        ]
        if sensor_str is not None:
            rows.insert(1, ("Rain sensor", sensor_str))
        for label, value in rows:
            table.add_row(label, value)

        console.print(Panel(table, title="[bold]Controller Status[/bold]", expand=False))

    run_async(_run())


@app.command()
def zones():
    """List all configured zones and their active/idle state."""
    async def _run():
        async with handle_errors():
            async with aiohttp.ClientSession() as session:
                data = await lib.get_zones(session, _ctx["host"], _ctx["password"])

        table = Table(show_header=True, header_style="bold")
        table.add_column("Zone", style="bold", width=6)
        table.add_column("Status")
        for z in data["zones"]:
            if z["active"]:
                table.add_row(str(z["zone"]), "[green]Active[/green]")
            else:
                table.add_row(str(z["zone"]), "[dim]Idle[/dim]")
        console.print(table)

    run_async(_run())


@app.command()
def sensor():
    """Show rain sensor state."""
    if not _ctx.get("rain_sensor"):
        console.print("Rain sensor: [dim]Not configured[/dim] (set RAINBIRD_RAIN_SENSOR=true to enable)")
        return

    async def _run():
        async with handle_errors():
            async with aiohttp.ClientSession() as session:
                data = await lib.get_sensor(session, _ctx["host"], _ctx["password"])

        if data["triggered"]:
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
                if days is None:
                    data = await lib.get_delay(session, _ctx["host"], _ctx["password"])
                    current = data["days"]
                    if current:
                        console.print(f"Rain delay: {current} day{'s' if current != 1 else ''} remaining")
                    else:
                        console.print("Rain delay: [dim]None[/dim]")
                else:
                    await lib.set_delay(session, _ctx["host"], _ctx["password"], days)
                    if days == 0:
                        console.print("[green]✓[/green] Rain delay cleared.")
                    else:
                        console.print(f"[green]✓[/green] Rain delay set to {days} day{'s' if days != 1 else ''}.")

    run_async(_run())
