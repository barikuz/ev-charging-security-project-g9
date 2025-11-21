"""
Anomaly Injection Module
Handles anomaly generation and attack simulation
"""

import logging
import asyncio
import random
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class AnomalyType(Enum):
    """Types of anomalies that can be injected"""
    CAN_INJECTION = "can_injection"
    CAN_FUZZING = "can_fuzzing"
    MESSAGE_DELAY = "message_delay"
    MESSAGE_DUPLICATION = "message_duplication"
    MESSAGE_MODIFICATION = "message_modification"
    SPOOFING = "spoofing"
    REPLAY_ATTACK = "replay_attack"
    DOS_ATTACK = "dos_attack"
    TIMING_ATTACK = "timing_attack"
    INVALID_STATE = "invalid_state"
    POWER_ANOMALY = "power_anomaly"
    THERMAL_RUNAWAY = "thermal_runaway"


class AttackSeverity(Enum):
    """Attack severity levels"""
    LOW = 0.1
    MEDIUM = 0.5
    HIGH = 0.9


@dataclass
class AnomalyConfig:
    """Anomaly configuration"""
    enabled: bool = True
    injection_rate: float = 0.1  # 0.0 to 1.0
    intensity: float = 0.5  # 0.0 to 1.0
    duration: float = 60.0  # seconds
    random_seed: Optional[int] = None


@dataclass
class AnomalyEvent:
    """Represents an injected anomaly event"""
    timestamp: float
    anomaly_type: AnomalyType
    severity: AttackSeverity
    target_protocol: str  # "can", "ocpp", "v2g"
    description: str
    affected_message_id: Optional[str] = None


class AnomalyInjector:
    """Manages anomaly injection for testing"""
    
    def __init__(self, config: Optional[AnomalyConfig] = None):
        self.config = config or AnomalyConfig()
        self.active_anomalies: Dict[str, AnomalyEvent] = {}
        self.anomaly_history: List[AnomalyEvent] = []
        self.running = False
        
        if self.config.random_seed is not None:
            random.seed(self.config.random_seed)
            
    def inject(self, anomaly_type: str, 
               protocol: str = "can",
               severity: AttackSeverity = AttackSeverity.MEDIUM,
               duration: Optional[float] = None) -> bool:
        """Inject an anomaly"""
        if not self.config.enabled:
            logger.warning("Anomaly injection is disabled")
            return False
            
        try:
            anom_type = AnomalyType[anomaly_type.upper()]
            event = AnomalyEvent(
                timestamp=datetime.now().timestamp(),
                anomaly_type=anom_type,
                severity=severity,
                target_protocol=protocol,
                description=f"Injected {anom_type.value} with severity {severity.name}"
            )
            
            anomaly_id = f"{anom_type.value}_{len(self.anomaly_history)}"
            self.active_anomalies[anomaly_id] = event
            self.anomaly_history.append(event)
            
            logger.info(f"Anomaly injected: {anomaly_id} ({severity.name})")
            return True
        except KeyError:
            logger.error(f"Unknown anomaly type: {anomaly_type}")
            return False
            
    def remove_anomaly(self, anomaly_id: str) -> bool:
        """Remove an active anomaly"""
        if anomaly_id in self.active_anomalies:
            del self.active_anomalies[anomaly_id]
            logger.info(f"Anomaly removed: {anomaly_id}")
            return True
        return False
        
    def get_active_anomalies(self) -> List[AnomalyEvent]:
        """Get list of active anomalies"""
        return list(self.active_anomalies.values())
        
    def should_inject(self) -> bool:
        """Determine if anomaly should be injected based on injection rate"""
        return random.random() < self.config.injection_rate
        
    def modify_can_message(self, data: bytes, severity: float = 0.5) -> bytes:
        """Modify CAN message data based on severity"""
        data_list = list(data)
        num_bytes_to_modify = max(1, int(len(data_list) * severity))
        
        indices = random.sample(range(len(data_list)), num_bytes_to_modify)
        for idx in indices:
            data_list[idx] = random.randint(0, 255)
            
        return bytes(data_list)
        
    def create_dos_messages(self, count: int = 100) -> List[Dict[str, Any]]:
        """Create messages for DoS attack"""
        messages = []
        for i in range(count):
            messages.append({
                "id": random.randint(0x000, 0x7FF),
                "data": bytes([random.randint(0, 255) for _ in range(8)]),
                "timestamp": datetime.now().timestamp() + (i * 0.001)
            })
        return messages
        
    def create_spoofed_message(self, original_id: int, payload: bytes) -> Dict[str, Any]:
        """Create a spoofed CAN message"""
        return {
            "id": original_id,
            "data": payload,
            "spoofed": True,
            "timestamp": datetime.now().timestamp()
        }
        
    def get_statistics(self) -> Dict[str, Any]:
        """Get anomaly injection statistics"""
        anomaly_counts = {}
        for event in self.anomaly_history:
            key = event.anomaly_type.value
            anomaly_counts[key] = anomaly_counts.get(key, 0) + 1
            
        return {
            "total_injected": len(self.anomaly_history),
            "active_anomalies": len(self.active_anomalies),
            "anomaly_counts": anomaly_counts,
            "injection_rate": self.config.injection_rate,
            "intensity": self.config.intensity
        }


class AttackScenario:
    """Defines an attack scenario"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.anomalies: List[Dict[str, Any]] = []
        
    def add_anomaly(self, anomaly_type: str, protocol: str, 
                    severity: AttackSeverity, delay: float = 0) -> None:
        """Add anomaly to scenario"""
        self.anomalies.append({
            "type": anomaly_type,
            "protocol": protocol,
            "severity": severity,
            "delay": delay
        })
        
    async def execute(self, injector: AnomalyInjector) -> bool:
        """Execute the attack scenario"""
        logger.info(f"Executing attack scenario: {self.name}")
        
        for anomaly in self.anomalies:
            await asyncio.sleep(anomaly["delay"])
            injector.inject(
                anomaly["type"],
                protocol=anomaly["protocol"],
                severity=anomaly["severity"]
            )
            
        logger.info(f"Attack scenario completed: {self.name}")
        return True


# Predefined attack scenarios
class AttackScenarios:
    """Collection of predefined attack scenarios"""
    
    @staticmethod
    def can_injection_attack() -> AttackScenario:
        """CAN message injection attack"""
        scenario = AttackScenario(
            "CAN Injection Attack",
            "Injects malicious CAN messages to disrupt charging"
        )
        scenario.add_anomaly("CAN_INJECTION", "can", AttackSeverity.HIGH, 0)
        scenario.add_anomaly("CAN_FUZZING", "can", AttackSeverity.HIGH, 1)
        return scenario
        
    @staticmethod
    def dos_attack() -> AttackScenario:
        """Denial of Service attack"""
        scenario = AttackScenario(
            "DoS Attack",
            "Floods the charging system with messages"
        )
        scenario.add_anomaly("DOS_ATTACK", "can", AttackSeverity.HIGH, 0)
        scenario.add_anomaly("DOS_ATTACK", "ocpp", AttackSeverity.MEDIUM, 2)
        return scenario
        
    @staticmethod
    def replay_attack() -> AttackScenario:
        """Replay attack"""
        scenario = AttackScenario(
            "Replay Attack",
            "Replays captured valid messages to cause state confusion"
        )
        scenario.add_anomaly("REPLAY_ATTACK", "ocpp", AttackSeverity.MEDIUM, 0)
        scenario.add_anomaly("REPLAY_ATTACK", "v2g", AttackSeverity.MEDIUM, 5)
        return scenario
        
    @staticmethod
    def spoofing_attack() -> AttackScenario:
        """Spoofing attack"""
        scenario = AttackScenario(
            "Spoofing Attack",
            "Sends messages with false identity"
        )
        scenario.add_anomaly("SPOOFING", "can", AttackSeverity.HIGH, 0)
        scenario.add_anomaly("SPOOFING", "ocpp", AttackSeverity.HIGH, 1)
        return scenario
        
    @staticmethod
    def thermal_attack() -> AttackScenario:
        """Thermal runaway attack (High Resistance Connector)"""
        scenario = AttackScenario(
            "Thermal Runaway Attack",
            "Simulates high resistance contact causing rapid heating"
        )
        scenario.add_anomaly("THERMAL_RUNAWAY", "physical", AttackSeverity.HIGH, 5)
        return scenario
