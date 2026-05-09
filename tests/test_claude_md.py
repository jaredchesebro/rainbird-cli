"""Verify CLAUDE.md contains required MCP section documentation."""

import os
import re

CLAUDE_MD = os.path.join(os.path.dirname(__file__), "..", "CLAUDE.md")


def _content():
    with open(CLAUDE_MD) as f:
        return f.read()


def test_mcp_section_exists():
    assert "## MCP Server" in _content()


def test_mcp_tools_table_present():
    content = _content()
    for tool in ("irrigate_zone", "stop_irrigation", "test_zone", "advance_zone",
                 "set_rain_delay", "start_program"):
        assert tool in content, f"Tool '{tool}' missing from CLAUDE.md"


def test_mcp_resources_table_present():
    content = _content()
    for uri in ("rainbird://status", "rainbird://zones", "rainbird://schedule",
                "rainbird://delay", "rainbird://sensor", "rainbird://info",
                "rainbird://wifi", "rainbird://network"):
        assert uri in content, f"Resource URI '{uri}' missing from CLAUDE.md"


def test_mcp_entry_point_documented():
    assert "rainbird_mcp.py" in _content()


def test_mcp_global_wrapper_documented():
    assert "rainbird-mcp" in _content()


def test_mcp_env_vars_documented():
    content = _content()
    for var in ("RAINBIRD_HOST", "RAINBIRD_PASSWORD", "RAINBIRD_DEBUG"):
        assert var in content, f"Env var '{var}' missing from CLAUDE.md"


def test_mcp_lib_py_documented():
    assert "lib.py" in _content()


def test_mcp_start_program_confirmation_note():
    content = _content()
    assert "rainbird://schedule" in content
    # Confirm the confirmation requirement is noted near start_program
    idx_tool = content.find("start_program")
    assert idx_tool != -1
    surrounding = content[max(0, idx_tool - 50):idx_tool + 200]
    assert "confirm" in surrounding.lower() or "schedule" in surrounding.lower()
