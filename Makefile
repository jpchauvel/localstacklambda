.PHONY: up down deploy destroy test-unit test-integration test-e2e test clean logs help

# Load .env if it exists
ifneq (,$(wildcard .env))
include .env
export
endif

# Default goal
.DEFAULT_GOAL := help

# Variables
DOCKER_CONTAINER := localstack-pubsub
HEALTH_ENDPOINT := http://localhost:4566/_localstack/health
HEALTH_TIMEOUT := 60
HEALTH_INTERVAL := 2

# up: Start LocalStack container and wait for health
up:
	@echo "Starting LocalStack container..."
	docker compose up -d
	@echo "Waiting for LocalStack to be healthy (up to $(HEALTH_TIMEOUT)s)..."
	@elapsed=0; \
	while [ $$elapsed -lt $(HEALTH_TIMEOUT) ]; do \
		if curl -s $(HEALTH_ENDPOINT) > /dev/null 2>&1; then \
			echo "✓ LocalStack is healthy"; \
			exit 0; \
		fi; \
		echo "  Waiting... ($$elapsed/$(HEALTH_TIMEOUT)s)"; \
		sleep $(HEALTH_INTERVAL); \
		elapsed=$$((elapsed + $(HEALTH_INTERVAL))); \
	done; \
	echo "✗ LocalStack failed to become healthy within $(HEALTH_TIMEOUT)s"; \
	exit 1

# down: Stop LocalStack container
down:
	@echo "Stopping LocalStack container..."
	docker compose down

# deploy: Initialize and apply Terraform configuration
deploy:
	@echo "Deploying infrastructure via Terraform..."
	cd terraform && tflocal init -upgrade && tflocal apply -auto-approve

# destroy: Destroy Terraform infrastructure
destroy:
	@echo "Destroying infrastructure via Terraform..."
	cd terraform && tflocal destroy -auto-approve || true

# test-unit: Run unit tests with coverage
test-unit:
	@echo "Running unit tests..."
	python -m pytest tests/unit -m unit -v --cov=src --cov-report=term-missing --cov-fail-under=80

# test-integration: Run integration tests
test-integration:
	@echo "Running integration tests..."
	python -m pytest tests/integration -m integration -v

# test-e2e: Run end-to-end tests
test-e2e:
	@echo "Running end-to-end tests..."
	python -m pytest tests/e2e -m e2e -v --timeout=60

# test: Run all tests (unit, integration, e2e)
test: test-unit test-integration test-e2e

# clean: Remove build artifacts, cache, and temporary files
clean:
	@echo "Cleaning up..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -f .coverage
	rm -rf terraform/.terraform
	rm -f terraform/*.tfstate*
	@echo "✓ Cleanup complete"

# logs: Stream LocalStack container logs
logs:
	docker logs -f $(DOCKER_CONTAINER)

# help: Display available targets
help:
	@echo "LocalStack Lambda PubSub - Developer Targets"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  up                 Start LocalStack container and wait for health"
	@echo "  down               Stop LocalStack container"
	@echo "  deploy             Initialize and apply Terraform configuration"
	@echo "  destroy            Destroy Terraform infrastructure"
	@echo "  test-unit          Run unit tests with coverage (80% minimum)"
	@echo "  test-integration   Run integration tests"
	@echo "  test-e2e           Run end-to-end tests with 60s timeout"
	@echo "  test               Run all tests (unit + integration + e2e)"
	@echo "  clean              Remove build artifacts and cache"
	@echo "  logs               Stream LocalStack container logs"
	@echo "  help               Display this help message"
	@echo ""
