#!/usr/bin/env python3
"""Quick test to check if CSMS is responding"""
import asyncio
import websockets

async def test_csms():
    try:
        print("🔗 Connecting to CSMS...")
        ws = await asyncio.wait_for(
            websockets.connect("ws://127.0.0.1:9000/TEST", subprotocols=["ocpp1.6"]),
            timeout=5
        )
        print("✅ Connected to CSMS!")
        await ws.close()
        return True
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_csms())
    exit(0 if result else 1)
