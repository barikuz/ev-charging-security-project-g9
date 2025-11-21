#!/usr/bin/env python3
"""
Virtual CAN Charger Module
Simulates a charging station's power electronics controller.
Publishes current readings (0x300) and responds to control commands.
"""
import time
import can
import threading

# Initialize virtual CAN bus - STANDARDIZED
bus = can.interface.Bus(bustype="virtual", channel="vcan0", bitrate=500000)

# Charger state
state = {
    "running": False,
    "limit": 32,
    "target": 0.0,
    "current": 0.0
}

def rx_loop():
    """
    Receive loop: Listen for CAN commands
    0x200 - Start charging (enable current flow)
    0x201 - Stop charging (set current to 0)
    0x210 - Set current limit
    """
    print("🔌 Charger Module: Listening for CAN commands...")
    while True:
        msg = bus.recv(timeout=0.1)
        if not msg:
            continue

        if msg.arbitration_id == 0x200:
            # Start charging command
            state["running"] = True
            state["target"] = state["limit"]
            print(f"✅ START command received. Target current: {state['limit']}A")

        elif msg.arbitration_id == 0x201:
            # Stop charging command
            state["running"] = False
            state["target"] = 0
            print(f"🛑 STOP command received. Ramping down to 0A")

        elif msg.arbitration_id == 0x210:
            # Set current limit command
            new_limit = msg.data[0] if len(msg.data) > 0 else 0
            state["limit"] = new_limit
            if state["running"]:
                state["target"] = state["limit"]
            print(f"⚡ Current limit set to: {new_limit}A (running={state['running']})")

def tx_loop():
    """
    Transmit loop: Publish current readings on 0x300
    Smoothly ramp current towards target value
    Also write to shared file for direct plotting
    """
    print("📡 Charger Module: Publishing current readings on CAN ID 0x300...")
    DATA_FILE = "/tmp/ev_current.json"
    import json
    
    while True:
        # Smooth ramping: move 20% towards target each iteration
        state["current"] += (state["target"] - state["current"]) * 0.2
        current = int(max(0, round(state["current"])))
        
        # Send current reading on CAN - STANDARDIZED ENCODING
        msg = can.Message(
            arbitration_id=0x300,
            data=[current & 0xFF, (current >> 8) & 0xFF],
            is_extended_id=False
        )
        bus.send(msg)
        print(f"SENT: {current}")
        
        # ALSO write to shared file for plotter
        with open(DATA_FILE, 'w') as f:
            json.dump({"timestamp": time.time(), "current": current}, f)
        
        time.sleep(0.1)  # Send every 100ms for smooth plotting

if __name__ == "__main__":
    print("=" * 60)
    print("🔋 Virtual Charger Module Starting...")
    print("=" * 60)
    print(f"CAN Bus: interface=virtual, channel=0")
    print(f"Initial state: {state}")
    print()
    
    # Start receiver thread
    threading.Thread(target=rx_loop, daemon=True).start()
    
    # Run transmitter in main thread
    tx_loop()
