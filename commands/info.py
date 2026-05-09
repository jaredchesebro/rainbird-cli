"""Device info commands: info, wifi, network."""

import aiohttp
from rich.panel import Panel
from rich.table import Table

import lib
from core import _ctx, app, console, handle_errors, run_async


@app.command()
def info():
    """Show device model, firmware, and serial number."""
    async def _run():
        async with handle_errors():
            async with aiohttp.ClientSession() as session:
                data = await lib.get_info(session, _ctx["host"], _ctx["password"])

        table = Table.grid(padding=(0, 2))
        table.add_column(style="bold", min_width=12)
        table.add_column()
        table.add_row("Model", f"{data['model']} ({data['model_id']})")
        table.add_row("Protocol", data["protocol"])
        table.add_row("Firmware", data["firmware"])
        table.add_row("Serial", data["serial"])
        console.print(Panel(table, title="[bold]Device Info[/bold]", expand=False))

    run_async(_run())


@app.command()
def wifi():
    """Show Wi-Fi connection details."""
    async def _run():
        async with handle_errors():
            async with aiohttp.ClientSession() as session:
                data = await lib.get_wifi(session, _ctx["host"], _ctx["password"])

        table = Table.grid(padding=(0, 2))
        table.add_column(style="bold", min_width=12)
        table.add_column()
        table.add_row("SSID", data["ssid"] or "[dim]—[/dim]")
        table.add_row("IP Address", data["ip"] or "[dim]—[/dim]")
        table.add_row("Netmask", data["netmask"] or "[dim]—[/dim]")
        table.add_row("Gateway", data["gateway"] or "[dim]—[/dim]")
        table.add_row("MAC", data["mac"] or "[dim]—[/dim]")
        table.add_row("Signal", f"{data['rssi_dbm']} dBm" if data["rssi_dbm"] else "[dim]—[/dim]")
        console.print(Panel(table, title="[bold]Wi-Fi[/bold]", expand=False))

    run_async(_run())


@app.command()
def network():
    """Show network and internet connectivity status."""
    async def _run():
        async with handle_errors():
            async with aiohttp.ClientSession() as session:
                data = await lib.get_network(session, _ctx["host"], _ctx["password"])

        net = "[green]Connected[/green]" if data["network_up"] else "[red]Disconnected[/red]"
        inet = "[green]Connected[/green]" if data["internet_up"] else "[red]Disconnected[/red]"

        table = Table.grid(padding=(0, 2))
        table.add_column(style="bold", min_width=12)
        table.add_column()
        table.add_row("Network", net)
        table.add_row("Internet", inet)
        console.print(Panel(table, title="[bold]Network[/bold]", expand=False))

    run_async(_run())
