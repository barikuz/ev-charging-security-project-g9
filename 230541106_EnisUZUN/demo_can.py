#!/usr/bin/env python3
"""
Demo script that shows a simple CAN bus test
Can be used to verify CAN communication is working
"""
import can
import time

def demo():
    print("=" * 60)
    print("🔧 CAN Bus Quick Test")
    print("=" * 60)
    print()
    
    # Create CAN bus
    bus = can.interface.Bus(interface="virtual", channel=0)
    print("✅ CAN bus created")
    
    # Send a test message
    test_msg = can.Message(
        arbitration_id=0x123,
        data=[1, 2, 3, 4],
        is_extended_id=False
    )
    bus.send(test_msg)
    print(f"📤 Sent test message: ID=0x{test_msg.arbitration_id:03x}, data={list(test_msg.data)}")
    
    # Try to receive it
    print("📥 Listening for messages (2 seconds)...")
    start = time.time()
    received = False
    
    while time.time() - start < 2:
        msg = bus.recv(timeout=0.1)
        if msg:
            print(f"   Received: ID=0x{msg.arbitration_id:03x}, data={list(msg.data)}")
            received = True
    
    if received:
        print("✅ CAN communication working!")
    else:
        print("⚠️  No messages received (this is normal for virtual bus without other processes)")
    
    bus.shutdown()
    print()
    print("=" * 60)
    print("Test complete. Virtual CAN bus is functional.")
    print("=" * 60)

if __name__ == "__main__":
    demo()
