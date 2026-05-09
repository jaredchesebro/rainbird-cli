"""Irrigation control commands: run, stop, test, program, advance."""

import aiohttp
import typer

import lib
from core import _ctx, app, console, err_console, handle_errors, run_async


@app.command()
def run(
    zone: int = typer.Argument(..., help="Zone number to irrigate"),
    minutes: int = typer.Argument(..., help="Duration in minutes"),
):
    """Irrigate a zone for a set number of minutes. Example: run 3 10"""
    async def _run():
        async with handle_errors():
            async with aiohttp.ClientSession() as session:
                try:
                    await lib.irrigate_zone(session, _ctx["host"], _ctx["password"], zone, minutes)
                except ValueError as e:
                    err_console.print(f"[red]Error:[/red] {e}")
                    raise typer.Exit(1)
            console.print(f"[green]✓[/green] Zone {zone} started — {minutes} minute{'s' if minutes != 1 else ''}.")

    run_async(_run())


@app.command()
def stop():
    """Stop all irrigation immediately."""
    async def _run():
        async with handle_errors():
            async with aiohttp.ClientSession() as session:
                await lib.stop_irrigation(session, _ctx["host"], _ctx["password"])
            console.print("[green]✓[/green] Irrigation stopped.")

    run_async(_run())


@app.command()
def test(zone: int = typer.Argument(..., help="Zone number to test")):
    """Run a quick test on a zone."""
    async def _run():
        async with handle_errors():
            async with aiohttp.ClientSession() as session:
                await lib.test_zone(session, _ctx["host"], _ctx["password"], zone)
            console.print(f"[green]✓[/green] Zone {zone} test started.")

    run_async(_run())


@app.command()
def program(letter: str = typer.Argument(..., help="Program letter: A, B, C, or D")):
    """Start a program by letter. Example: program B"""
    letter = letter.upper().strip()
    if len(letter) != 1 or letter not in "ABCD":
        err_console.print("[red]Error:[/red] Program must be A, B, C, or D.")
        raise typer.Exit(1)
    program_num = ord(letter) - ord("A")

    async def _run():
        async with handle_errors():
            async with aiohttp.ClientSession() as session:
                await lib.start_program(session, _ctx["host"], _ctx["password"], program_num)
            console.print(f"[green]✓[/green] Program {letter} started.")

    run_async(_run())


@app.command()
def advance():
    """Advance to the next zone in the active program."""
    async def _run():
        async with handle_errors():
            async with aiohttp.ClientSession() as session:
                await lib.advance_zone(session, _ctx["host"], _ctx["password"])
            console.print("[green]✓[/green] Advanced to next zone.")

    run_async(_run())
