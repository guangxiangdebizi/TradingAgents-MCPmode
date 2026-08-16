"""Helpers for normalizing the repository's MCP server configuration."""

from typing import Any, Dict, Mapping


def configured_servers(config: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Return the configured server map, accepting the legacy key as fallback."""
    servers = config.get("mcpServers")
    if servers is None:
        servers = config.get("servers", {})
    if not isinstance(servers, Mapping):
        return {}
    return {
        str(name): dict(server)
        for name, server in servers.items()
        if isinstance(server, Mapping)
    }


def active_servers(servers: Mapping[str, Mapping[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Remove disabled servers and fields not accepted by the MCP client."""
    active: Dict[str, Dict[str, Any]] = {}
    for name, server in servers.items():
        if server.get("disabled", False):
            continue
        active[str(name)] = {
            key: value for key, value in server.items() if key != "disabled"
        }
    return active
