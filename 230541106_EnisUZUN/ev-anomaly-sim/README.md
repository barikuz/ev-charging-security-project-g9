# ⚡ EV Charging Anomaly Simulator

A complete, runnable simulation of **"Repeated Current Fluctuation During Charging"** anomaly in Electric Vehicle charging stations with **🧠 MemoryBank** - a persistent memory system for event logging and anomaly learning.

## 🎯 Overview

This project simulates an OCPP 1.6 charging infrastructure with:
- **CSMS (Central System)** - WebSocket server orchestrating charging commands
- **Charge Point** - OCPP client that bridges OCPP messages to CAN bus
- **Virtual Charger Module** - CAN device simulating power electronics
- **Live Plotter** - Real-time visualization of charging current
- **🧠 MemoryBank** - SQLite-based persistent memory for events, anomalies, and patterns

## 🏗️ Architecture

```
┌─────────────┐        OCPP 1.6         ┌──────────────┐
│    CSMS     │◄─────WebSocket──────────►│ Charge Point │
│  (Server)   │   ws://127.0.0.1:9000    │   (Client)   │
└─────────────┘                          └───────┬──────┘
                                                 │
                                          CAN Bus│(Virtual)
                                                 │
                    ┌────────────────────────────┼────────────┐
                    │                            │            │
              ┌─────▼──────┐                ┌───▼────────┐   │
              │  Charger   │                │  Current   │   │
              │   Module   │───────0x300───►│  Plotter   │   │
              │ (CAN Node) │                │  (Monitor) │   │
              └────────────┘                └────────────┘   │
                                                              │
                    Virtual CAN Bus (interface="virtual", channel=0)
```

## 📋 Requirements

- **OS**: macOS (tested on M2)
- **Python**: 3.11
- **Dependencies**:
  - matplotlib==3.8.2
  - python-can==4.4.2
  - ocpp==0.20.0
  - websockets==12.0
  - tabulate==0.9.0 (for MemoryBank viewer)

## 🚀 Quick Start

### 1. Create Virtual Environment

```bash
cd 230541106_EnisUZUN
python3.11 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Simulation

```bash
chmod +x run_all.sh
./run_all.sh
```

This will open 4 Terminal tabs:
1. **Charger Module** - CAN device simulator
2. **CSMS Server** - OCPP server
3. **Charge Point** - OCPP client
4. **Current Plotter** - Live graph

## 📁 Project Files

### Core Components

| File | Description |
|------|-------------|
| `charger_module.py` | Virtual CAN device that publishes current readings (0x300) and responds to control commands (0x200, 0x201, 0x210) |
| `csms.py` | OCPP 1.6 WebSocket server that orchestrates the anomaly by cycling SetChargingProfile, RemoteStart/Stop (🧠 MemoryBank enabled) |
| `cp.py` | OCPP client that translates OCPP messages to CAN commands and reports MeterValues (🧠 MemoryBank enabled) |
| `plot_current.py` | Real-time matplotlib visualization of charging current (🧠 shows historical anomalies) |
| `memory_bank.py` | SQLite-based persistent memory system for events, anomalies, sessions, and patterns |
| `memory_viewer.py` | Interactive tool to view and analyze MemoryBank data |
| `run_all.sh` | Launcher script that starts all components in separate Terminal tabs |

### Configuration Files

| File | Description |
|------|-------------|
| `requirements.txt` | Python package dependencies |
| `README.md` | This file |

## 🔌 CAN Message Protocol

| CAN ID | Direction | Purpose | Data Format |
|--------|-----------|---------|-------------|
| 0x200 | CP → Charger | Start charging | Empty |
| 0x201 | CP → Charger | Stop charging | Empty |
| 0x210 | CP → Charger | Set current limit | [limit_low, limit_high] (little-endian) |
| 0x300 | Charger → All | Current reading | [current_low, current_high] (little-endian) |

## 🎭 Anomaly Scenario

The CSMS executes this cycle repeatedly:

1. **SetChargingProfile(0A)** → Limit current to 0A
2. *Wait 2 seconds*
3. **SetChargingProfile(100A)** → Raise limit to 100A
4. *Wait 1 second*
5. **RemoteStartTransaction** → Start charging
6. *Wait 2 seconds*
7. **RemoteStopTransaction** → Stop charging
8. *Wait 3 seconds*
9. **Repeat**

This creates a repeating pattern of current fluctuations: **0A → 100A → 0A → 100A**

## 🖥️ Component Details

### Charger Module (`charger_module.py`)

- Runs on virtual CAN bus (interface="virtual", channel=0)
- Publishes current readings every 1 second on CAN ID 0x300
- Smoothly ramps current (20% per iteration) to simulate realistic behavior
- Responds to control commands from Charge Point

### CSMS (`csms.py`)

- WebSocket server on ws://127.0.0.1:9000/
- Implements OCPP 1.6 server-side operations
- Handles BootNotification and MeterValues from charge points
- Orchestrates anomaly scenario in infinite loop

### Charge Point (`cp.py`)

- OCPP 1.6 client connecting to CSMS
- Implements handlers for RemoteStartTransaction, RemoteStopTransaction, SetChargingProfile
- Translates OCPP commands to CAN messages
- Reads CAN 0x300 and sends MeterValues to CSMS every second

### Current Plotter (`plot_current.py`)

- Subscribes to CAN ID 0x300 (current readings)
- Displays live matplotlib graph with 60-second rolling window
- Shows anomaly detection indicator when fluctuations detected
- Real-time current value display

## 🛠️ Manual Testing

To run components individually:

```bash
# Terminal 1: Start charger module
source venv/bin/activate
python3 charger_module.py

# Terminal 2: Start CSMS server
source venv/bin/activate
python3 csms.py

# Terminal 3: Start charge point
source venv/bin/activate
python3 cp.py

# Terminal 4: Start plotter
source venv/bin/activate
python3 plot_current.py
```

## 🐛 Troubleshooting

### Issue: "No module named 'can'"
**Solution**: Ensure virtual environment is activated and dependencies are installed:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: Components can't communicate
**Solution**: Ensure all components use the same CAN bus configuration:
- `interface="virtual"`
- `channel=0`
- No `extended_id` or `is_extended_id=False`

### Issue: Plotter shows no data
**Solution**: 
1. Check that charger_module.py is running
2. Verify CAN bus is working: `python3 -c "import can; bus = can.interface.Bus(interface='virtual', channel=0); print('OK')"`

### Issue: WebSocket connection refused
**Solution**: Ensure CSMS is running before starting Charge Point

## 📊 Expected Output

When running correctly, you should see:

1. **Charger Module**: Current values ramping up/down
2. **CSMS**: Sending OCPP commands in cycles (🧠 recording to MemoryBank)
3. **Charge Point**: Receiving OCPP, sending CAN, reporting MeterValues (🧠 logging events)
4. **Plotter**: Live graph showing 0A ↔ 100A fluctuations with anomaly indicator and statistics

## 🧠 MemoryBank Features

The MemoryBank system provides persistent memory and learning capabilities:

### What MemoryBank Records

- **Events**: All OCPP messages, CAN communications, system events
- **Anomalies**: Detected anomalies with severity, patterns, and deviations
- **Sessions**: Charging session metadata (start/end time, energy, statistics)
- **Metrics**: Current, voltage, power measurements over time
- **Patterns**: Learned behavior patterns for anomaly detection

### Using MemoryBank Viewer

View and analyze collected data:

```bash
# Interactive menu
python3 memory_viewer.py

# Quick summary
python3 memory_viewer.py --summary

# View recent events
python3 memory_viewer.py --events 50

# View anomalies
python3 memory_viewer.py --anomalies 20

# View sessions
python3 memory_viewer.py --sessions 10

# Export data to JSON
python3 memory_viewer.py --export data_export.json

# Show statistics
python3 memory_viewer.py --stats
```

### Database Location

All data is stored in: `ev_charging_memory.db` (SQLite database)

You can view this database with any SQLite viewer or use the provided `memory_viewer.py` tool.

## 🔒 Technical Notes

- **Virtual CAN Bus**: Uses python-can's virtual bus (no kernel modules needed)
- **No socketcan/vcan**: Compatible with macOS without CAN hardware
- **Thread-safe**: CAN bus operations are thread-safe across processes
- **Asyncio**: OCPP components use asyncio for concurrent operations
- **Real-time**: All components update at 1-second intervals
- **🧠 Persistent Memory**: SQLite database for event history and learning

## 📝 License

This is a simulation/educational project. Use freely for learning and testing purposes.

## 🤝 Contributing

This is a complete, self-contained simulation. Modify as needed for your use case.

## ⚠️ Disclaimer

This is a **simulation** for testing and demonstration purposes. It mimics the behavior of real EV charging infrastructure but should not be used in production environments without proper adaptation and safety measures.

---

**Made with ⚡ for EV charging anomaly research**
