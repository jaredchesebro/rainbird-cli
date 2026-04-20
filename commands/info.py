"""Device info commands: info, wifi, network."""

import aiohttp
from rich.panel import Panel
from rich.table import Table

from core import app, console, get_controller, handle_errors, run_async


@app.command()
def info():
    """Show device model, firmware, and serial number."""
    async def _run():
        async with handle_errors():
            async with aiohttp.ClientSession() as session:
                controller = await get_controller(session)
                model = await controller.get_model_and_version()
                firmware = await controller.get_controller_firmware_version()
                serial = await controller.get_serial_number()

        table = Table.grid(padding=(0, 2))
        table.add_column(style="bold", min_width=12)
        table.add_column()
        table.add_row("Model", f"{model.model_info.name} (0x{model.model:04X})")
        table.add_row("Protocol", f"{model.major}.{model.minor}")
        table.add_row("Firmware", f"{firmware.major}.{firmware.minor}.{firmware.patch}")
        table.add_row("Serial", str(serial))
        console.print(Panel(table, title="[bold]Device Info[/bold]", expand=False))

    run_async(_run())


@app.command()
def wifi():
    """Show Wi-Fi connection details."""
    async def _run():
        async with handle_errors():
            async with aiohttp.ClientSession() as session:
                controller = await get_controller(session)
                params = await controller.get_wifi_params()

        table = Table.grid(padding=(0, 2))
        table.add_column(style="bold", min_width=12)
        table.add_column()
        table.add_row("SSID", params.wifi_ssid or "[dim]—[/dim]")
        table.add_row("IP Address", params.local_ip_address or "[dim]—[/dim]")
        table.add_row("Netmask", params.local_netmask or "[dim]—[/dim]")
        table.add_row("Gateway", params.local_gateway or "[dim]—[/dim]")
        table.add_row("MAC", params.mac_address or "[dim]—[/dim]")
        table.add_row("Signal", f"{params.rssi} dBm" if params.rssi else "[dim]—[/dim]")
        console.print(Panel(table, title="[bold]Wi-Fi[/bold]", expand=False))

    run_async(_run())


@app.command()
def network():
    """Show network and internet connectivity status."""
    async def _run():
        async with handle_errors():
            async with aiohttp.ClientSession() as session:
                controller = await get_controller(session)
                net_status = await controller.get_network_status()

        net = "[green]Connected[/green]" if net_status.network_up else "[red]Disconnected[/red]"
        inet = "[green]Connected[/green]" if net_status.internet_up else "[red]Disconnected[/red]"

        table = Table.grid(padding=(0, 2))
        table.add_column(style="bold", min_width=12)
        table.add_column()
        table.add_row("Network", net)
        table.add_row("Internet", inet)
        console.print(Panel(table, title="[bold]Network[/bold]", expand=False))

    run_async(_run())
