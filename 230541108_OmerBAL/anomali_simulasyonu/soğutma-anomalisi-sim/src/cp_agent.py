# This file acts as a simple OCPP client that parses incoming commands and writes CAN frames to vcan0.

import can
import asyncio
import json
import os

class CPAagent:
    def __init__(self, channel='vcan0'):
        self.bus = can.interface.Bus(channel=channel, bustype='socketcan')

    async def parse_command(self, command):
        # Parse the incoming command and prepare CAN frame
        try:
            command_data = json.loads(command)
            can_id = command_data.get('can_id', 0x123)  # Default CAN ID
            data = command_data.get('data', bytearray())
            self.send_can_frame(can_id, data)
        except json.JSONDecodeError:
            print("Invalid command format")

    def send_can_frame(self, can_id, data):
        # Send CAN frame to vcan0
        msg = can.Message(arbitration_id=can_id, data=data, is_extended_id=False)
        try:
            self.bus.send(msg)
            print(f"Sent CAN frame: ID={hex(can_id)}, Data={data.hex()}")
        except can.CanError:
            print("Failed to send CAN frame")

async def main():
    agent = CPAagent()
    while True:
        command = await asyncio.get_event_loop().run_in_executor(None, input, "Enter command (JSON format): ")
        await agent.parse_command(command)

if __name__ == "__main__":
    asyncio.run(main())