from sourcebrief_shared.graph_index import _service_endpoints


def _by_kind(items: list[dict[str, str]]) -> dict[str, set[tuple[str, str]]]:
    grouped: dict[str, set[tuple[str, str]]] = {}
    for item in items:
        grouped.setdefault(item["matcher_type"], set()).add((item["handle"], item["role"]))
    return grouped


def test_service_endpoint_extraction_covers_supported_matchers() -> None:
    content = """
@app.get('/v1/orders')
def list_orders():
    return []
fetch('/v1/orders')
topic: 'orders.created'
query GetOrders { orders { id } }
OrderService.GetOrder
trpc.order.get.useQuery()
"""

    grouped = _by_kind(_service_endpoints("src/api.py", content))

    assert grouped["http_route"] == {("/v1/orders", "server"), ("/v1/orders", "client")}
    assert grouped["async_topic"] == {("orders.created", "producer_or_consumer")}
    assert grouped["graphql_operation"] == {("GetOrders", "operation")}
    assert grouped["grpc_method"] == {("OrderService.GetOrder", "caller")}
    assert grouped["trpc_route"] == {("order.get", "caller")}


def test_service_endpoint_extraction_deduplicates_same_file_matches() -> None:
    content = "fetch('/v1/orders')\nfetch('/v1/orders')\n"

    endpoints = _service_endpoints("src/client.ts", content)

    assert endpoints == [
        {"matcher_type": "http_route", "role": "client", "handle": "/v1/orders", "path": "src/client.ts"}
    ]
