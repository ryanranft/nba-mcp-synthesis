# Test Best Practices

**NBA MCP Synthesis - Testing Best Practices Guide**
**Last Updated**: 2025-10-24
**Version**: 1.0

---

## Table of Contents

1. [Writing Effective Tests](#writing-effective-tests)
2. [Test Organization](#test-organization)
3. [Async Testing Patterns](#async-testing-patterns)
4. [Fixture Design](#fixture-design)
5. [Mocking Best Practices](#mocking-best-practices)
6. [Performance Optimization](#performance-optimization)
7. [Test Maintenance](#test-maintenance)

---

## Writing Effective Tests

### 1. Test Structure: Arrange-Act-Assert

```python
def test_player_stats_calculation():
    # Arrange: Set up test data
    player = Player(name="LeBron James")
    games = [Game(points=25, assists=7, rebounds=8) for _ in range(5)]

    # Act: Execute the function being tested
    stats = player.calculate_season_stats(games)

    # Assert: Verify the results
    assert stats.avg_points == 25.0
    assert stats.avg_assists == 7.0
    assert stats.avg_rebounds == 8.0
```

### 2. Descriptive Test Names

```python
# Good ✅
def test_concurrent_database_queries_dont_cause_deadlocks():
    ...

def test_missing_api_key_raises_authentication_error():
    ...

def test_formula_extraction_handles_malformed_latex():
    ...

# Bad ❌
def test_db():
    ...

def test_auth():
    ...

def test_formula():
    ...
```

### 3. One Concept Per Test

```python
# Good ✅
def test_user_registration_creates_new_user():
    user = register_user("test@example.com")
    assert user.email == "test@example.com"

def test_user_registration_sends_confirmation_email():
    register_user("test@example.com")
    assert email_was_sent_to("test@example.com")

# Bad ❌
def test_user_registration():
    user = register_user("test@example.com")
    assert user.email == "test@example.com"
    assert email_was_sent_to("test@example.com")
    assert user.is_active is False
    assert user.created_at is not None
```

### 4. Clear Assertions with Messages

```python
# Good ✅
assert result.status == "success", \
    f"Expected success but got {result.status}. Error: {result.error}"

assert len(users) == 5, \
    f"Expected 5 users but got {len(users)}"

# Bad ❌
assert result.status == "success"
assert len(users) == 5
```

---

## Test Organization

### 1. File Structure

```
tests/
├── unit/                  # Fast, isolated tests
│   ├── test_models.py
│   ├── test_utils.py
│   └── test_calculations.py
│
├── integration/           # Tests with external dependencies
│   ├── test_database.py
│   ├── test_api_clients.py
│   └── test_file_operations.py
│
├── e2e/                   # End-to-end workflows
│   ├── test_workflows.py
│   └── test_deployments.py
│
├── conftest.py            # Shared fixtures
└── fixtures/              # Test data
    ├── sample_books.json
    └── test_configs.yaml
```

### 2. Fixture Organization (conftest.py)

```python
# tests/conftest.py

import pytest
import pytest_asyncio
from pathlib import Path

# ============= Session-level Fixtures =============

@pytest.fixture(scope="session")
def test_data_dir():
    """Path to test data directory"""
    return Path(__file__).parent / "fixtures"

@pytest.fixture(scope="session")
def database_url():
    """Test database URL"""
    return "postgresql://test:test@localhost:5432/test_db"

# ============= Module-level Fixtures =============

@pytest.fixture(scope="module")
def sample_book_data(test_data_dir):
    """Load sample book data"""
    import json
    with open(test_data_dir / "sample_books.json") as f:
        return json.load(f)

# ============= Function-level Fixtures =============

@pytest.fixture
def temp_directory(tmp_path):
    """Clean temporary directory for each test"""
    yield tmp_path
    # Cleanup happens automatically

@pytest.fixture
def mock_mcp_server():
    """Mock MCP server for testing"""
    from tests.mocks import MockMCPServer
    server = MockMCPServer()
    yield server
    server.cleanup()

# ============= Async Fixtures =============

@pytest_asyncio.fixture
async def async_client():
    """Async test client"""
    client = AsyncClient()
    await client.connect()
    yield client
    await client.disconnect()
```

### 3. Test Class Organization

```python
class TestPlayerStatistics:
    """Test suite for player statistics calculations"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup run before each test in this class"""
        self.player = Player("Test Player")
        yield
        # Teardown code here if needed

    def test_calculate_ppg(self):
        """Test points per game calculation"""
        assert self.player.calculate_ppg([20, 25, 30]) == 25.0

    def test_calculate_efficiency_rating(self):
        """Test efficiency rating calculation"""
        stats = {"pts": 20, "reb": 5, "ast": 5}
        assert self.player.calculate_efficiency(stats) > 15.0

    @pytest.mark.slow
    def test_season_trend_analysis(self):
        """Test season-long trend analysis"""
        # Longer-running test
        ...
```

---

## Async Testing Patterns

### 1. Async Test Functions

```python
import pytest

# Correct ✅
@pytest.mark.asyncio
async def test_async_database_query():
    result = await db.query("SELECT * FROM players")
    assert len(result) > 0

# Wrong ❌ - Missing @pytest.mark.asyncio
async def test_async_function():
    ...
```

### 2. Async Fixtures

```python
import pytest_asyncio

# Correct ✅
@pytest_asyncio.fixture
async def async_db_connection():
    connection = await create_connection()
    yield connection
    await connection.close()

# Wrong ❌ - Using @pytest.fixture for async
@pytest.fixture
async def async_db_connection():
    ...
```

### 3. Testing Async Context Managers

```python
@pytest.mark.asyncio
async def test_async_context_manager():
    async with AsyncResource() as resource:
        result = await resource.do_something()
        assert result is not None
```

### 4. Testing Concurrent Operations

```python
import asyncio

@pytest.mark.asyncio
async def test_concurrent_requests_dont_interfere():
    # Create multiple concurrent tasks
    tasks = [
        fetch_data(i)
        for i in range(10)
    ]

    # Run concurrently
    results = await asyncio.gather(*tasks)

    # Verify no interference
    assert len(results) == 10
    assert len(set(results)) == 10  # All unique
```

---

## Fixture Design

### 1. Fixture Scopes

```python
# Session scope - Created once per test session
@pytest.fixture(scope="session")
def database_engine():
    engine = create_engine("postgresql://...")
    yield engine
    engine.dispose()

# Module scope - Created once per test module
@pytest.fixture(scope="module")
def api_client():
    client = APIClient()
    yield client
    client.cleanup()

# Function scope (default) - Created for each test
@pytest.fixture
def clean_database(database_engine):
    # Reset database for each test
    reset_tables(database_engine)
    yield database_engine
```

### 2. Fixture Dependencies

```python
@pytest.fixture
def database():
    return create_database()

@pytest.fixture
def user_repository(database):
    return UserRepository(database)

@pytest.fixture
def auth_service(user_repository):
    return AuthService(user_repository)

def test_user_authentication(auth_service):
    # auth_service automatically gets database and user_repository
    result = auth_service.login("user", "pass")
    assert result.success
```

### 3. Fixture Autouse

```python
@pytest.fixture(autouse=True)
def setup_logging():
    """Automatically configure logging for all tests"""
    logging.basicConfig(level=logging.DEBUG)
    yield
    # Cleanup logging handlers

@pytest.fixture(autouse=True, scope="function")
def isolate_test_environment(monkeypatch):
    """Isolate each test's environment variables"""
    # monkeypatch cleans up automatically after each test
    monkeypatch.setenv("TEST_MODE", "true")
```

### 4. Parametrized Fixtures

```python
@pytest.fixture(params=["sqlite", "postgresql", "mysql"])
def database_type(request):
    """Run tests with different database types"""
    return request.param

def test_query_execution(database_type):
    # This test runs 3 times, once for each database type
    db = create_database(database_type)
    result = db.query("SELECT 1")
    assert result is not None
```

---

## Mocking Best Practices

### 1. Mock External Services

```python
from unittest.mock import Mock, patch, AsyncMock

def test_fetch_player_data_from_api():
    # Mock external API call
    with patch('api.client.requests.get') as mock_get:
        mock_get.return_value.json.return_value = {
            "name": "LeBron James",
            "points": 25
        }

        result = fetch_player_data("lebron-james")

        assert result["name"] == "LeBron James"
        mock_get.assert_called_once_with("/players/lebron-james")
```

### 2. Mock Async Functions

```python
@pytest.mark.asyncio
async def test_async_api_call():
    with patch('api.async_client.fetch', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = {"data": "test"}

        result = await call_api()

        assert result["data"] == "test"
        mock_fetch.assert_awaited_once()
```

### 3. Mock File Operations

```python
from unittest.mock import mock_open, patch

def test_read_config_file():
    mock_data = "config_value=123"

    with patch("builtins.open", mock_open(read_data=mock_data)):
        config = load_config("config.txt")

        assert config["config_value"] == "123"
```

### 4. Mock Environment Variables

```python
def test_environment_dependent_code(monkeypatch):
    # monkeypatch is a pytest fixture
    monkeypatch.setenv("API_KEY", "test_key")
    monkeypatch.setenv("DEBUG", "true")

    result = get_api_client()

    assert result.api_key == "test_key"
    assert result.debug is True
```

### 5. Spy vs Mock vs Stub

```python
# Spy - Calls real method, records calls
from unittest.mock import MagicMock

def test_with_spy():
    obj = RealClass()
    obj.method = MagicMock(side_effect=obj.method)  # Spy

    result = obj.method(1, 2)

    assert result == 3  # Real result
    obj.method.assert_called_once_with(1, 2)  # Call recorded

# Mock - Replaces behavior completely
def test_with_mock():
    obj = MagicMock()
    obj.method.return_value = 42

    result = obj.method(1, 2)

    assert result == 42

# Stub - Simple replacement
def test_with_stub():
    def stub_method():
        return "stubbed"

    obj.method = stub_method
    assert obj.method() == "stubbed"
```

---

## Performance Optimization

### 1. Parallel Test Execution

```bash
# Run with pytest-xdist
pytest tests/ -n auto        # Auto-detect CPU count
pytest tests/ -n 8           # Use 8 workers
pytest tests/ -n logical     # One worker per logical CPU
```

```python
# Mark tests for isolation if needed
@pytest.mark.isolation
def test_requires_isolation():
    # This test shouldn't run in parallel
    ...
```

### 2. Mark Slow Tests

```python
# Mark slow tests
@pytest.mark.slow
def test_comprehensive_analysis():
    # Long-running test
    ...

# Skip slow tests during development
pytest tests/ -m "not slow"
```

### 3. Lazy Fixtures

```python
# Bad ❌ - Always creates database even if not needed
@pytest.fixture
def database():
    return create_expensive_database()  # Always runs

# Good ✅ - Lazy evaluation
@pytest.fixture
def database(request):
    _db = None

    def _create_db():
        nonlocal _db
        if _db is None:
            _db = create_expensive_database()
        return _db

    return _create_db

def test_something(database):
    db = database()  # Only created when called
```

### 4. Test Data Management

```python
# Bad ❌ - Loading large data in fixture
@pytest.fixture
def all_players():
    return load_all_players()  # 10,000 players

# Good ✅ - Load only what's needed
@pytest.fixture
def sample_players():
    return load_players(limit=10)

@pytest.mark.slow
def test_with_full_dataset(all_players):
    # Only tests that need it use the large dataset
    ...
```

---

## Test Maintenance

### 1. Keep Tests DRY (Don't Repeat Yourself)

```python
# Bad ❌
def test_user_creation():
    user = User(name="Test", email="test@example.com", age=25)
    assert user.name == "Test"

def test_user_validation():
    user = User(name="Test", email="test@example.com", age=25)
    assert user.is_valid()

# Good ✅
@pytest.fixture
def sample_user():
    return User(name="Test", email="test@example.com", age=25)

def test_user_creation(sample_user):
    assert sample_user.name == "Test"

def test_user_validation(sample_user):
    assert sample_user.is_valid()
```

### 2. Refactor Test Code Like Production Code

```python
# Helper functions for common operations
def create_test_player(name="Test Player", **kwargs):
    """Create a test player with sensible defaults"""
    defaults = {
        "position": "F",
        "team": "Test Team",
        "jersey_number": 23
    }
    defaults.update(kwargs)
    return Player(name=name, **defaults)

# Use helpers in tests
def test_player_statistics():
    player = create_test_player(name="LeBron")
    # Test logic...
```

### 3. Test Data Builders

```python
class PlayerBuilder:
    """Builder pattern for test player data"""

    def __init__(self):
        self._name = "Test Player"
        self._position = "F"
        self._stats = {}

    def with_name(self, name):
        self._name = name
        return self

    def with_position(self, position):
        self._position = position
        return self

    def with_stats(self, **stats):
        self._stats = stats
        return self

    def build(self):
        return Player(
            name=self._name,
            position=self._position,
            stats=self._stats
        )

# Usage in tests
def test_forward_statistics():
    player = (PlayerBuilder()
              .with_name("LeBron")
              .with_position("F")
              .with_stats(points=27, assists=7)
              .build())

    assert player.is_forward()
```

### 4. Parameterized Tests

```python
@pytest.mark.parametrize("input,expected", [
    (0, 0),
    (1, 1),
    (2, 4),
    (3, 9),
    (4, 16),
])
def test_square(input, expected):
    assert square(input) == expected

# Multiple parameters
@pytest.mark.parametrize("player_name,position,expected_role", [
    ("LeBron James", "F", "Forward"),
    ("Stephen Curry", "G", "Guard"),
    ("Anthony Davis", "C", "Center"),
])
def test_player_role(player_name, position, expected_role):
    player = Player(player_name, position)
    assert player.role == expected_role
```

---

## Common Pitfalls to Avoid

### 1. Testing Implementation Instead of Behavior

```python
# Bad ❌ - Tests implementation details
def test_sorting_uses_quicksort():
    assert sorter.algorithm == "quicksort"

# Good ✅ - Tests behavior
def test_sorting_returns_sorted_list():
    result = sort([3, 1, 2])
    assert result == [1, 2, 3]
```

### 2. Tests Depending on Each Other

```python
# Bad ❌
def test_01_create_user():
    global created_user
    created_user = create_user("test")

def test_02_update_user():
    # Depends on test_01 running first
    update_user(created_user, name="updated")

# Good ✅
@pytest.fixture
def created_user():
    return create_user("test")

def test_create_user(created_user):
    assert created_user.name == "test"

def test_update_user(created_user):
    update_user(created_user, name="updated")
    assert created_user.name == "updated"
```

### 3. Ignoring Test Failures

```python
# Bad ❌
@pytest.mark.skip("Fails sometimes")
def test_flaky_feature():
    ...

# Good ✅ - Fix the flakiness
def test_stable_feature():
    # Add proper waits, mocks, or retries
    ...
```

---

## Testing Checklist

Before merging code, ensure:

- [ ] All tests pass
- [ ] New code has tests
- [ ] Tests are independent
- [ ] Tests are fast (< 100ms for unit tests)
- [ ] Test names are descriptive
- [ ] Async fixtures use `@pytest_asyncio.fixture`
- [ ] External services are mocked
- [ ] No hardcoded credentials
- [ ] Coverage meets threshold (> 90%)
- [ ] No flaky tests

---

## Additional Resources

- [Testing Guide](./TESTING_GUIDE.md) - Comprehensive testing guide
- [CI/CD Testing Guide](./CI_CD_TESTING_GUIDE.md) - CI/CD integration
- [pytest Documentation](https://docs.pytest.org/)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)

---

**Last Updated**: 2025-10-24
**Maintainer**: NBA MCP Synthesis Team
**Version**: 1.0
