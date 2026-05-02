## Overview
LocalStack Lambda pubsub system using Producer Lambda, EventBridge (custom bus), Consumer Lambda, and Redis (ElastiCache) for idempotency. The entire stack is deployed to LocalStack Pro using Terraform.

## Architecture diagram
```
Client → API Gateway HTTP API → Producer Lambda → EventBridge (orders-bus)
                                                        ↓
                                                 Consumer Lambda → Redis (SET NX)
```

## Prerequisites
- Docker
- LocalStack Pro auth token (required for ElastiCache)
- Python >=3.14
- Terraform >=1.9
- `pip install terraform-local`

## Setup
```bash
# Set up environment variables
cp .env.example .env

# Install dependencies
pip install -e ".[dev]"

# Start LocalStack Pro
make up

# Deploy infrastructure
make deploy
```

## Test commands
```bash
make test-unit         # Fast unit tests (offline)
make test-integration  # Integration tests (requires LocalStack)
make test-e2e          # End-to-end flow validation
make test              # Run all test suites
```

## Try it
```bash
INVOKE_URL=$(cd terraform && tflocal output -raw invoke_url)

curl -X POST "$INVOKE_URL" \
  -H 'Content-Type: application/json' \
  -d '{
    "order_id": "o-1",
    "customer_id": "c1",
    "amount": "99.99",
    "currency": "USD",
    "items": [
      {
        "sku": "s1",
        "quantity": 1,
        "unit_price": "99.99"
      }
    ]
  }'
```

## Project structure
```
.
├── docker-compose.yml
├── Makefile
├── pyproject.toml
├── README.md
├── src/
├── terraform/
└── tests/
```

## Teardown
```bash
make destroy
make down
```

## Limitations
- Local-only: Designed for LocalStack Pro; not intended for AWS deployment
- Development-grade: No Dead Letter Queues (DLQ), authentication, or CI/CD pipelines
- Ephemeral storage: Single-node Redis cluster with no persistence
