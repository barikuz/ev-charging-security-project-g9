# EV Charging Simulator - Quick Start Guide

## 🚀 Quick Start

### 1. Installation (5 minutes)

```bash
# Clone or navigate to project
cd EV

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Your First Simulation (2 minutes)

```bash
# Run basic simulator
python -m src.simulator.main
```

### 3. Test the Installation (3 minutes)

```bash
# Run test suite
pytest tests/ -v
```

---

## 📝 Common Examples

### Example 1: Basic Charging Session
```python
import asyncio
from src.simulator.main import EVChargingSimulator

async def basic_session():
    simulator = EVChargingSimulator()
    result = await simulator.simulate_charging_session(duration=60)
    print(result)

asyncio.run(basic_session())
```

### Example 2: Charging with Anomalies
```python
result = await simulator.simulate_charging_session(
    duration=60,
    anomalies=["CAN_INJECTION", "SPOOFING"]
)
```

### Example 3: Execute Attack Scenario
```python
simulator = EVChargingSimulator()
await simulator.start()
await simulator.execute_attack_scenario("dos")
await simulator.stop()
```

### Example 4: Monitor Statistics
```python
stats = simulator.get_statistics()
print(f"CAN messages: {stats['messages']['can_messages_sent']}")
print(f"Anomalies: {stats['anomalies']['total_injected']}")
```

---

## 🔧 Configuration

All configurations are in `configs/`:
- **simulator_config.yaml** - Main settings
- **can_bus_config.yaml** - CAN parameters
- **ocpp_config.yaml** - OCPP settings
- **v2g_config.yaml** - V2G settings
- **anomalies_config.yaml** - Anomaly settings

Edit these files to customize behavior.

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific component tests
pytest tests/test_can_bus.py -v
pytest tests/test_ocpp.py -v
pytest tests/test_v2g.py -v
pytest tests/test_anomalies.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

---

## 📚 Available Components

| Component | File | Purpose |
|-----------|------|---------|
| **CAN Bus** | `src/can_bus/` | CAN message simulation |
| **OCPP** | `src/ocpp/` | Charging protocol |
| **V2G** | `src/v2g/` | Vehicle-to-Grid |
| **Anomalies** | `src/anomalies/` | Attack simulation |
| **Simulator** | `src/simulator/` | Main orchestrator |

---

## 🎯 Supported Attack Types

- **CAN Injection** - Invalid CAN messages
- **Fuzzing** - Corrupted data
- **DoS Attacks** - Message flooding
- **Spoofing** - False identity
- **Replay Attacks** - Message replay
- **Timing Attacks** - Delay manipulation

---

## 📖 Documentation

- **API.md** - Complete API reference
- **USAGE.md** - Detailed usage examples
- **DEVELOPMENT.md** - Development guide
- **README.md** - Project overview

---

## ⚙️ System Requirements

- Python 3.8+
- ~500MB disk space
- ~100MB RAM minimum
- No special hardware needed (uses virtual CAN)

---

## 🐛 Troubleshooting

### Import Error
```bash
# Make sure venv is activated and requirements are installed
pip install -r requirements.txt
```

### Tests Fail
```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov
```

### Module Not Found
```bash
# Ensure you're in the project root directory
cd path/to/EV
```

---

## 💡 Next Steps

1. ✅ Run the basic simulation
2. ✅ Explore the test files
3. ✅ Try different anomalies
4. ✅ Execute attack scenarios
5. ✅ Customize configurations
6. ✅ Read full documentation

---

## 🔗 Resources

- [OCPP Specification](https://www.openchargealliance.org/)
- [ISO 15118 (V2G)](https://www.iso.org/standard/67014.html)
- [CAN Protocol](https://www.can-cia.org/)
- [Python AsyncIO](https://docs.python.org/3/library/asyncio.html)

---

## 📞 Support

For issues:
1. Check documentation in `docs/`
2. Review test examples in `tests/`
3. Check configuration examples in `configs/`
4. Review error messages and logs

---

**Happy Charging! ⚡**
