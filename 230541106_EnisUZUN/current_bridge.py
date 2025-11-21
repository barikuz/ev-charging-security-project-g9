#!/usr/bin/env python3
"""
CAN Current Bridge
Reads from charger_module CAN bus and writes to shared file
Other processes can read from this file
"""
import can
import json
import time

# CAN bus for receiving from charger
bus_rx = can.interface.Bus(bustype="virtual", channel="vcan0", bitrate=500000)

# Shared data file
DATA_FILE = "/tmp/ev_current.json"

print("=" * 60)
print("🌉 CAN Current Bridge Starting...")
print("=" * 60)
print("Reading from: CAN 0x300")
print(f"Writing to: {DATA_FILE}")
print()

# Initialize file
with open(DATA_FILE, 'w') as f:
    json.dump({"timestamp": 0, "current": 0}, f)

while True:
    msg = bus_rx.recv(timeout=0.5)
    if msg and msg.arbitration_id == 0x300:
        if len(msg.data) >= 2:
            current = msg.data[0] + (msg.data[1] << 8)
            data = {
                "timestamp": time.time(),
                "current": current
            }
            with open(DATA_FILE, 'w') as f:
                json.dump(data, f)
            print(f"📊 BRIDGE: {current}A")
