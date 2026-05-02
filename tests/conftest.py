"""Shared pytest fixtures for LocalStack integration tests."""

import json
import os
import subprocess
from pathlib import Path

import boto3
import pytest
import redis


@pytest.fixture(scope="session")
def localstack_endpoint():
    """Return LocalStack endpoint URL."""
    return os.environ.get("AWS_ENDPOINT_URL", "http://localhost:4566")


@pytest.fixture(scope="session")
def aws_creds():
    """Set AWS credentials for LocalStack testing."""
    # Set credentials if not already set
    os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
    os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")
    os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
    yield
    # Cleanup is optional; credentials remain for session


@pytest.fixture(scope="session")
def events_client(localstack_endpoint, aws_creds):
    """Return boto3 EventBridge client connected to LocalStack."""
    return boto3.client(
        "events",
        endpoint_url=localstack_endpoint,
        region_name="us-east-1",
    )


@pytest.fixture(scope="session")
def lambda_client(localstack_endpoint, aws_creds):
    """Return boto3 Lambda client connected to LocalStack."""
    return boto3.client(
        "lambda",
        endpoint_url=localstack_endpoint,
        region_name="us-east-1",
    )


@pytest.fixture(scope="session")
def logs_client(localstack_endpoint, aws_creds):
    """Return boto3 CloudWatch Logs client connected to LocalStack."""
    return boto3.client(
        "logs",
        endpoint_url=localstack_endpoint,
        region_name="us-east-1",
    )


@pytest.fixture(scope="session")
def apigw_client(localstack_endpoint, aws_creds):
    """Return boto3 API Gateway v2 client connected to LocalStack."""
    return boto3.client(
        "apigatewayv2",
        endpoint_url=localstack_endpoint,
        region_name="us-east-1",
    )


@pytest.fixture(scope="session")
def elasticache_client(localstack_endpoint, aws_creds):
    """Return boto3 ElastiCache client connected to LocalStack."""
    return boto3.client(
        "elasticache",
        endpoint_url=localstack_endpoint,
        region_name="us-east-1",
    )


@pytest.fixture(scope="session")
def redis_client():
    """Return redis.Redis client for LocalStack Redis."""
    redis_host = os.environ.get("LOCALSTACK_REDIS_HOST")
    if not redis_host:
        pytest.skip("LOCALSTACK_REDIS_HOST not set")

    redis_port = int(os.environ.get("LOCALSTACK_REDIS_PORT", "6379"))
    return redis.Redis(
        host=redis_host,
        port=redis_port,
        decode_responses=True,
    )


@pytest.fixture(scope="session")
def terraform_outputs():
    """Return parsed Terraform outputs from LocalStack deployment."""
    tfstate_path = Path("terraform/terraform.tfstate")
    if not tfstate_path.exists():
        pytest.skip("terraform/terraform.tfstate not found")

    result = subprocess.run(
        ["tflocal", "output", "-json"],
        cwd="terraform",
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        pytest.skip(f"tflocal output failed: {result.stderr}")

    return json.loads(result.stdout)


@pytest.fixture(scope="session")
def api_endpoint(terraform_outputs):
    """Return API Gateway invoke URL from Terraform outputs."""
    try:
        return terraform_outputs["invoke_url"]["value"]
    except KeyError:
        pytest.skip("invoke_url not found in Terraform outputs")


def pytest_collection_modifyitems(config, items):
    """Auto-apply pytest markers based on test file location."""
    for item in items:
        # Get the relative path from the test file
        fspath = str(item.fspath)

        # Check for marker-specific directories
        if "/unit/" in fspath or "\\unit\\" in fspath:
            item.add_marker(pytest.mark.unit)
        elif "/integration/" in fspath or "\\integration\\" in fspath:
            item.add_marker(pytest.mark.integration)
        elif "/e2e/" in fspath or "\\e2e\\" in fspath:
            item.add_marker(pytest.mark.e2e)
