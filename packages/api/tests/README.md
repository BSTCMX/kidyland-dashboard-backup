# Test Suite - Kidyland API

## Structure

```
tests/
├── conftest.py              # Pytest configuration and fixtures
├── unit/                     # Unit tests (services, utilities)
│   ├── test_sale_service.py
│   ├── test_timer_service.py
│   ├── test_day_close_service.py
│   └── test_stock_service.py
└── integration/              # Integration tests (endpoints, E2E)
    ├── test_auth_endpoints.py
    ├── test_sales_endpoints.py
    ├── test_timers_endpoints.py
    ├── test_websocket.py
    ├── test_e2e_flow.py
    └── test_docker_validation.py
```

## Running Tests

### All tests
```bash
cd packages/api
pytest
```

### Unit tests only
```bash
pytest tests/unit/ -m unit
```

### Integration tests only
```bash
pytest tests/integration/ -m integration
```

### With coverage
```bash
pytest --cov=. --cov-report=html
```

### Specific test file
```bash
pytest tests/unit/test_sale_service.py
```

## Test Database

Tests use in-memory SQLite by default for speed. To use PostgreSQL for integration tests:

1. Set `TEST_DATABASE_URL` in `conftest.py`
2. Ensure test database exists: `createdb kidyland_test`
3. Run integration tests: `pytest -m integration`

## Markers

- `@pytest.mark.unit`: Fast unit tests
- `@pytest.mark.integration`: Integration tests (require database)
- `@pytest.mark.slow`: Slow tests (Docker builds, etc.)
- `@pytest.mark.websocket`: WebSocket-specific tests

## Fixtures

- `test_db`: Async database session (in-memory SQLite)
- `test_user`: Test user (recepcion role)
- `test_superadmin`: Super admin user
- `test_sucursal`: Test sucursal
- `test_service`: Test service
- `test_product`: Test product
































