"""Verify rainbird entry exists in Claude Desktop MCP config."""

import json
import os


CONFIG = os.path.expanduser(
    "~/Library/Application Support/Claude/claude_desktop_config.json"
)
WRAPPER = os.path.expanduser("~/.local/bin/rainbird-mcp")


def _config():
    with open(CONFIG) as f:
        return json.load(f)


def test_config_file_exists():
    assert os.path.isfile(CONFIG)


def test_rainbird_server_present():
    cfg = _config()
    assert "rainbird" in cfg.get("mcpServers", {})


def test_rainbird_command_is_wrapper():
    entry = _config()["mcpServers"]["rainbird"]
    assert entry["command"] == WRAPPER


def test_rainbird_env_has_host():
    entry = _config()["mcpServers"]["rainbird"]
    assert "RAINBIRD_HOST" in entry.get("env", {})
    assert entry["env"]["RAINBIRD_HOST"]


def test_rainbird_env_has_password():
    entry = _config()["mcpServers"]["rainbird"]
    assert "RAINBIRD_PASSWORD" in entry.get("env", {})
    assert entry["env"]["RAINBIRD_PASSWORD"]


def test_rainbird_config_is_valid_json():
    """Config file must remain valid JSON after edit."""
    with open(CONFIG) as f:
        data = json.load(f)
    assert isinstance(data, dict)
