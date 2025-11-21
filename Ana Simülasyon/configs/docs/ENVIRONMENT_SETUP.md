# Environment Setup Instructions

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment support

Verify Python version:
```bash
python --version
```

---

## Windows Setup

### 1. Create Virtual Environment
```bash
python -m venv venv
```

### 2. Activate Virtual Environment
```bash
venv\Scripts\activate
```

You should see `(venv)` prefix in your terminal.

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Verify Installation
```bash
python -m src.simulator.main
```

---

## Linux/macOS Setup

### 1. Create Virtual Environment
```bash
python3 -m venv venv
```

### 2. Activate Virtual Environment
```bash
source venv/bin/activate
```

You should see `(venv)` prefix in your terminal.

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Verify Installation
```bash
python -m src.simulator.main
```

---

## VS Code Setup

### 1. Select Python Interpreter
- Press `Ctrl+Shift+P`
- Type "Python: Select Interpreter"
- Choose the one in `./venv/Scripts/python.exe` (Windows)
- Or `./venv/bin/python` (Linux/macOS)

### 2. Install Recommended Extensions
- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- pytest (littlefishy.pytest)

### 3. Configure Settings
Settings are in `.vscode/settings.json`:
- Black formatting on save
- Linting enabled
- Python path configured

---

## Troubleshooting

### Virtual Environment Not Activating

**Windows:**
```bash
# If venv\Scripts\activate doesn't work, try:
venv\Scripts\activate.bat
```

**Linux/macOS:**
```bash
# Make script executable if needed
chmod +x venv/bin/activate
source venv/bin/activate
```

### Python Not Found
```bash
# Use python3 instead
python3 -m venv venv
```

### Permission Denied
```bash
# On Linux/macOS
chmod +x venv/bin/activate
```

### pip Not Working
```bash
# Upgrade pip
python -m pip install --upgrade pip
```

### Packages Won't Install
```bash
# Try with no cache
pip install --no-cache-dir -r requirements.txt
```

---

## Verifying Setup

### Check Python Version
```bash
python --version
# Should be 3.8+
```

### Check Virtual Environment is Active
```bash
which python  # Linux/macOS
where python  # Windows
# Should show path in venv folder
```

### List Installed Packages
```bash
pip list
# Should show pytest, aiohttp, websockets, etc.
```

### Run Quick Test
```bash
python -c "from src.simulator.main import EVChargingSimulator; print('✓ Installation OK')"
```

---

## Development Dependencies (Optional)

For development, code formatting, and type checking:

```bash
pip install black flake8 mypy pylint
```

### Format Code
```bash
black src/ tests/
```

### Check Code Style
```bash
flake8 src/ tests/
```

### Type Checking
```bash
mypy src/ --ignore-missing-imports
```

---

## Running the Project

### Run Simulator
```bash
python -m src.simulator.main
```

### Run Tests
```bash
pytest tests/ -v
```

### Run with Coverage
```bash
pytest tests/ --cov=src --cov-report=html
```

### Run Examples
```bash
python examples/integration_example.py
```

---

## IDE Configuration Examples

### VS Code - Launch Configuration

Create `.vscode/launch.json`:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Main",
            "type": "python",
            "request": "launch",
            "module": "src.simulator.main",
            "console": "integratedTerminal",
            "justMyCode": true
        },
        {
            "name": "Python: Tests",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": ["tests/", "-v"],
            "console": "integratedTerminal",
            "justMyCode": true
        }
    ]
}
```

### PyCharm Configuration

1. File → Settings → Project → Python Interpreter
2. Click gear icon → Add
3. Select "Existing Environment"
4. Browse to `venv/Scripts/python.exe` (Windows) or `venv/bin/python` (Linux/macOS)
5. Click OK

---

## Deactivating Virtual Environment

When done, deactivate the virtual environment:

```bash
deactivate
```

This returns you to system Python.

---

## Recreating Virtual Environment

If needed, start fresh:

```bash
# Deactivate current environment
deactivate

# Remove old environment
rmdir /s venv  # Windows
rm -rf venv    # Linux/macOS

# Create new environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/macOS

# Install dependencies
pip install -r requirements.txt
```

---

## System-wide Installation (Not Recommended)

For production deployment only:

```bash
# Without virtual environment
pip install -r requirements.txt

# Run simulator
python -m src.simulator.main
```

**Note**: Virtual environment usage is strongly recommended for development.

---

## Docker Setup (Optional)

For containerized deployment:

```dockerfile
FROM python:3.9

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "-m", "src.simulator.main"]
```

Build and run:
```bash
docker build -t ev-simulator .
docker run ev-simulator
```

---

## Troubleshooting Commands

### Check environment variables
```bash
echo %PYTHONPATH%  # Windows
echo $PYTHONPATH   # Linux/macOS
```

### Check Python paths
```bash
python -c "import sys; print(sys.executable)"
python -c "import sys; print(sys.path)"
```

### Test asyncio
```bash
python -c "import asyncio; print('✓ asyncio OK')"
```

### Test installed modules
```bash
python -c "import pytest, aiohttp, websockets; print('✓ All modules OK')"
```

---

## Next Steps

1. ✅ Follow setup instructions for your OS
2. ✅ Activate virtual environment
3. ✅ Install dependencies
4. ✅ Verify with `pytest tests/ -v`
5. ✅ Run first simulation: `python -m src.simulator.main`

---

## Support

If issues persist:

1. Check Python version: `python --version`
2. Verify venv is active: `pip list` should show installed packages
3. Check project path: Make sure you're in the `EV` directory
4. Review error messages carefully
5. Check documentation in `docs/` directory

---

**Ready to simulate! ⚡**
