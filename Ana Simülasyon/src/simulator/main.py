"""
Main EV Charging Simulator
Orchestrates CAN bus, OCPP, and V2G communication
"""

import logging
import asyncio
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from datetime import datetime

from src.can_bus.simulator import CANBusSimulator, CANConfig, EVCANMessages
from src.ocpp.protocol import OCPPServer, OCPPClient, OCPPConfig
from src.v2g.communicator import V2GCommunicator, V2GConfig
from src.anomalies.injector import AnomalyInjector, AnomalyConfig, AttackScenarios

logger = logging.getLogger(__name__)


@dataclass
class SimulatorConfig:
    """Main simulator configuration"""
    name: str = "EV Charging Simulator"
    can_enabled: bool = True
    ocpp_enabled: bool = True
    v2g_enabled: bool = True
    anomaly_enabled: bool = True
    
    can_config: Optional[CANConfig] = None
    ocpp_config: Optional[OCPPConfig] = None
    v2g_config: Optional[V2GConfig] = None
    anomaly_config: Optional[AnomalyConfig] = None
    
    def __post_init__(self):
        if self.can_config is None:
            self.can_config = CANConfig()
        if self.ocpp_config is None:
            self.ocpp_config = OCPPConfig()
        if self.v2g_config is None:
            self.v2g_config = V2GConfig()
        if self.anomaly_config is None:
            self.anomaly_config = AnomalyConfig()


class EVChargingSimulator:
    """Main simulator orchestrating all charging systems"""
    
    def __init__(self, config: Optional[SimulatorConfig] = None, config_path: Optional[str] = None):
        self.config = config or SimulatorConfig()
        self.can_bus: Optional[CANBusSimulator] = None
        self.ocpp_server: Optional[OCPPServer] = None
        self.ocpp_client: Optional[OCPPClient] = None
        self.v2g: Optional[V2GCommunicator] = None
        self.anomaly_injector: Optional[AnomalyInjector] = None
        
        self.running = False
        self.start_time: Optional[float] = None
        self.statistics = {
            "can_messages_sent": 0,
            "ocpp_messages_sent": 0,
            "v2g_messages_sent": 0,
            "anomalies_injected": 0,
            "errors": 0,
        }
        
        if config_path:
            self._load_config(config_path)
            
        self._initialize_components()
        
    def _load_config(self, config_path: str) -> None:
        """Load configuration from YAML file"""
        try:
            import json
            with open(config_path, 'r') as f:
                config_data = json.load(f)
                logger.info(f"Configuration loaded from {config_path}")
        except Exception as e:
            logger.warning(f"Could not load config file: {e}, using defaults")
            
    def _initialize_components(self) -> None:
        """Initialize all simulator components"""
        logger.info("Initializing simulator components...")
        
        if self.config.can_enabled:
            self.can_bus = CANBusSimulator(self.config.can_config)
            logger.info("CAN bus simulator initialized")
            
        if self.config.ocpp_enabled:
            self.ocpp_server = OCPPServer(self.config.ocpp_config)
            self.ocpp_client = OCPPClient(self.config.ocpp_config)
            logger.info("OCPP server and client initialized")
            
        if self.config.v2g_enabled:
            self.v2g = V2GCommunicator(self.config.v2g_config)
            logger.info("V2G communicator initialized")
            
        if self.config.anomaly_enabled:
            self.anomaly_injector = AnomalyInjector(self.config.anomaly_config)
            logger.info("Anomaly injector initialized")
            
    async def start(self) -> None:
        """Start the simulator"""
        self.running = True
        self.start_time = datetime.now().timestamp()
        logger.info(f"Starting EV Charging Simulator: {self.config.name}")
        
        if self.can_bus:
            self.can_bus.start()
            
        if self.ocpp_server:
            await self.ocpp_server.start()
            
        if self.ocpp_client:
            await self.ocpp_client.connect()
            
    async def stop(self) -> None:
        """Stop the simulator"""
        self.running = False
        logger.info("Stopping EV Charging Simulator")
        
        if self.can_bus:
            self.can_bus.stop()
            
        if self.ocpp_server:
            await self.ocpp_server.stop()
            
        if self.ocpp_client:
            await self.ocpp_client.disconnect()
            
    async def simulate_charging_session(self, duration: float = 300.0, anomalies: Optional[List[str]] = None) -> Dict[str, Any]:
        """Simulate a complete charging session"""
        logger.info(f"Starting charging session (duration: {duration}s)")
        
        await self.start()
        start_time = datetime.now().timestamp()
        
        try:
            # Simulate charging phases
            await self._simulate_connection_phase()
            await self._simulate_charging_phase(duration * 0.6)
            
            if anomalies and self.anomaly_injector:
                for anomaly in anomalies:
                    self.anomaly_injector.inject(anomaly)
                    
            await self._simulate_charging_phase(duration * 0.4)
            await self._simulate_disconnection_phase()
            
        except Exception as e:
            logger.error(f"Error during charging session: {e}")
            self.statistics["errors"] += 1
            
        finally:
            await self.stop()
            
        elapsed = datetime.now().timestamp() - start_time
        return {
            "duration": elapsed,
            "statistics": self.statistics,
            "status": "completed"
        }
        
    async def _simulate_connection_phase(self) -> None:
        """Simulate vehicle connection phase"""
        logger.info("Simulating connection phase...")
        
        if self.v2g:
            discovery_msg = {
                "type": "DiscoveryReq",
                "vehicleID": "TEST-EV-001"
            }
            await self.v2g.handle_message(discovery_msg)
            
        if self.ocpp_client:
            await self.ocpp_client.send_boot_notification()
            
        await asyncio.sleep(1)
        
    async def _simulate_charging_phase(self, duration: float) -> None:
        """Simulate active charging phase"""
        logger.info(f"Simulating charging phase ({duration}s)...")
        
        start_time = datetime.now().timestamp()
        soc = 20
        
        while datetime.now().timestamp() - start_time < duration and self.running:
            # Update battery status via CAN
            if self.can_bus:
                msg = EVCANMessages.battery_status(
                    soc=int(min(100, soc)),
                    temperature=35,
                    voltage=400
                )
                await self.can_bus.send_message(msg)
                self.statistics["can_messages_sent"] += 1
                
            # Send OCPP meter values
            if self.ocpp_client:
                await self.ocpp_client.send_heartbeat()
                self.statistics["ocpp_messages_sent"] += 1
                
            # Send V2G charging status
            if self.v2g:
                status_msg = {
                    "type": "ChargingStatusReq",
                    "requestedPower": 10000
                }
                await self.v2g.handle_message(status_msg)
                self.statistics["v2g_messages_sent"] += 1
                
            soc += 0.5
            await asyncio.sleep(1)
            
    async def _simulate_disconnection_phase(self) -> None:
        """Simulate vehicle disconnection phase"""
        logger.info("Simulating disconnection phase...")
        
        if self.ocpp_client:
            await self.ocpp_client.stop_transaction(meter_stop=80000)
            
        if self.v2g:
            stop_msg = {"type": "SessionStopReq"}
            await self.v2g.handle_message(stop_msg)
            
        await asyncio.sleep(1)
        
    def inject_anomaly(self, anomaly_type: str, severity: str = "MEDIUM") -> bool:
        """Inject an anomaly into the simulation"""
        if not self.anomaly_injector:
            logger.warning("Anomaly injector not available")
            return False
            
        from src.anomalies.injector import AttackSeverity
        severity_map = {
            "LOW": AttackSeverity.LOW,
            "MEDIUM": AttackSeverity.MEDIUM,
            "HIGH": AttackSeverity.HIGH,
        }
        
        return self.anomaly_injector.inject(
            anomaly_type,
            severity=severity_map.get(severity, AttackSeverity.MEDIUM)
        )
        
    async def execute_attack_scenario(self, scenario_name: str) -> bool:
        """Execute a predefined attack scenario"""
        if not self.anomaly_injector:
            logger.warning("Anomaly injector not available")
            return False
            
        scenarios_map = {
            "can_injection": AttackScenarios.can_injection_attack,
            "dos": AttackScenarios.dos_attack,
            "replay": AttackScenarios.replay_attack,
            "spoofing": AttackScenarios.spoofing_attack,
        }
        
        if scenario_name not in scenarios_map:
            logger.error(f"Unknown attack scenario: {scenario_name}")
            return False
            
        scenario = scenarios_map[scenario_name]()
        return await scenario.execute(self.anomaly_injector)
        
    def get_statistics(self) -> Dict[str, Any]:
        """Get simulator statistics"""
        elapsed = 0
        if self.start_time:
            elapsed = datetime.now().timestamp() - self.start_time
            
        stats = {
            "elapsed_time": elapsed,
            "is_running": self.running,
            "messages": self.statistics.copy(),
        }
        
        if self.can_bus:
            stats["can_bus"] = self.can_bus.get_statistics()
            
        if self.anomaly_injector:
            stats["anomalies"] = self.anomaly_injector.get_statistics()
            
        if self.v2g:
            stats["v2g"] = self.v2g.get_session_info()
            
        return stats


async def main():
    """Main entry point for simulation"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create simulator
    config = SimulatorConfig()
    simulator = EVChargingSimulator(config)
    
    # Run a test charging session
    try:
        result = await simulator.simulate_charging_session(duration=30.0)
        print("\nSimulation completed!")
        print(f"Statistics: {result}")
    except KeyboardInterrupt:
        print("\nSimulation interrupted")


if __name__ == "__main__":
    asyncio.run(main())
