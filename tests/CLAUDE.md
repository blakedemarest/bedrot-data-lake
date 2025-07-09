# CLAUDE.md - Data Lake Testing Guide

This directory contains the test suite for the BEDROT Data Lake ETL pipelines. All tests are organized by service and follow pytest conventions.

## Overview

The test suite ensures data quality, pipeline reliability, and code correctness across all extractors and cleaners. Tests cover unit functionality, integration scenarios, and end-to-end pipeline validation.

## Directory Structure

```
tests/
├── conftest.py              # Pytest configuration and fixtures
├── fixtures/                # Sample data files for testing
├── distrokid/              # DistroKid pipeline tests
├── spotify/                # Spotify pipeline tests
├── tiktok/                 # TikTok pipeline tests
├── metaads/               # Meta Ads pipeline tests
├── linktree/              # Linktree pipeline tests
├── toolost/               # TooLost pipeline tests
└── test_archive_old_data.py  # Archive functionality tests
```

## Running Tests

### All Tests
```bash
cd /mnt/c/Users/Earth/BEDROT\ PRODUCTIONS/bedrot-data-ecosystem/data_lake
export PROJECT_ROOT=$(pwd)

# Run all tests with coverage
pytest -ra --cov=src --cov-report=term-missing

# Run with verbose output
pytest -v

# Run tests in parallel
pytest -n auto
```

### Service-Specific Tests
```bash
# Test single service
pytest tests/spotify/ -v

# Test specific module
pytest tests/spotify/test_spotify_audience_extractor.py -v

# Test specific function
pytest tests/spotify/test_spotify_audience_extractor.py::test_date_parsing -v
```

### Test Categories
```bash
# Only unit tests
pytest -m unit

# Only integration tests
pytest -m integration

# Exclude slow tests
pytest -m "not slow"
```

## Writing Tests

### Test Structure
Each service should have tests for:
1. **Extractors**: Mock external APIs/websites
2. **Cleaners**: Test data transformation logic
3. **End-to-end**: Full pipeline validation

### Example Test File
```python
# tests/spotify/test_spotify_landing2raw.py
import pytest
import pandas as pd
from pathlib import Path
from src.spotify.cleaners.spotify_landing2raw import (
    validate_csv_structure,
    convert_to_ndjson,
    process_landing_file
)

class TestSpotifyLanding2Raw:
    """Test cases for Spotify landing to raw conversion."""
    
    @pytest.fixture
    def sample_csv_path(self, tmp_path):
        """Create sample CSV file for testing."""
        df = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02'],
            'listeners': [1000, 1100],
            'streams': [5000, 5500]
        })
        path = tmp_path / "test_audience.csv"
        df.to_csv(path, index=False)
        return path
    
    def test_validate_csv_structure(self, sample_csv_path):
        """Test CSV validation logic."""
        assert validate_csv_structure(sample_csv_path) == True
        
    def test_missing_required_column(self, tmp_path):
        """Test handling of missing columns."""
        df = pd.DataFrame({'date': ['2024-01-01']})  # Missing 'listeners'
        path = tmp_path / "invalid.csv"
        df.to_csv(path, index=False)
        
        with pytest.raises(ValueError, match="Missing required column"):
            validate_csv_structure(path)
    
    @pytest.mark.integration
    def test_full_conversion(self, sample_csv_path, tmp_path):
        """Test complete landing to raw conversion."""
        output_path = tmp_path / "output.ndjson"
        
        process_landing_file(sample_csv_path, output_path)
        
        assert output_path.exists()
        # Verify NDJSON format
        with open(output_path) as f:
            lines = f.readlines()
        assert len(lines) == 2  # Two data rows
```

### Common Test Patterns

**Testing Data Transformations**
```python
def test_clean_numeric_field():
    """Test numeric cleaning logic."""
    assert clean_numeric("1,234") == 1234
    assert clean_numeric("$1,234.56") == 1234.56
    assert clean_numeric("N/A") is None
```

**Testing File Operations**
```python
def test_archive_file(tmp_path):
    """Test file archiving."""
    original = tmp_path / "data.csv"
    original.write_text("test data")
    
    archived = archive_file(original)
    
    assert archived.name.startswith("data_")
    assert archived.suffix == ".csv"
    assert "archive" in str(archived.parent)
```

**Testing API Interactions**
```python
@pytest.mark.vcr()  # Record/replay HTTP requests
def test_meta_api_call():
    """Test Meta API interaction."""
    response = fetch_campaign_data("act_123")
    assert response.status_code == 200
    assert "campaigns" in response.json()
```

## Test Fixtures

### Common Fixtures (conftest.py)
```python
@pytest.fixture
def project_root():
    """Return project root path."""
    return Path(__file__).parent.parent

@pytest.fixture
def sample_landing_dir(tmp_path):
    """Create temporary landing directory structure."""
    landing = tmp_path / "landing"
    for service in ["spotify", "tiktok", "distrokid"]:
        (landing / service).mkdir(parents=True)
    return landing

@pytest.fixture
def mock_browser():
    """Mock Playwright browser for testing."""
    with patch('playwright.async_api.async_playwright') as mock:
        yield mock
```

### Service-Specific Fixtures
```python
# tests/tiktok/conftest.py
@pytest.fixture
def tiktok_sample_zip(tmp_path):
    """Create sample TikTok analytics ZIP file."""
    import zipfile
    
    zip_path = tmp_path / "analytics.zip"
    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.writestr('Overview.csv', 'date,views,likes\n2024-01-01,1000,50')
    return zip_path
```

## Mocking External Dependencies

### Web Scraping
```python
@patch('playwright.async_api.Page')
async def test_spotify_login(mock_page):
    """Test Spotify login flow."""
    mock_page.goto.return_value = None
    mock_page.fill.return_value = None
    
    result = await login_to_spotify(mock_page, "user", "pass")
    
    mock_page.goto.assert_called_with("https://artists.spotify.com")
    assert result == True
```

### API Calls
```python
@patch('requests.get')
def test_fetch_data(mock_get):
    """Test API data fetching."""
    mock_get.return_value.json.return_value = {
        'data': [{'id': 1, 'value': 100}]
    }
    
    result = fetch_api_data()
    assert len(result) == 1
    assert result[0]['value'] == 100
```

## Testing Best Practices

### 1. Test Organization
- One test file per module
- Group related tests in classes
- Use descriptive test names

### 2. Test Data
- Use minimal representative data
- Store large fixtures in `tests/fixtures/`
- Generate test data programmatically when possible

### 3. Test Independence
- Each test should be independent
- Use tmp_path for file operations
- Clean up resources in teardown

### 4. Test Coverage
- Aim for 80%+ code coverage
- Test edge cases and error conditions
- Include integration tests for critical paths

## Continuous Integration

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest tests/ -x
        language: system
        pass_filenames: false
        always_run: true
```

### GitHub Actions
```yaml
# .github/workflows/test.yml
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          playwright install chromium
      - name: Run tests
        run: pytest -ra --cov=src
```

## Debugging Tests

### Running with Debugger
```bash
# Drop into debugger on failure
pytest --pdb

# Drop into debugger at specific point
import pdb; pdb.set_trace()
```

### Verbose Output
```bash
# Show print statements
pytest -s

# Show full diff on assertion failure
pytest -vv
```

### Test Isolation
```bash
# Run single test in isolation
pytest tests/spotify/test_specific.py::test_function -v --tb=short
```

## Performance Testing

### Timing Tests
```python
@pytest.mark.slow
def test_large_file_processing(benchmark):
    """Benchmark file processing performance."""
    large_df = pd.DataFrame({
        'col': range(1_000_000)
    })
    
    result = benchmark(process_dataframe, large_df)
    assert len(result) == 1_000_000
```

### Memory Testing
```python
@pytest.mark.memory
def test_memory_usage():
    """Test memory consumption stays reasonable."""
    import tracemalloc
    
    tracemalloc.start()
    process_large_dataset()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    assert peak / 1024 / 1024 < 500  # Less than 500MB
```

## Common Issues

### Import Errors
```bash
# Fix by setting PYTHONPATH
export PYTHONPATH=$PROJECT_ROOT/src:$PYTHONPATH
```

### Async Test Issues
```python
# Use pytest-asyncio
@pytest.mark.asyncio
async def test_async_function():
    result = await async_operation()
    assert result is not None
```

### Flaky Tests
```python
# Retry flaky tests
@pytest.mark.flaky(reruns=3)
def test_unstable_network_call():
    # Test that might fail due to network
    pass
```

## Test Documentation

Each test should include:
1. **Docstring**: What is being tested
2. **Arrange**: Setup test data
3. **Act**: Execute the function
4. **Assert**: Verify the result

```python
def test_example():
    """Test that widget processing handles empty input correctly."""
    # Arrange
    widget = Widget()
    empty_input = []
    
    # Act
    result = widget.process(empty_input)
    
    # Assert
    assert result == []
    assert widget.processed_count == 0
```