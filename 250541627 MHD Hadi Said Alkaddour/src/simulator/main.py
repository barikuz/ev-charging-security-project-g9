"""
Main EV Charging Simulator
Orchestrates CAN bus, OCPP, and V2G communication
"""

import logging
import asyncio
import sys
import os

# Add project root to path to allow direct execution
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from typing import Dict, Optional, Any, List, Tuple
from dataclasses import dataclass
from datetime import datetime

from src.can_bus.simulator import CANBusSimulator, CANConfig, EVCANMessages
from src.ocpp.protocol import OCPPServer, OCPPClient, OCPPConfig
from src.v2g.communicator import V2GCommunicator, V2GConfig
from src.anomalies.injector import AnomalyInjector, AnomalyConfig, AttackScenarios

logger = logging.getLogger(__name__)


class Connector:
    """
    Thermal and electrical model for connector/pin.
    Simulates contact resistance heating.
    """
    def __init__(
        self,
        contact_resistance_ohm: float = 0.00005,  # Default copper
        temp_c: float = 25.0,
        heat_capacity_j_per_c: float = 200.0,
        thermal_resistance_c_per_w: float = 0.5,
    ) -> None:
        self.contact_resistance = contact_resistance_ohm
        self.temp_c = temp_c
        self.heat_capacity = heat_capacity_j_per_c
        self.thermal_resistance = thermal_resistance_c_per_w

    def step(self, current_a: float, dt_s: float, t_amb: float = 25.0) -> Tuple[float, float]:
        """Advance thermal state by dt seconds under current `current_a`."""
        p_loss = (current_a ** 2) * self.contact_resistance
        heat_flow = (self.temp_c - t_amb) / self.thermal_resistance
        dT_dt = (p_loss - heat_flow) / self.heat_capacity
        self.temp_c += dT_dt * dt_s
        return p_loss, dT_dt

    def set_resistance(self, resistance: float) -> None:
        """Update contact resistance (e.g. to simulate degradation or anomaly)"""
        self.contact_resistance = resistance

    def set_properties(self, resistance: float, heat_capacity: float, thermal_resistance: float) -> None:
        """Update all thermal properties"""
        self.contact_resistance = resistance
        self.heat_capacity = heat_capacity
        self.thermal_resistance = thermal_resistance



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
        self.connector = Connector()  # Initialize with default copper contact
        
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
        current_a = 32.0  # Nominal current
        
        while datetime.now().timestamp() - start_time < duration and self.running:
            # Check for thermal anomaly
            if self.anomaly_injector:
                active_anomalies = self.anomaly_injector.get_active_anomalies()
                is_thermal_attack = any(a.anomaly_type.name == "THERMAL_RUNAWAY" for a in active_anomalies)
                
                if is_thermal_attack:
                    # Simulate high resistance (Iron contact)
                    # contact_r = 0.0035, heat_capacity = 120.0, thermal_resistance = 0.4
                    self.connector.set_properties(0.0035, 120.0, 0.4)
                else:
                    # Normal resistance (Copper contact)
                    # contact_r = 0.00005, heat_capacity = 200.0, thermal_resistance = 0.5
                    self.connector.set_properties(0.00005, 200.0, 0.5)
            
            # Update thermal state
            _, dTdt = self.connector.step(current_a, dt_s=1.0)
            
            # Thermal protection logic
            if self.connector.temp_c >= 100.0:
                logger.critical(f"CRITICAL TEMPERATURE: {self.connector.temp_c:.1f}C. Stopping session!")
                self.running = False
                break
            elif self.connector.temp_c >= 80.0:
                logger.warning(f"High temperature warning: {self.connector.temp_c:.1f}C. Derating current.")
                current_a = max(0, current_a - 5.0)
            
            # Update battery status via CAN
            if self.can_bus:
                msg = EVCANMessages.battery_status(
                    soc=int(min(100, soc)),
                    temperature=int(self.connector.temp_c),
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
                    "requestedPower": int(current_a * 230)
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
            "thermal": AttackScenarios.thermal_attack,
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
