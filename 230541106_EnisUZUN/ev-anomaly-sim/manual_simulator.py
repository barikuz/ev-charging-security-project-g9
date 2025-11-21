#!/usr/bin/env python3
"""
Manual Anomaly Simulator
Sends CAN commands directly to charger to demonstrate anomaly pattern
NO OCPP - direct CAN control
"""
import can
import time

print("=" * 60)
print("🎭 Manual Anomaly Simulator")
print("=" * 60)

# Connect to same CAN bus as charger
bus = can.interface.Bus(interface="virtual", channel=0)
print("✅ CAN bus connected")
print()

def send_start():
    """Send START command (0x200)"""
    msg = can.Message(arbitration_id=0x200, data=[], is_extended_id=False)
    bus.send(msg)
    print("📤 Sent: START (0x200)")

def send_stop():
    """Send STOP command (0x201)"""
    msg = can.Message(arbitration_id=0x201, data=[], is_extended_id=False)
    bus.send(msg)
    print("📤 Sent: STOP (0x201)")

def send_limit(amps):
    """Send current limit (0x210)"""
    msg = can.Message(
        arbitration_id=0x210,
        data=[amps & 0xFF, (amps >> 8) & 0xFF],
        is_extended_id=False
    )
    bus.send(msg)
    print(f"📤 Sent: SET_LIMIT {amps}A (0x210)")

print("🔄 Starting Anomaly Cycle...")
print()

cycle = 1
while True:
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"🔄 Cycle #{cycle}")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # Phase 1: Set limit to 0A
    print("📉 Phase 1: Setting limit to 0A")
    send_limit(0)
    send_start()
    print("⏱️  Waiting 10 seconds...")
    time.sleep(10)
    
    # Phase 2: Set limit to 32A
    print("📈 Phase 2: Setting limit to 32A")
    send_limit(32)
    print("⏱️  Waiting 10 seconds...")
    time.sleep(10)
    
    # Phase 3: Stop
    print("🛑 Phase 3: Stopping")
    send_stop()
    print("⏱️  Waiting 5 seconds...")
    time.sleep(5)
    
    cycle += 1
    print()
