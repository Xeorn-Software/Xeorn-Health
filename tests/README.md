# RWANA Health App Tests

This directory contains tests for the RWANA Health Voice Assistant application.

## Test Structure

The tests are organized as follows:

- `conftest.py` - Contains pytest fixtures used across test files
- `test_utils.py` - Tests for utility functions (translation, LLM responses, etc.)
- `test_routes.py` - Tests for Flask routes and API endpoints
- `test_frontend.py` - Tests for the HTML/JS frontend components

## Running Tests

To run the tests, first install the test requirements:

```bash
pip install -r test_requirements.txt
```

Then run pytest from the root directory:

```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=app

# Run specific test file
pytest tests/test_utils.py

# Run tests matching a specific name
pytest -k "test_clean_markdown"
```

## Test Coverage

The tests cover the following aspects of the application:

1. **Backend Functionality**
   - Utility functions (translation, LLM responses, etc.)
   - Error handling
   - Session management

2. **API Endpoints**
   - Text processing endpoint
   - Audio processing endpoint
   - SMS notification endpoint
   - Health tracking endpoints
   - Appointment management endpoints

3. **Frontend**
   - HTML structure
   - JavaScript event handlers
   - Responsive design elements

## Adding New Tests

When adding new tests:

1. Place them in the appropriate test file based on functionality
2. Follow the naming convention `test_*` for test functions
3. Use the existing fixtures defined in `conftest.py`
4. Use mocking for external dependencies (APIs, etc.)

## Debugging Tests

If a test fails, you can run it with more verbose output:

```bash
pytest tests/test_file.py::test_function -v
```

For more detailed debugging, you can use the `--pdb` flag to drop into the debugger when a test fails:

```bash
pytest tests/test_file.py::test_function --pdb
```
