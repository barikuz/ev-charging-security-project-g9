#!/bin/bash

# run_all.sh
# Starts all components of the EV Anomaly Simulation in separate Terminal tabs
# Designed for macOS

echo "🚀 Starting EV Charging Anomaly Simulation..."
echo "=============================================="
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment path
VENV_PATH="$SCRIPT_DIR/venv/bin/activate"

# Check if virtual environment exists
if [ ! -f "$VENV_PATH" ]; then
    echo "❌ Virtual environment not found at $SCRIPT_DIR/venv"
    echo "Please create it first:"
    echo "  cd $SCRIPT_DIR"
    echo "  python3.11 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install matplotlib==3.8.2 python-can==4.4.2 ocpp==0.20.0 websockets==12.0"
    exit 1
fi

echo "✅ Virtual environment found"
echo "📂 Project directory: $SCRIPT_DIR"
echo ""

# Function to open a new Terminal tab and run a command
run_in_new_tab() {
    local title=$1
    local script=$2
    local color=$3
    
    osascript <<EOF
tell application "Terminal"
    activate
    set newTab to do script "cd '$SCRIPT_DIR' && source venv/bin/activate && clear && echo '═══════════════════════════════════════════════════════════' && echo '🏷  $title' && echo '═══════════════════════════════════════════════════════════' && echo '' && python3 $script"
    set custom title of newTab to "$title"
end tell
EOF
    echo "✅ Started: $title"
    sleep 1
}

echo "🔧 Launching components in separate Terminal tabs..."
echo ""

# Start components in order with delays for proper initialization
run_in_new_tab "1️⃣  Charger Module" "charger_module.py" "blue"
sleep 2

run_in_new_tab "2️⃣  CAN Bridge" "current_bridge.py" "cyan"
sleep 1

run_in_new_tab "3️⃣  CSMS Server" "csms.py" "green"
sleep 2

run_in_new_tab "4️⃣  Charge Point" "cp.py" "yellow"
sleep 2

run_in_new_tab "5️⃣  Current Plotter" "plot_current.py" "purple"

echo ""
echo "✅ All components launched!"
echo ""
echo "=============================================="
echo "📊 System Overview:"
echo "=============================================="
echo "1️⃣  Charger Module  → Virtual CAN device (publishes 0x300)"
echo "2️⃣  CAN Bridge      → Reads CAN, writes to /tmp/ev_current.json"
echo "3️⃣  CSMS Server     → OCPP 1.6 server (ws://127.0.0.1:9000)"
echo "4️⃣  Charge Point    → OCPP client + CAN commander"
echo "5️⃣  Current Plotter → Real-time visualization from file"
echo ""
echo "🎭 The simulation will now:"
echo "   • Generate repeated current fluctuations"
echo "   • Display live charging current graph"
echo "   • Demonstrate 0A ↔ 100A anomaly pattern"
echo ""
echo "🛑 To stop: Close each Terminal tab manually"
echo "   or press Ctrl+C in each tab"
echo ""
echo "=============================================="
