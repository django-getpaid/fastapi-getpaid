.PHONY: test test-unit test-integration test-build test-down

UNIT_TESTS = \
	tests/test_config.py \
	tests/test_protocols.py \
	tests/test_public_api.py \
	tests/test_schemas.py \
	tests/test_retry.py \
	tests/test_registry.py \
	tests/test_dependencies.py \
	tests/test_router.py \
	tests/test_exceptions.py \
	tests/test_routes_payments.py \
	tests/test_routes_callbacks.py \
	tests/test_routes_redirects.py \
	tests/test_database.py

INTEGRATION_TESTS = \
	tests/test_contrib_sqlalchemy_models.py \
	tests/test_contrib_sqlalchemy_repository.py \
	tests/test_contrib_sqlalchemy_retry_store.py \
	tests/test_integration.py

test-unit:
	uv run pytest $(UNIT_TESTS) -x

test-integration: test-build
	docker compose -f compose.test.yml run --rm tests uv run pytest $(INTEGRATION_TESTS) -x

test:
	$(MAKE) test-unit
	$(MAKE) test-integration

test-build:
	docker compose -f compose.test.yml build

test-down:
	docker compose -f compose.test.yml down -v
