"""
Run server and client together
"""

import asyncio
import subprocess
import time
import sys

async def main():
    # Start server in subprocess
    print("Starting server...")
    server_proc = subprocess.Popen(
        [sys.executable, "server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for server to start
    print("Waiting for server to start...")
    await asyncio.sleep(3)
    
    # Run client
    print("Running client...")
    client_proc = subprocess.run(
        [
            sys.executable, 
            "tests/client.py",
            "--url", "ws://localhost:8000",
            "--scenario", "normal",
            "--count", "3",
            "--out", "test_output.csv"
        ]
    )
    
    # Give some time for any remaining operations
    await asyncio.sleep(2)
    
    # Stop server
    print("Stopping server...")
    server_proc.terminate()
    server_proc.wait(timeout=5)
    
    print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
