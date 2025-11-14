"""
Integration Example - Complete EV Charging Simulation
Demonstrates full workflow with all components
"""

import asyncio
import logging
from src.simulator.main import EVChargingSimulator
from src.anomalies.injector import AttackSeverity, AttackScenarios

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def example_1_basic_charging():
    """Example 1: Basic charging session"""
    logger.info("=" * 60)
    logger.info("EXAMPLE 1: Basic Charging Session")
    logger.info("=" * 60)
    
    simulator = EVChargingSimulator()
    result = await simulator.simulate_charging_session(duration=30)
    
    logger.info(f"Session Duration: {result['duration']:.2f}s")
    logger.info(f"Status: {result['status']}")
    logger.info(f"CAN Messages: {result['statistics']['can_messages_sent']}")
    logger.info(f"OCPP Messages: {result['statistics']['ocpp_messages_sent']}")
    logger.info(f"V2G Messages: {result['statistics']['v2g_messages_sent']}")


async def example_2_charging_with_anomalies():
    """Example 2: Charging session with injected anomalies"""
    logger.info("=" * 60)
    logger.info("EXAMPLE 2: Charging with Anomalies")
    logger.info("=" * 60)
    
    simulator = EVChargingSimulator()
    
    result = await simulator.simulate_charging_session(
        duration=30,
        anomalies=["CAN_INJECTION", "SPOOFING"]
    )
    
    stats = result['statistics']
    logger.info(f"Anomalies Injected: {stats['anomalies_injected']}")
    logger.info(f"Errors: {stats['errors']}")


async def example_3_attack_scenarios():
    """Example 3: Execute predefined attack scenarios"""
    logger.info("=" * 60)
    logger.info("EXAMPLE 3: Attack Scenarios")
    logger.info("=" * 60)
    
    simulator = EVChargingSimulator()
    await simulator.start()
    
    # List of attack scenarios
    scenarios = ["can_injection", "dos", "replay", "spoofing"]
    
    for scenario in scenarios:
        logger.info(f"Executing: {scenario} attack...")
        success = await simulator.execute_attack_scenario(scenario)
        logger.info(f"Result: {'SUCCESS' if success else 'FAILED'}")
        await asyncio.sleep(2)
    
    await simulator.stop()


async def example_4_manual_anomaly_injection():
    """Example 4: Manual anomaly injection control"""
    logger.info("=" * 60)
    logger.info("EXAMPLE 4: Manual Anomaly Injection")
    logger.info("=" * 60)
    
    simulator = EVChargingSimulator()
    await simulator.start()
    
    # Inject different anomalies with various severities
    anomalies = [
        ("CAN_INJECTION", "HIGH"),
        ("DOS_ATTACK", "MEDIUM"),
        ("REPLAY_ATTACK", "LOW"),
        ("TIMING_ATTACK", "HIGH"),
    ]
    
    for anom_type, severity in anomalies:
        result = simulator.inject_anomaly(anom_type, severity)
        logger.info(f"Injected {anom_type} ({severity}): {result}")
        await asyncio.sleep(1)
    
    # Get current statistics
    stats = simulator.get_statistics()
    logger.info(f"Active Anomalies: {stats['anomalies']['active_anomalies']}")
    logger.info(f"Total Injected: {stats['anomalies']['total_injected']}")
    
    await simulator.stop()


async def example_5_monitoring():
    """Example 5: Real-time monitoring during session"""
    logger.info("=" * 60)
    logger.info("EXAMPLE 5: Monitoring")
    logger.info("=" * 60)
    
    simulator = EVChargingSimulator()
    await simulator.start()
    
    logger.info("Starting monitoring for 10 seconds...")
    for i in range(10):
        stats = simulator.get_statistics()
        logger.info(f"[{i+1}s] CAN: {stats['messages']['can_messages_sent']}, "
                   f"OCPP: {stats['messages']['ocpp_messages_sent']}, "
                   f"V2G: {stats['messages']['v2g_messages_sent']}")
        await asyncio.sleep(1)
    
    await simulator.stop()


async def example_6_custom_configuration():
    """Example 6: Using custom configuration"""
    logger.info("=" * 60)
    logger.info("EXAMPLE 6: Custom Configuration")
    logger.info("=" * 60)
    
    from src.simulator.main import SimulatorConfig
    from src.can_bus.simulator import CANConfig
    from src.anomalies.injector import AnomalyConfig
    
    # Create custom config
    can_config = CANConfig(channel="vcan_custom", bitrate=1000000)
    anomaly_config = AnomalyConfig(enabled=True, injection_rate=0.3)
    
    config = SimulatorConfig(
        name="Custom Charging Simulator",
        can_enabled=True,
        ocpp_enabled=True,
        v2g_enabled=True,
        can_config=can_config,
        anomaly_config=anomaly_config,
    )
    
    simulator = EVChargingSimulator(config)
    logger.info(f"Simulator: {simulator.config.name}")
    logger.info(f"CAN Channel: {simulator.config.can_config.channel}")
    logger.info(f"Anomaly Rate: {simulator.config.anomaly_config.injection_rate}")


async def main():
    """Run all examples"""
    try:
        # Uncomment the examples you want to run
        
        await example_1_basic_charging()
        await asyncio.sleep(2)
        
        await example_2_charging_with_anomalies()
        await asyncio.sleep(2)
        
        await example_3_attack_scenarios()
        await asyncio.sleep(2)
        
        await example_4_manual_anomaly_injection()
        await asyncio.sleep(2)
        
        await example_5_monitoring()
        await asyncio.sleep(2)
        
        await example_6_custom_configuration()
        
        logger.info("=" * 60)
        logger.info("ALL EXAMPLES COMPLETED!")
        logger.info("=" * 60)
        
    except KeyboardInterrupt:
        logger.info("Examples interrupted by user")
    except Exception as e:
        logger.error(f"Error running examples: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
