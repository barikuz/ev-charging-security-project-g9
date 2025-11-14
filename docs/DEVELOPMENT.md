# Development Guide

## Project Structure

```
EV/
├── src/                          # Source code
│   ├── __init__.py
│   ├── can_bus/                 # CAN bus simulator
│   │   ├── __init__.py
│   │   └── simulator.py
│   ├── ocpp/                    # OCPP protocol
│   │   ├── __init__.py
│   │   └── protocol.py
│   ├── v2g/                     # V2G communication
│   │   ├── __init__.py
│   │   └── communicator.py
│   ├── simulator/               # Main simulator
│   │   ├── __init__.py
│   │   └── main.py
│   └── anomalies/               # Anomaly injection
│       ├── __init__.py
│       └── injector.py
├── tests/                        # Test suite
│   ├── conftest.py
│   ├── test_can_bus.py
│   ├── test_ocpp.py
│   ├── test_v2g.py
│   ├── test_anomalies.py
│   └── test_simulator.py
├── configs/                      # Configuration files
│   ├── can_bus_config.yaml
│   ├── ocpp_config.yaml
│   ├── v2g_config.yaml
│   ├── anomalies_config.yaml
│   └── simulator_config.yaml
├── docs/                         # Documentation
│   ├── API.md
│   ├── USAGE.md
│   └── DEVELOPMENT.md
├── logs/                         # Application logs
├── requirements.txt              # Python dependencies
├── pyproject.toml               # Project metadata
├── README.md                    # Project README
└── .gitignore                   # Git ignore rules
```

## Development Workflow

### Setting Up Development Environment

1. **Clone and setup**
   ```bash
   git clone <repo>
   cd EV
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Install development dependencies**
   ```bash
   pip install black flake8 mypy pylint
   ```

3. **Code style**
   - Follow PEP 8
   - Use Black for formatting: `black src/ tests/`
   - Check with Flake8: `flake8 src/ tests/`

### Adding New Features

1. **Create feature branch**
   ```bash
   git checkout -b feature/new-feature
   ```

2. **Implement feature with tests**
   ```bash
   # Add code to src/
   # Add tests to tests/
   # Run tests: pytest tests/
   ```

3. **Run all checks**
   ```bash
   pytest tests/ -v --cov=src
   black src/ tests/
   flake8 src/ tests/
   ```

4. **Commit and push**
   ```bash
   git add .
   git commit -m "Add new feature"
   git push origin feature/new-feature
   ```

### Test Development

#### Test Structure
```python
import pytest
from src.module import Component

@pytest.fixture
def component():
    """Fixture for component setup"""
    return Component()

def test_feature(component):
    """Test description"""
    result = component.method()
    assert result is True
```

#### Running Tests
```bash
# Run all tests
pytest tests/

# Run specific file
pytest tests/test_can_bus.py

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test
pytest tests/test_can_bus.py::test_can_message_creation

# Run with verbose output
pytest tests/ -v -s
```

#### Async Test Example
```python
@pytest.mark.asyncio
async def test_async_operation():
    simulator = EVChargingSimulator()
    await simulator.start()
    assert simulator.running is True
    await simulator.stop()
```

### Adding New Protocol/Component

1. **Create module file** in appropriate package
2. **Implement classes** with type hints
3. **Create tests** in `tests/` directory
4. **Update __init__.py** for exports
5. **Add configuration** if needed
6. **Document** in API.md and USAGE.md

### Configuration Management

1. **Global settings**: `configs/simulator_config.yaml`
2. **Component settings**: `configs/<component>_config.yaml`
3. **Loading configuration**:
   ```python
   from src.simulator.main import EVChargingSimulator
   sim = EVChargingSimulator(config_path='configs/custom.yaml')
   ```

## Code Style Guidelines

### Naming Conventions
- Classes: `PascalCase` (e.g., `CANBusSimulator`)
- Functions/methods: `snake_case` (e.g., `send_message`)
- Constants: `UPPER_SNAKE_CASE`
- Private: prefix with `_` (e.g., `_internal_method`)

### Type Hints
```python
from typing import Dict, Optional, List, Any

def process_message(
    message: Dict[str, Any],
    timeout: Optional[float] = None
) -> bool:
    """Process a message."""
    pass
```

### Docstrings
```python
def send_message(self, message: CANMessage) -> bool:
    """Send a CAN message to the bus.
    
    Args:
        message: The CAN message to send
        
    Returns:
        True if sent successfully, False otherwise
        
    Raises:
        ValueError: If message is invalid
    """
    pass
```

### Async Code
```python
async def async_operation(self) -> None:
    """Perform async operation."""
    await asyncio.sleep(1)
    await self.process()
```

## Logging

Use module-level logger:
```python
import logging

logger = logging.getLogger(__name__)

logger.info("Operation started")
logger.warning("Potential issue")
logger.error("Error occurred")
logger.debug("Debug information")
```

## Performance Optimization

### Profiling
```bash
pip install cProfile
python -m cProfile -s cumulative -m src.simulator.main
```

### Memory Usage
```bash
pip install memory_profiler
python -m memory_profiler src/simulator/main.py
```

## Debugging Techniques

### Using Python Debugger
```python
import pdb; pdb.set_trace()
```

### VS Code Debugging
- Set breakpoints (click line number)
- F5 to start debugger
- F10 to step
- F11 to step into
- Shift+F11 to step out

### Async Debugging
```python
import asyncio
asyncio.set_debug(True)
```

## Continuous Integration

### GitHub Actions Example
```yaml
name: Tests
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v --cov=src
```

## Building and Packaging

### Build distribution
```bash
python -m build
```

### Upload to PyPI
```bash
python -m twine upload dist/*
```

## Common Tasks

### Adding Dependency
```bash
pip install package-name
pip freeze > requirements.txt
```

### Updating Tests
```bash
pytest tests/ -k "pattern" -v
```

### Generate API Docs
```bash
pip install sphinx
sphinx-quickstart docs
```

## Troubleshooting Development

### Import Issues
```python
# Ensure __init__.py exists in all packages
# Use absolute imports from project root
from src.module.component import Class
```

### Async Issues
- Always use `await` for async functions
- Run tests with pytest-asyncio
- Use `asyncio.run()` in main

### Type Checking
```bash
mypy src/ --ignore-missing-imports
```

## Contributing Code

1. Follow style guide
2. Add tests for new code
3. Update documentation
4. Run full test suite
5. Create descriptive commit message
6. Push to feature branch
7. Create pull request with description

## Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Run full test suite
4. Tag release: `git tag v0.1.0`
5. Push tags: `git push --tags`
6. Create GitHub release with notes
