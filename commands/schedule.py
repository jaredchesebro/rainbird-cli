"""Schedule command."""

import aiohttp
from rich.table import Table

import lib
from core import _ctx, app, console, handle_errors, run_async


def _fmt_time(t: str) -> str:
    """Format 'HH:MM' to '6:00 AM' style."""
    h, m = map(int, t.split(":"))
    period = "AM" if h < 12 else "PM"
    h12 = h % 12 or 12
    return f"{h12}:{m:02d} {period}"


@app.command()
def schedule():
    """Show all programs: zones, durations, run days and times."""
    async def _run():
        async with handle_errors():
            async with aiohttp.ClientSession() as session:
                data = await lib.get_schedule(session, _ctx["host"], _ctx["password"])

        if not data["programs"]:
            console.print("[dim]No programs configured.[/dim]")
            return

        for prog in data["programs"]:
            letter = prog["letter"]
            freq_str = prog["frequency"]
            starts = prog["start_times"]
            starts_str = ", ".join(_fmt_time(t) for t in starts) if starts else "No start times"
            header = f"[bold]Program {letter}[/bold] — {freq_str} — {starts_str}"

            if prog["zones"]:
                table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
                table.add_column("Zone", width=6)
                table.add_column("Duration")
                for zd in prog["zones"]:
                    table.add_row(str(zd["zone"]), f"{zd['duration_minutes']} min")
                console.print(header)
                console.print(table)
            else:
                console.print(header)
                console.print("  [dim](no zones)[/dim]")
            console.print()

    run_async(_run())
