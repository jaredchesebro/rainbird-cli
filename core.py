"""Shared state, app instance, async helpers, and error handling."""

import asyncio
from contextlib import asynccontextmanager
from typing import Optional

import aiohttp
import typer
from dotenv import load_dotenv
from rich.console import Console

from pyrainbird import async_client
from pyrainbird.exceptions import (
    RainbirdApiException,
    RainbirdAuthException,
    RainbirdConnectionError,
    RainbirdDeviceBusyException,
)

load_dotenv()

app = typer.Typer(no_args_is_help=True, help="Control your Rain Bird irrigation system.")
console = Console()
err_console = Console(stderr=True)

_ctx: dict = {}


def run_async(coro):
    return asyncio.run(coro)


@asynccontextmanager
async def handle_errors():
    host = _ctx.get("host", "")
    debug = _ctx.get("debug", False)
    try:
        yield
    except RainbirdAuthException:
        err_console.print("[red]Error:[/red] Authentication failed. Check your password.")
        if debug:
            raise
        raise typer.Exit(1)
    except RainbirdDeviceBusyException:
        err_console.print("[red]Error:[/red] Controller busy. Try again in a moment.")
        if debug:
            raise
        raise typer.Exit(1)
    except RainbirdConnectionError:
        err_console.print(f"[red]Error:[/red] Cannot reach controller at {host}. Check host/network.")
        if debug:
            raise
        raise typer.Exit(1)
    except RainbirdApiException as e:
        err_console.print(f"[red]Error:[/red] Controller error: {e}")
        if debug:
            raise
        raise typer.Exit(1)


async def get_controller(session: aiohttp.ClientSession):
    return await async_client.create_controller(
        session, _ctx.get("host"), _ctx.get("password")
    )


@app.callback()
def main(
    host: Optional[str] = typer.Option(None, envvar="RAINBIRD_HOST", help="Controller IP address"),
    password: Optional[str] = typer.Option(None, envvar="RAINBIRD_PASSWORD", help="Controller password"),
    debug: bool = typer.Option(False, "--debug", help="Show full error tracebacks"),
    rain_sensor: Optional[str] = typer.Option(None, envvar="RAINBIRD_RAIN_SENSOR", hidden=True),
):
    if not host or not password:
        err_console.print("[red]Error:[/red] RAINBIRD_HOST and RAINBIRD_PASSWORD required (.env or --host/--password).")
        raise typer.Exit(1)
    _ctx["host"] = host
    _ctx["password"] = password
    _ctx["debug"] = debug
    _ctx["rain_sensor"] = (rain_sensor or "").lower() == "true"
