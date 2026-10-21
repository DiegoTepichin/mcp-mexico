import json
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parent.parent


def load_server_json() -> dict[str, Any]:
    server: dict[str, Any] = json.loads((ROOT / "server.json").read_text())
    return server


def test_server_json_matches_package_version() -> None:
    version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    server = load_server_json()
    assert server["version"] == version
    assert [package["version"] for package in server["packages"]] == [version]


def test_readme_declares_registry_name() -> None:
    name = load_server_json()["name"]
    assert f"<!-- mcp-name: {name} -->" in (ROOT / "README.md").read_text()
