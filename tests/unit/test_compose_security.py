from pathlib import Path

import yaml  # type: ignore[import-untyped]

REPO_ROOT = Path(__file__).resolve().parents[2]
COMPOSE_FILE = REPO_ROOT / "docker-compose.yml"


def _compose_ports(service: str) -> list[str]:
    compose = yaml.safe_load(COMPOSE_FILE.read_text(encoding="utf-8"))
    return list(compose["services"][service]["ports"])


def test_internal_data_services_bind_to_loopback_by_default() -> None:
    assert _compose_ports("postgres") == [
        "127.0.0.1:${SOURCEBRIEF_POSTGRES_PORT:-${CONTEXTSMITH_POSTGRES_PORT:-55432}}:5432"
    ]
    assert _compose_ports("redis") == [
        "127.0.0.1:${SOURCEBRIEF_REDIS_PORT:-${CONTEXTSMITH_REDIS_PORT:-6380}}:6379"
    ]


def test_external_product_services_keep_host_port_defaults() -> None:
    assert _compose_ports("api") == ["${SOURCEBRIEF_API_PORT:-${CONTEXTSMITH_API_PORT:-18000}}:8000"]
    assert _compose_ports("frontend") == ["${SOURCEBRIEF_WEB_PORT:-${CONTEXTSMITH_WEB_PORT:-13000}}:3000"]
