# 🚀 Quick Start Guide

## Complete Setup (First Time)

```bash
# 1. Navigate to project
cd /Users/enisuzun/Desktop/ev-anomaly-sim

# 2. Create Python 3.11 virtual environment (already done!)
# python3.11 -m venv venv

# 3. Activate virtual environment
source venv/bin/activate

# 4. Install dependencies (already done!)
# pip install -r requirements.txt

# 5. Test environment
python3 test_environment.py

# 6. Run the simulation
./run_all.sh
```

## Quick Run (After Initial Setup)

```bash
cd /Users/enisuzun/Desktop/ev-anomaly-sim
./run_all.sh
```

## What Happens When You Run

The `run_all.sh` script will open **4 new Terminal tabs**:

1. **Tab 1: Charger Module** 🔌
   - Virtual CAN device
   - Publishes current readings
   - Responds to control commands

2. **Tab 2: CSMS Server** 🏢
   - OCPP WebSocket server
   - Orchestrates anomaly scenario
   - Sends charging commands

3. **Tab 3: Charge Point** ⚡
   - OCPP client
   - Translates OCPP → CAN
   - Reports meter values

4. **Tab 4: Current Plotter** 📊
   - Opens matplotlib window
   - Shows live current graph
   - Displays anomaly indicator

## Expected Behavior

### Terminal Output

Each component will show its status:
- Connection messages
- CAN messages sent/received
- OCPP commands
- Current values

### Graph Window

You'll see a live graph showing:
- Charging current (0-100A)
- Time on x-axis
- Fluctuating pattern (0A ↔ 100A)
- Red "ANOMALY DETECTED" warning when fluctuations occur

## Stopping the Simulation

### Option 1: Close Individual Tabs
Close each Terminal tab (Cmd+W in each tab)

### Option 2: Kill All at Once
In a new terminal:
```bash
pkill -f "charger_module.py"
pkill -f "csms.py"
pkill -f "cp.py"
pkill -f "plot_current.py"
```

### Option 3: Ctrl+C in Each Tab
Press Ctrl+C in each Terminal tab

## Troubleshooting Quick Fixes

### "command not found: python3.11"
Install Python 3.11:
```bash
brew install python@3.11
```

### "No module named 'X'"
Ensure virtual environment is activated:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Components not communicating
1. Ensure all components are running
2. Check that charger_module.py started first
3. Restart in order: charger → csms → cp → plotter

### Graph not showing
1. Check that charger_module.py is running
2. Wait 5-10 seconds for data to accumulate
3. Ensure matplotlib window isn't hidden behind other windows

## Testing Individual Components

### Test CAN Bus Only
```bash
source venv/bin/activate
python3 demo_can.py
```

### Test Charger Module Only
```bash
source venv/bin/activate
python3 charger_module.py
# Should show: "Listening for CAN commands..."
```

### Test CSMS Only
```bash
source venv/bin/activate
python3 csms.py
# Should show: "CSMS WebSocket server running..."
```

## Understanding the Anomaly Pattern

The simulation creates this repeating cycle:

```
Cycle 1:
  0s:  SetChargingProfile(0A)   → Target: 0A
  2s:  SetChargingProfile(100A) → Target: 100A
  3s:  RemoteStartTransaction   → Start charging
  5s:  RemoteStopTransaction    → Stop charging
  8s:  [Repeat]

Result: Current fluctuates 0A → 100A → 0A → 100A ...
```

This creates the "Repeated Current Fluctuation" anomaly pattern.

## File Roles

| File | Purpose | Can Run Alone? |
|------|---------|----------------|
| `charger_module.py` | CAN device simulator | ✅ Yes |
| `csms.py` | OCPP server | ✅ Yes |
| `cp.py` | OCPP client | ❌ Needs CSMS + Charger |
| `plot_current.py` | Visualizer | ❌ Needs Charger |

## Next Steps

1. ✅ Run `./run_all.sh`
2. 📊 Watch the live graph
3. 🔍 Observe the anomaly pattern
4. 📝 Modify timing in `csms.py` to experiment
5. ⚙️ Adjust current limits to see different patterns

## Tips

- **Best viewing**: Make the matplotlib window full screen
- **Log analysis**: Each terminal shows detailed operation logs
- **Timing**: Wait 10-15 seconds for the full pattern to emerge
- **Performance**: Close other apps for smoother plotting

---

**Ready to start? Run: `./run_all.sh`**
