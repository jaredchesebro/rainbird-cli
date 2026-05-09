"""Tests for ~/.local/bin/rainbird-mcp global wrapper script."""

import os
import stat
import subprocess


WRAPPER = os.path.expanduser("~/.local/bin/rainbird-mcp")
TARGET = "/Users/jared/.scripts/rainbird/.venv/bin/rainbird-mcp"


def test_wrapper_exists():
    assert os.path.isfile(WRAPPER)


def test_wrapper_is_executable():
    mode = os.stat(WRAPPER).st_mode
    assert mode & stat.S_IXUSR, "wrapper not user-executable"


def test_wrapper_delegates_to_venv_binary():
    content = open(WRAPPER).read()
    assert TARGET in content


def test_wrapper_passes_args_through():
    """MCP server exits 0 for --help (FastMCP accepts unknown flags silently).
    Confirms exec delegation reaches the target binary without error."""
    result = subprocess.run(
        [WRAPPER, "--help"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0
