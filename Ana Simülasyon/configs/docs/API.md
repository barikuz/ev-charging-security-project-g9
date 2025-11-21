# API Documentation

## Overview
This document provides detailed API documentation for the EV Charging Simulator.

## Main Components

### EVChargingSimulator

The main orchestrator class that manages all charging system simulations.

#### Constructor
```python
simulator = EVChargingSimulator(
    config: Optional[SimulatorConfig] = None,
    config_path: Optional[str] = None
)
```

#### Methods

- `async start()` - Start the simulator and all components
- `async stop()` - Stop the simulator gracefully
- `async simulate_charging_session(duration: float, anomalies: Optional[List[str]]) -> Dict` - Run a complete charging session
- `inject_anomaly(anomaly_type: str, severity: str) -> bool` - Inject an anomaly
- `async execute_attack_scenario(scenario_name: str) -> bool` - Execute a predefined attack
- `get_statistics() -> Dict` - Get current statistics

#### Example Usage
```python
import asyncio
from src.simulator.main import EVChargingSimulator

async def main():
    simulator = EVChargingSimulator()
    
    # Run a charging session with anomalies
    result = await simulator.simulate_charging_session(
        duration=300.0,
        anomalies=["CAN_INJECTION", "DOS_ATTACK"]
    )
    
    print(result)

asyncio.run(main())
```

---

## CAN Bus Simulator

### CANBusSimulator

Handles CAN message generation and communication.

#### Methods

- `async send_message(message: CANMessage) -> bool` - Send a CAN message
- `async receive_messages(timeout: float) -> List[CANMessage]` - Receive CAN messages
- `add_listener(callback: callable)` - Register a message listener
- `start()` - Start the simulator
- `stop()` - Stop the simulator
- `get_statistics() -> Dict` - Get bus statistics

#### CANMessage

```python
message = CANMessage(
    arbitration_id=0x123,
    data=b'\x00\x01\x02\x03\x04\x05\x06\x07',
    dlc=8,
    is_extended_id=False
)
```

#### Predefined Messages

```python
# Battery status
msg = EVCANMessages.battery_status(soc=75, temperature=35, voltage=400)

# Charging state
msg = EVCANMessages.charging_state(state=1, current=32, power=10000)

# Error status
msg = EVCANMessages.error_status(error_code=0x01, severity=1)
```

---

## OCPP Protocol

### OCPPServer

OCPP protocol server implementation.

#### Methods

- `async start()` - Start OCPP server
- `async stop()` - Stop OCPP server
- `async handle_message(message: OCPPMessage) -> Optional[OCPPMessage]` - Handle incoming message

### OCPPClient

OCPP protocol client implementation.

#### Methods

- `async connect() -> bool` - Connect to OCPP server
- `async disconnect()` - Disconnect from server
- `async send_boot_notification() -> Dict` - Send boot notification
- `async send_heartbeat() -> Dict` - Send heartbeat
- `async send_meter_values(values: Dict) -> Dict` - Send meter values
- `async start_transaction(id_tag: str, meter_start: int) -> Dict` - Start transaction
- `async stop_transaction(meter_stop: int, transaction_id: Optional[int]) -> Dict` - Stop transaction

#### Example Usage
```python
client = OCPPClient()
await client.connect()
result = await client.start_transaction("TAG123", 0)
print(f"Transaction ID: {result['transactionId']}")
```

---

## V2G Communication

### V2GCommunicator

Handles V2G (Vehicle-to-Grid) protocol communication.

#### Methods

- `async handle_message(message: Dict) -> Dict` - Process V2G message
- `async authenticate(auth_type: V2GAuthType, credentials: Dict) -> bool` - Authenticate
- `get_session_info() -> Dict` - Get current session info
- `get_message_log(limit: int) -> List[Dict]` - Get message history

#### Message Types
- DiscoveryReq/Res
- ServiceDiscoveryReq/Res
- SessionStartReq/Res
- ChargingStatusReq/Res
- PowerDeliveryReq/Res
- SessionStopReq/Res

---

## Anomaly Injection

### AnomalyInjector

Manages anomaly and attack injection for security testing.

#### Methods

- `inject(anomaly_type: str, protocol: str, severity: AttackSeverity) -> bool` - Inject anomaly
- `remove_anomaly(anomaly_id: str) -> bool` - Remove active anomaly
- `get_active_anomalies() -> List[AnomalyEvent]` - Get active anomalies
- `modify_can_message(data: bytes, severity: float) -> bytes` - Corrupt CAN message
- `create_dos_messages(count: int) -> List[Dict]` - Create DoS messages
- `create_spoofed_message(original_id: int, payload: bytes) -> Dict` - Create spoofed message
- `get_statistics() -> Dict` - Get injection statistics

#### Anomaly Types
- CAN_INJECTION
- CAN_FUZZING
- MESSAGE_DELAY
- MESSAGE_DUPLICATION
- SPOOFING
- REPLAY_ATTACK
- DOS_ATTACK
- TIMING_ATTACK
- INVALID_STATE
- POWER_ANOMALY

#### Attack Severity
- LOW (0.1)
- MEDIUM (0.5)
- HIGH (0.9)

#### Predefined Scenarios
```python
# CAN injection attack
scenario = AttackScenarios.can_injection_attack()
await scenario.execute(injector)

# DoS attack
scenario = AttackScenarios.dos_attack()
await scenario.execute(injector)

# Replay attack
scenario = AttackScenarios.replay_attack()
await scenario.execute(injector)

# Spoofing attack
scenario = AttackScenarios.spoofing_attack()
await scenario.execute(injector)
```

---

## Configuration

### Simulator Configuration

Main configuration file: `configs/simulator_config.yaml`

```yaml
simulator:
  name: "EV Charging Simulator"
  log_level: "INFO"

protocols:
  can:
    enabled: true
  ocpp:
    enabled: true
  v2g:
    enabled: true
  anomalies:
    enabled: true
```

### Protocol-Specific Configurations

- `configs/can_bus_config.yaml` - CAN bus parameters
- `configs/ocpp_config.yaml` - OCPP server/client settings
- `configs/v2g_config.yaml` - V2G communication settings
- `configs/anomalies_config.yaml` - Anomaly injection parameters

---

## Data Structures

### SimulatorConfig
```python
@dataclass
class SimulatorConfig:
    name: str = "EV Charging Simulator"
    can_enabled: bool = True
    ocpp_enabled: bool = True
    v2g_enabled: bool = True
    anomaly_enabled: bool = True
```

### AnomalyEvent
```python
@dataclass
class AnomalyEvent:
    timestamp: float
    anomaly_type: AnomalyType
    severity: AttackSeverity
    target_protocol: str
    description: str
    affected_message_id: Optional[str] = None
```

### Statistics Response
```python
{
    "elapsed_time": 0.0,
    "is_running": False,
    "messages": {
        "can_messages_sent": 0,
        "ocpp_messages_sent": 0,
        "v2g_messages_sent": 0,
        "anomalies_injected": 0,
        "errors": 0
    },
    "can_bus": {...},
    "anomalies": {...},
    "v2g": {...}
}
```

---

## Error Handling

All async methods can raise exceptions. Handle them appropriately:

```python
try:
    await simulator.start()
except Exception as e:
    logger.error(f"Simulator error: {e}")
```

---

## Logging

The simulator uses Python's standard logging module. Configure logging:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

---

## Performance Considerations

- CAN bus can process ~1000 messages/second
- OCPP messages typically take 100-500ms for round-trip
- V2G handshake takes 1-2 seconds
- Anomaly injection has minimal overhead (<5%)

---

## References

- [OCPP Specification](https://www.openchargealliance.org/)
- [ISO 15118 (V2G)](https://www.iso.org/standard/67014.html)
- [CAN Protocol](https://www.can-cia.org/)
