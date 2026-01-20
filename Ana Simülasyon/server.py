"""
Simple OCPP Server for testing
"""

import asyncio
import logging
import json
import websockets
from datetime import datetime, timezone
from typing import Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Store connected clients
clients: Set = set()

def now_ts():
    """Get current UTC timestamp"""
    return datetime.now(timezone.utc).isoformat()

async def handle_client(websocket, path):
    """Handle incoming client connections"""
    try:
        addr = getattr(websocket, 'remote_address', 'unknown')
        logger.info(f"Client connected: {addr}")
        clients.add(websocket)
        
        async for message in websocket:
            try:
                data = json.loads(message)
                logger.info(f"Received: {data}")
                
                # Handle OCPP messages
                if isinstance(data, list) and len(data) >= 2:
                    msg_type = data[0]
                    msg_id = data[1]
                    
                    # CALL (2) - Request
                    if msg_type == 2 and len(data) >= 3:
                        action = data[2]
                        payload = data[3] if len(data) > 3 else {}
                        
                        # Respond based on action
                        if action == "BootNotification":
                            response = [3, msg_id, {
                                "status": "Accepted",
                                "currentTime": now_ts(),
                                "interval": 900
                            }]
                        elif action == "StartTransaction":
                            response = [3, msg_id, {
                                "transactionId": 123,
                                "status": "Accepted"
                            }]
                        elif action == "StopTransaction":
                            response = [3, msg_id, {
                                "status": "Accepted"
                            }]
                        elif action == "MeterValues":
                            response = [3, msg_id, {}]
                        elif action == "Heartbeat":
                            response = [3, msg_id, {
                                "currentTime": now_ts()
                            }]
                        else:
                            response = [3, msg_id, {}]
                        
                        logger.info(f"Sending response for {action}: {response}")
                        await websocket.send(json.dumps(response))
                        
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received: {e}")
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
                
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client disconnected")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
    finally:
        clients.discard(websocket)

async def main():
    """Start the server"""
    logger.info("Starting OCPP Server on ws://localhost:8000")
    async with websockets.serve(
        handle_client,
        "localhost",
        8000,
        subprotocols=["ocpp1.6"]
    ):
        logger.info("Server is running. Press Ctrl+C to stop.")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped")
