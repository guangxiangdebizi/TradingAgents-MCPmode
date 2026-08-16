import json
from pathlib import Path

from src.mcp_config import active_servers, configured_servers


ROOT = Path(__file__).resolve().parents[1]


def test_repository_configs_use_one_canonical_schema():
    for filename in ("mcp_config.json", "mcp_config.json.example"):
        config = json.loads((ROOT / filename).read_text(encoding="utf-8"))
        assert "mcpServers" in config
        assert "servers" not in config


def test_fxmacrodata_is_opt_in_and_needs_no_repository_credential():
    config = json.loads((ROOT / "mcp_config.json.example").read_text(encoding="utf-8"))
    servers = configured_servers(config)

    assert servers["fxmacrodata"] == {
        "disabled": True,
        "timeout": 600,
        "transport": "streamable_http",
        "url": "https://mcp.fxmacrodata.com",
    }
    assert "fxmacrodata" not in active_servers(servers)


def test_active_servers_supports_legacy_key_and_strips_control_fields():
    servers = configured_servers(
        {
            "servers": {
                "enabled": {"disabled": False, "transport": "http", "url": "https://example.com"},
                "disabled": {"disabled": True, "transport": "http", "url": "https://example.test"},
            }
        }
    )

    assert active_servers(servers) == {
        "enabled": {"transport": "http", "url": "https://example.com"}
    }
