#!/usr/bin/env python3
"""
All-in-One EV Charging Anomaly Simulator
Single process: charger + anomaly logic + file writer
NO CAN bus isolation issues!
"""
import time
import json
import threading
import random

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
    Anomaly simulation: Realistic diverse anomaly scenarios
    Includes: normal charging, sudden drops, overloads, fluctuations, shutdowns
    """
    print("🎭 Starting realistic anomaly cycle...")
    time.sleep(2)  # Let tx_loop start first
    
    # Define diverse anomaly scenarios
    scenarios = [
        # (start, end, duration, description)
        (0, 32, 10, "Normal charging start"),
        (32, 0, 5, "Sudden shutdown"),
        (15, 80, 8, "Power surge - overload!"),
        (50, 10, 6, "Connection loss - rapid drop"),
        (20, 35, 7, "Minor fluctuation"),
        (35, 25, 4, "Voltage sag"),
        (25, 60, 9, "Medium load increase"),
        (60, 45, 5, "Controlled reduction"),
        (45, 90, 10, "Maximum load"),
        (90, 0, 3, "Emergency shutdown!"),
        (10, 55, 8, "Gradual ramp-up"),
        (55, 40, 6, "Load balancing"),
        (40, 75, 9, "High demand"),
        (75, 20, 7, "System recovery"),
        (30, 48, 6, "Standard operation"),
    ]
    
    cycle = 1
    while True:
        # Randomly select a scenario
        start_current, end_current, duration, description = random.choice(scenarios)
        
        print(f"\n{'='*70}")
        print(f"🔄 ANOMALY CYCLE #{cycle}: {description}")
        print(f"{'='*70}\n")
        
        # Phase 1: Set initial current
        print(f"📉 Phase 1: Setting current to {start_current}A")
        state["limit"] = start_current
        state["running"] = True
        state["target"] = start_current
        wait_time = random.uniform(3, 6)
        print(f"⏱️  {wait_time:.1f} seconds...")
        time.sleep(wait_time)
        
        # Phase 2: Transition to end current
        print(f"\n📈 Phase 2: Changing current to {end_current}A")
        state["limit"] = end_current
        state["target"] = end_current
        print(f"⏱️  {duration} seconds...")
        time.sleep(duration)
        
        # Phase 3: Randomly decide whether to STOP
        if random.random() > 0.6:  # 40% chance of stopping
            print("\n🛑 Phase 3: STOP command")
            state["running"] = False
            state["target"] = 0
            stop_time = random.uniform(2, 5)
            print(f"⏱️  {stop_time:.1f} seconds...")
            time.sleep(stop_time)
        else:
            print("\n✅ Continuing to next cycle...")
            time.sleep(1)
        
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
