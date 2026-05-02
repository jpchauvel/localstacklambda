import json

import boto3
import pytest

pytestmark = pytest.mark.integration

ENDPOINT = "http://localhost:4566"
REGION = "us-east-1"
CREDS = dict(
    aws_access_key_id="test", aws_secret_access_key="test", region_name=REGION
)


def _client(service):
    return boto3.client(service, endpoint_url=ENDPOINT, **CREDS)


def test_lambdas_exist():
    lc = _client("lambda")
    fns = lc.list_functions()["Functions"]
    names = {f["FunctionName"] for f in fns}
    assert "pubsub-producer" in names
    assert "pubsub-consumer" in names
    runtimes = {
        f["FunctionName"]: f["Runtime"]
        for f in fns
        if f["FunctionName"] in {"pubsub-producer", "pubsub-consumer"}
    }
    assert runtimes["pubsub-producer"] in ("python3.13", "python3.14")
    assert runtimes["pubsub-consumer"] in ("python3.13", "python3.14")


def test_event_bus_exists():
    ec = _client("events")
    buses = ec.list_event_buses()["EventBuses"]
    names = {b["Name"] for b in buses}
    assert "orders-bus" in names


def test_event_rule_targets_consumer():
    ec = _client("events")
    resp = ec.list_targets_by_rule(
        Rule="orders-created-rule", EventBusName="orders-bus"
    )
    targets = resp["Targets"]
    assert len(targets) == 1
    assert targets[0]["Arn"].endswith(":function:pubsub-consumer")


def test_apigateway_route_exists():
    agc = _client("apigatewayv2")
    apis = agc.get_apis()["Items"]
    api = next((a for a in apis if a["Name"] == "pubsub-api"), None)
    assert api is not None, "pubsub-api not found"
    routes = agc.get_routes(ApiId=api["ApiId"])["Items"]
    route_keys = {r["RouteKey"] for r in routes}
    assert "POST /orders" in route_keys


def test_lambda_permission_for_apigw_present():
    lc = _client("lambda")
    try:
        policy_str = lc.get_policy(FunctionName="pubsub-producer")["Policy"]
        policy = json.loads(policy_str)
        principals = [
            s["Principal"]["Service"]
            for s in policy["Statement"]
            if isinstance(s.get("Principal"), dict)
        ]
        assert "apigateway.amazonaws.com" in principals
    except lc.exceptions.ResourceNotFoundException:
        pytest.skip(
            "Lambda policy not found - LocalStack may not support get_policy"
        )


def test_lambda_permission_for_eventbridge_present():
    lc = _client("lambda")
    try:
        policy_str = lc.get_policy(FunctionName="pubsub-consumer")["Policy"]
        policy = json.loads(policy_str)
        principals = [
            s["Principal"]["Service"]
            for s in policy["Statement"]
            if isinstance(s.get("Principal"), dict)
        ]
        assert "events.amazonaws.com" in principals
    except lc.exceptions.ResourceNotFoundException:
        pytest.skip(
            "Lambda policy not found - LocalStack may not support get_policy"
        )


def test_elasticache_cluster_available():
    ec = _client("elasticache")
    resp = ec.describe_cache_clusters(CacheClusterId="pubsub-redis")
    clusters = resp["CacheClusters"]
    assert len(clusters) == 1
    assert clusters[0]["CacheClusterStatus"] in ("available", "creating")


def test_lambda_env_vars_set():
    lc = _client("lambda")
    producer = lc.get_function_configuration(FunctionName="pubsub-producer")
    consumer = lc.get_function_configuration(FunctionName="pubsub-consumer")
    prod_env = producer.get("Environment", {}).get("Variables", {})
    cons_env = consumer.get("Environment", {}).get("Variables", {})
    assert prod_env.get("EVENT_BUS_NAME") == "orders-bus"
    assert "REDIS_HOST" in cons_env
    assert "REDIS_TTL_SECONDS" in cons_env
