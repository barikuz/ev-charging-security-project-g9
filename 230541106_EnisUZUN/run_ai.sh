#!/bin/bash

# run_ai.sh
# Starts the AI-powered anomaly detection system

echo "🤖 Starting AI-Powered EV Charging Anomaly Detection System"
echo "=============================================================="
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_PATH="$SCRIPT_DIR/venv/bin/activate"

if [ ! -f "$VENV_PATH" ]; then
    echo "❌ Virtual environment not found!"
    exit 1
fi

# Check if model exists
if [ ! -f "$SCRIPT_DIR/anomaly_model.pkl" ]; then
    echo "❌ AI model not found!"
    echo ""
    echo "Please train the model first:"
    echo "  1. ./run_all.sh  (start simulation)"
    echo "  2. python data_collector.py  (collect training data for 60s)"
    echo "  3. python train_model.py  (train the AI model)"
    echo ""
    exit 1
fi

echo "✅ AI Model found"
echo "📂 Project directory: $SCRIPT_DIR"
echo ""

# Function to open Terminal tab
run_in_new_tab() {
    local title=$1
    local script=$2
    
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

echo "🔧 Launching AI components..."
echo ""

# Start simulator
run_in_new_tab "1️⃣  Charging Simulator" "all_in_one.py"
sleep 2

# Start AI detector
run_in_new_tab "2️⃣  AI Detector (Live)" "live_detector.py"
sleep 2

# Start enhanced plotter
run_in_new_tab "3️⃣  AI-Enhanced Graph" "enhanced_plot.py"

echo ""
echo "✅ AI SYSTEM STARTED!"
echo ""
echo "=============================================================="
echo "📊 System Components:"
echo "=============================================================="
echo "1️⃣  Charging Simulator → Generates anomaly patterns"
echo "2️⃣  AI Detector        → Real-time ML predictions"
echo "3️⃣  AI-Enhanced Graph  → Visualization with predictions"
echo ""
echo "🤖 AI Model: Random Forest Classifier"
echo "🎯 Detection: Real-time anomaly identification"
echo "📊 Features: 8 statistical features extracted from current"
echo ""
echo "🛑 To stop: Close each Terminal tab or press Ctrl+C"
echo "=============================================================="
