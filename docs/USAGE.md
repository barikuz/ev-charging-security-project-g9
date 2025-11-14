# Usage Guide

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd EV
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Simulator

### Basic Simulation
```bash
python -m src.simulator.main
```

### With Custom Configuration
```python
from src.simulator.main import EVChargingSimulator

simulator = EVChargingSimulator(config_path='configs/custom_config.yaml')
import asyncio
asyncio.run(simulator.simulate_charging_session(duration=300))
```

### Running Tests
```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_can_bus.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## Example Use Cases

### 1. Normal Charging Simulation
```python
import asyncio
from src.simulator.main import EVChargingSimulator

async def normal_charging():
    simulator = EVChargingSimulator()
    result = await simulator.simulate_charging_session(duration=300)
    print(f"Charging completed: {result}")

asyncio.run(normal_charging())
```

### 2. Testing with Anomalies
```python
import asyncio
from src.simulator.main import EVChargingSimulator

async def charging_with_anomalies():
    simulator = EVChargingSimulator()
    result = await simulator.simulate_charging_session(
        duration=300,
        anomalies=["CAN_INJECTION", "SPOOFING"]
    )
    print(result)

asyncio.run(charging_with_anomalies())
```

### 3. Running Attack Scenarios
```python
import asyncio
from src.simulator.main import EVChargingSimulator

async def attack_test():
    simulator = EVChargingSimulator()
    await simulator.start()
    
    # Execute DoS attack
    await simulator.execute_attack_scenario("dos")
    
    await simulator.stop()

asyncio.run(attack_test())
```

### 4. Custom CAN Bus Simulation
```python
import asyncio
from src.can_bus.simulator import CANBusSimulator, CANMessage, EVCANMessages

async def can_simulation():
    can_bus = CANBusSimulator()
    can_bus.start()
    
    # Send battery status
    msg = EVCANMessages.battery_status(soc=50, temperature=35, voltage=400)
    await can_bus.send_message(msg)
    
    # Send charging state
    msg = EVCANMessages.charging_state(state=1, current=32, power=10000)
    await can_bus.send_message(msg)
    
    can_bus.stop()

asyncio.run(can_simulation())
```

### 5. OCPP Communication
```python
import asyncio
from src.ocpp.protocol import OCPPServer, OCPPClient

async def ocpp_test():
    server = OCPPServer()
    client = OCPPClient()
    
    await server.start()
    await client.connect()
    
    # Start transaction
    result = await client.start_transaction("ID123", 0)
    print(f"Transaction: {result}")
    
    # Send heartbeat
    await client.send_heartbeat()
    
    await client.disconnect()
    await server.stop()

asyncio.run(ocpp_test())
```

### 6. V2G Protocol Testing
```python
import asyncio
from src.v2g.communicator import V2GCommunicator, V2GMessage

async def v2g_test():
    v2g = V2GCommunicator()
    
    # Discovery
    discovery_msg = {"type": V2GMessage.DISCOVERY_REQ.value}
    response = await v2g.handle_message(discovery_msg)
    print(f"Discovery response: {response}")
    
    # Session start
    start_msg = {"type": V2GMessage.SESSION_START_REQ.value}
    response = await v2g.handle_message(start_msg)
    print(f"Session ID: {response.get('sessionID')}")
    
    # Get session info
    info = v2g.get_session_info()
    print(f"Session active: {info['sessionActive']}")

asyncio.run(v2g_test())
```

### 7. Anomaly Injection Control
```python
from src.anomalies.injector import AnomalyInjector, AttackSeverity

# Create injector
injector = AnomalyInjector()

# Inject specific anomalies
injector.inject("CAN_INJECTION", "can", AttackSeverity.HIGH)
injector.inject("DOS_ATTACK", "ocpp", AttackSeverity.MEDIUM)

# Check active anomalies
active = injector.get_active_anomalies()
print(f"Active anomalies: {len(active)}")

# Get statistics
stats = injector.get_statistics()
print(f"Total injected: {stats['total_injected']}")

# Remove anomaly
injector.remove_anomaly("CAN_INJECTION_0")
```

## Configuration Files

### simulator_config.yaml
Main configuration for simulator parameters, protocols, and data collection.

### can_bus_config.yaml
CAN bus-specific settings including bitrate, channel, and message types.

### ocpp_config.yaml
OCPP protocol configuration with server/client settings.

### v2g_config.yaml
V2G communication parameters and power limits.

### anomalies_config.yaml
Anomaly injection parameters and attack scenarios.

## Command Line Tasks

In VS Code, you can run predefined tasks:

- **Run Simulator**: Executes the main simulator
- **Run Tests**: Runs pytest test suite
- **Run Tests with Coverage**: Generates coverage report
- **Install Dependencies**: Installs required packages

Use Ctrl+Shift+P → "Run Task" to execute these tasks.

## Debugging

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Use VS Code debugger with breakpoints for step-by-step execution.

## Performance Tips

1. **Reduce message rate** for slower systems
2. **Disable anomalies** when not testing attacks
3. **Use shorter durations** for quick tests
4. **Monitor resource usage** with system tools

## Troubleshooting

### Import Errors
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt`
- Check Python version (3.8+)

### Async Errors
- Verify `asyncio` syntax is correct
- Use `await` for async functions
- Check event loop is running

### CAN Bus Issues
- Ensure virtual CAN interface exists (Linux)
- Check permissions for hardware access
- Verify channel configuration

## Next Steps

1. Review the API documentation in `docs/API.md`
2. Explore test files for more examples
3. Customize configuration files for your needs
4. Integrate with your testing framework
