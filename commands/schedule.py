"""Schedule command."""

import aiohttp
from rich.table import Table

from core import app, console, get_controller, handle_errors, run_async
from formatting import format_duration, format_frequency


@app.command()
def schedule():
    """Show all programs: zones, durations, run days and times."""
    async def _run():
        async with handle_errors():
            async with aiohttp.ClientSession() as session:
                controller = await get_controller(session)
                sched = await controller.get_schedule()

        if not sched.programs:
            console.print("[dim]No programs configured.[/dim]")
            return

        for prog in sched.programs:
            letter = chr(ord("A") + prog.program)
            freq_str = format_frequency(prog)
            starts_str = ", ".join(t.strftime("%-I:%M %p") for t in prog.starts) if prog.starts else "No start times"
            header = f"[bold]Program {letter}[/bold] — {freq_str} — {starts_str}"

            if prog.durations:
                table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
                table.add_column("Zone", width=6)
                table.add_column("Duration")
                for zd in prog.durations:
                    table.add_row(str(zd.zone), format_duration(zd.duration))
                console.print(header)
                console.print(table)
            else:
                console.print(header)
                console.print("  [dim](no zones)[/dim]")
            console.print()

    run_async(_run())
