import asyncio
import logging
import sys
import os

# Add project root to path to allow direct execution
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.simulator.main import EVChargingSimulator, SimulatorConfig

async def test_thermal_anomaly():
    # Configure logging
    log_file = "thermal_anomaly_test.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, mode='w'),
            logging.StreamHandler()
        ]
    )
    print(f"Logging to {log_file}")
    
    # Create simulator
    config = SimulatorConfig()
    simulator = EVChargingSimulator(config)
    
    print("Starting Thermal Anomaly Simulation...")
    
    # Start simulator
    await simulator.start()
    
    # Inject thermal anomaly
    print("Injecting Thermal Runaway Anomaly...")
    simulator.inject_anomaly("THERMAL_RUNAWAY", severity="HIGH")
    
    # Run simulation for 60 seconds to see temperature rise
    try:
        await simulator.simulate_charging_session(duration=60.0, anomalies=["THERMAL_RUNAWAY"])
    except Exception as e:
        print(f"Simulation finished with: {e}")
        
    stats = simulator.get_statistics()
    print("\nSimulation Statistics:")
    print(stats)

if __name__ == "__main__":
    asyncio.run(test_thermal_anomaly())
