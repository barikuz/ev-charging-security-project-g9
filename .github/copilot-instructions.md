# EV Charging Simulator - Project Instructions

## Project Overview
This is a Python project for simulating electric vehicle charging systems with support for:
- CAN bus communication and message simulation
- OCPP (Open Charge Point Protocol) server/client implementation
- V2G (Vehicle-to-Grid) protocol simulation
- Anomaly injection for security testing
- Attack simulation and vulnerability testing

## Development Environment
- Language: Python 3.8+
- Main Framework: AsyncIO for async communication
- Protocols: CAN bus, OCPP 1.6/2.0, V2G (ISO 15118)
- Testing: pytest with asyncio support
- Web Interface: Flask-based dashboard

## Project Structure
- `src/can_bus/` - CAN message handling and simulation
- `src/ocpp/` - OCPP protocol implementation
- `src/v2g/` - V2G communication
- `src/simulator/` - Main simulation engine
- `src/anomalies/` - Anomaly and attack injection
- `tests/` - Unit and integration tests
- `configs/` - Configuration files

## Key Components to Develop
1. CAN bus simulator with realistic message generation
2. OCPP protocol handler (client and server)
3. V2G communication layer
4. Anomaly injection system
5. Web-based monitoring dashboard
6. Comprehensive test suite
