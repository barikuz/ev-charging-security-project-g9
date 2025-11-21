"""
V2G (Vehicle-to-Grid) Communication Module
Implements ISO 15118 protocol simulation
"""

import logging
import asyncio
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class V2GMessage(Enum):
    """V2G message types (ISO 15118)"""
    DISCOVERY_REQ = "DiscoveryReq"
    DISCOVERY_RES = "DiscoveryRes"
    SERVICE_DISCOVERY_REQ = "ServiceDiscoveryReq"
    SERVICE_DISCOVERY_RES = "ServiceDiscoveryRes"
    CHARGING_STATUS_REQ = "ChargingStatusReq"
    CHARGING_STATUS_RES = "ChargingStatusRes"
    POWER_DELIVERY_REQ = "PowerDeliveryReq"
    POWER_DELIVERY_RES = "PowerDeliveryRes"
    SESSION_START_REQ = "SessionStartReq"
    SESSION_START_RES = "SessionStartRes"
    SESSION_STOP_REQ = "SessionStopReq"
    SESSION_STOP_RES = "SessionStopRes"


class V2GAuthType(Enum):
    """V2G authentication types"""
    EIM = "EIM"  # External Identification Means
    PNC = "PNC"  # Plug and Charge


@dataclass
class V2GConfig:
    """V2G configuration"""
    protocol_version: str = "2020"  # ISO 15118-2 or later
    security_level: str = "TLS"
    max_power_ac: int = 16000  # Watts
    max_power_dc: int = 350000  # Watts
    max_current_ac: int = 32  # Amps
    max_current_dc: int = 200  # Amps


class V2GCommunicator:
    """V2G protocol communicator"""
    
    def __init__(self, config: Optional[V2GConfig] = None):
        self.config = config or V2GConfig()
        self.session_id: Optional[str] = None
        self.session_active = False
        self.authenticated = False
        self.message_handlers: Dict[str, callable] = {}
        self.message_log: List[Dict[str, Any]] = []
        self._setup_handlers()
        
    def _setup_handlers(self) -> None:
        """Setup default message handlers"""
        self.message_handlers[V2GMessage.DISCOVERY_REQ.value] = self._handle_discovery_req
        self.message_handlers[V2GMessage.SERVICE_DISCOVERY_REQ.value] = self._handle_service_discovery_req
        self.message_handlers[V2GMessage.SESSION_START_REQ.value] = self._handle_session_start_req
        self.message_handlers[V2GMessage.CHARGING_STATUS_REQ.value] = self._handle_charging_status_req
        self.message_handlers[V2GMessage.POWER_DELIVERY_REQ.value] = self._handle_power_delivery_req
        self.message_handlers[V2GMessage.SESSION_STOP_REQ.value] = self._handle_session_stop_req
        
    def register_handler(self, message_type: str, handler: callable) -> None:
        """Register a message handler"""
        self.message_handlers[message_type] = handler
        
    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming V2G message"""
        msg_type = message.get("type")
        
        self.message_log.append({
            "type": msg_type,
            "timestamp": datetime.now().isoformat(),
            "message": message
        })
        
        if msg_type in self.message_handlers:
            try:
                handler = self.message_handlers[msg_type]
                if asyncio.iscoroutinefunction(handler):
                    return await handler(message)
                else:
                    return handler(message)
            except Exception as e:
                logger.error(f"Error handling V2G message: {e}")
                return self._create_error_response(msg_type, str(e))
                
        logger.warning(f"Unknown V2G message type: {msg_type}")
        return self._create_error_response(msg_type, "Unknown message type")
        
    async def _handle_discovery_req(self, message: Dict) -> Dict:
        """Handle DiscoveryReq"""
        logger.info("V2G Discovery Request received")
        return {
            "type": V2GMessage.DISCOVERY_RES.value,
            "chargePointAddress": "192.168.1.100",
            "chargePointPort": 15118,
            "securityLevel": self.config.security_level,
        }
        
    async def _handle_service_discovery_req(self, message: Dict) -> Dict:
        """Handle ServiceDiscoveryReq"""
        logger.info("V2G Service Discovery Request received")
        return {
            "type": V2GMessage.SERVICE_DISCOVERY_RES.value,
            "services": [
                {
                    "serviceID": 1,
                    "serviceName": "AC Charging",
                    "maxPower": self.config.max_power_ac,
                    "maxCurrent": self.config.max_current_ac,
                },
                {
                    "serviceID": 2,
                    "serviceName": "DC Charging",
                    "maxPower": self.config.max_power_dc,
                    "maxCurrent": self.config.max_current_dc,
                },
            ]
        }
        
    async def _handle_session_start_req(self, message: Dict) -> Dict:
        """Handle SessionStartReq"""
        from uuid import uuid4
        self.session_id = str(uuid4())
        self.session_active = True
        logger.info(f"V2G session started: {self.session_id}")
        
        return {
            "type": V2GMessage.SESSION_START_RES.value,
            "sessionID": self.session_id,
            "evseID": "EVSE-001",
            "responseCode": "OK"
        }
        
    async def _handle_charging_status_req(self, message: Dict) -> Dict:
        """Handle ChargingStatusReq"""
        if not self.session_active:
            return self._create_error_response(V2GMessage.CHARGING_STATUS_REQ.value, "No active session")
            
        return {
            "type": V2GMessage.CHARGING_STATUS_RES.value,
            "sessionID": self.session_id,
            "chargingState": "Active",
            "currentPower": message.get("requestedPower", 0),
            "responseCode": "OK"
        }
        
    async def _handle_power_delivery_req(self, message: Dict) -> Dict:
        """Handle PowerDeliveryReq"""
        if not self.session_active:
            return self._create_error_response(V2GMessage.POWER_DELIVERY_REQ.value, "No active session")
            
        return {
            "type": V2GMessage.POWER_DELIVERY_RES.value,
            "sessionID": self.session_id,
            "responseCode": "OK",
            "powerAvailable": True
        }
        
    async def _handle_session_stop_req(self, message: Dict) -> Dict:
        """Handle SessionStopReq"""
        self.session_active = False
        logger.info(f"V2G session stopped: {self.session_id}")
        
        return {
            "type": V2GMessage.SESSION_STOP_RES.value,
            "responseCode": "OK"
        }
        
    def _create_error_response(self, message_type: str, error: str) -> Dict:
        """Create error response"""
        return {
            "type": f"{message_type}Error",
            "errorCode": "ERROR",
            "errorDescription": error
        }
        
    async def authenticate(self, auth_type: V2GAuthType, credentials: Dict) -> bool:
        """Authenticate V2G connection"""
        logger.info(f"V2G authentication attempt with {auth_type.value}")
        self.authenticated = True
        return True
        
    def get_session_info(self) -> Dict[str, Any]:
        """Get current session information"""
        return {
            "sessionID": self.session_id,
            "sessionActive": self.session_active,
            "authenticated": self.authenticated,
            "protocolVersion": self.config.protocol_version,
            "messageCount": len(self.message_log)
        }
        
    def get_message_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get message log"""
        return self.message_log[-limit:]
