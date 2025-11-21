#!/usr/bin/env python3
"""
CAN to File Bridge (Simplified)
Reads CAN 0x300 messages from charger and writes to shared file
NO OCPP - just direct CAN → file bridge
"""
import can
import time
import json

print("=" * 60)
print("🌉 CAN→File Bridge Starting...")
print("=" * 60)

# Connect to CAN bus (same as charger_module)
bus = can.interface.Bus(interface="virtual", channel=0)
print("✅ CAN bus connected")

DATA_FILE = "/tmp/ev_current.json"
print(f"📝 Writing to: {DATA_FILE}")
print()

# Initialize file
with open(DATA_FILE, 'w') as f:
    json.dump({"timestamp": time.time(), "current": 0}, f)

print("📊 Listening for CAN 0x300 messages...")
print()

while True:
    msg = bus.recv(timeout=0.5)
    if msg and msg.arbitration_id == 0x300:
        if len(msg.data) >= 2:
            # Decode current (little-endian)
            current = msg.data[0] + (msg.data[1] << 8)
            
            # Write to file
            with open(DATA_FILE, 'w') as f:
                json.dump({"timestamp": time.time(), "current": current}, f)
            
            print(f"RECEIVED: {current}A → Written to file")
