# This file simulates the Central System Management Service (CSMS) for the OCPP protocol.
# It listens for commands and can trigger RemoteStart via CLI.

import asyncio
import websockets
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def csms_handler(websocket, path):
    async for message in websocket:
        logging.info(f"Received message: {message}")
        command = json.loads(message)

        if command.get("action") == "RemoteStart":
            await websocket.send(json.dumps({"status": "Accepted", "action": "RemoteStart"}))
            logging.info("Triggered RemoteStart command.")

async def main():
    server = await websockets.serve(csms_handler, "localhost", 8765)
    logging.info("CSMS server started, waiting for commands...")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())