#!/usr/bin/env python3
"""
All-in-One EV Charging Anomaly Simulator
Single process: charger + anomaly logic + file writer
NO CAN bus isolation issues!
"""
import time
import json
import threading

# Charger state
state = {
    "running": False,
    "limit": 32,
    "target": 0.0,
    "current": 0.0
}

DATA_FILE = "/tmp/ev_current.json"

def tx_loop():
    """
    Transmit loop: Calculate current and write to file
    """
    print("📡 Starting current calculation loop...")
    
    while True:
        # Smooth ramping: move 20% towards target each iteration
        state["current"] += (state["target"] - state["current"]) * 0.2
        current = int(max(0, round(state["current"])))
        
        # Write to shared file for plotter
        with open(DATA_FILE, 'w') as f:
            json.dump({"timestamp": time.time(), "current": current}, f)
        
        print(f"⚡ Current: {current}A (target={state['target']}A, running={state['running']})")
        
        time.sleep(0.1)  # Update every 100ms

def anomaly_loop():
    """
    Anomaly simulation: Cycle through 0A → 32A → 0A
    """
    print("🎭 Starting anomaly cycle...")
    time.sleep(2)  # Let tx_loop start first
    
    cycle = 1
    while True:
        print(f"\n{'='*60}")
        print(f"🔄 ANOMALY CYCLE #{cycle}")
        print(f"{'='*60}\n")
        
        # Phase 1: Limit to 0A but START
        print("📉 Phase 1: Limit 0A + START")
        state["limit"] = 0
        state["running"] = True
        state["target"] = 0
        print("⏱️  10 seconds...")
        time.sleep(10)
        
        # Phase 2: Increase to 32A
        print("\n📈 Phase 2: Limit 32A")
        state["limit"] = 32
        state["target"] = 32
        print("⏱️  10 seconds...")
        time.sleep(10)
        
        # Phase 3: STOP
        print("\n🛑 Phase 3: STOP")
        state["running"] = False
        state["target"] = 0
        print("⏱️  5 seconds...")
        time.sleep(5)
        
        cycle += 1

if __name__ == "__main__":
    print("=" * 60)
    print("🔋 All-in-One EV Charging Anomaly Simulator")
    print("=" * 60)
    print(f"Initial state: {state}")
    print(f"Output file: {DATA_FILE}")
    print()
    
    # Initialize file
    with open(DATA_FILE, 'w') as f:
        json.dump({"timestamp": time.time(), "current": 0}, f)
    
    # Start transmitter thread
    threading.Thread(target=tx_loop, daemon=True).start()
    
    # Run anomaly loop in main thread
    try:
        anomaly_loop()
    except KeyboardInterrupt:
        print("\n\n✅ Simulation stopped")
