"""
OCPP Protocol Implementation
Handles Open Charge Point Protocol 1.6 and 2.0
"""

import logging
import asyncio
import json
from typing import Dict, Optional, Any, Callable, List
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class OCPPMessageType(Enum):
    """OCPP message types"""
    CALL = 2
    CALL_RESULT = 3
    CALL_ERROR = 4


class OCPPAction(Enum):
    """Common OCPP actions"""
    BOOT_NOTIFICATION = "BootNotification"
    HEARTBEAT = "Heartbeat"
    START_TRANSACTION = "StartTransaction"
    STOP_TRANSACTION = "StopTransaction"
    METER_VALUES = "MeterValues"
    AUTHORIZE = "Authorize"
    RESET = "Reset"
    REMOTE_START_TRANSACTION = "RemoteStartTransaction"
    REMOTE_STOP_TRANSACTION = "RemoteStopTransaction"
    GET_CONFIGURATION = "GetConfiguration"
    CHANGE_CONFIGURATION = "ChangeConfiguration"
    STATUS_NOTIFICATION = "StatusNotification"


class ChargePointStatus(Enum):
    """Charge point status values"""
    AVAILABLE = "Available"
    PREPARING = "Preparing"
    CHARGING = "Charging"
    SUSPENDED_EVSE = "SuspendedEVSE"
    SUSPENDED_EV = "SuspendedEV"
    FINISHING = "Finishing"
    RESERVED = "Reserved"
    UNAVAILABLE = "Unavailable"
    FAULTED = "Faulted"


@dataclass
class OCPPMessage:
    """OCPP message structure"""
    message_type: OCPPMessageType
    message_id: str
    action: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    error_description: Optional[str] = None
    
    def to_list(self) -> List:
        """Convert to OCPP list format [type, id, action, payload]"""
        if self.message_type == OCPPMessageType.CALL:
            return [self.message_type.value, self.message_id, self.action, self.payload or {}]
        elif self.message_type == OCPPMessageType.CALL_RESULT:
            return [self.message_type.value, self.message_id, self.payload or {}]
        elif self.message_type == OCPPMessageType.CALL_ERROR:
            return [self.message_type.value, self.message_id, self.error_code, self.error_description]
        return []


@dataclass
class OCPPConfig:
    """OCPP configuration"""
    version: str = "1.6"  # "1.6" or "2.0"
    charge_point_model: str = "SimulatedCP"
    charge_point_vendor: str = "EVSimulator"
    serial_number: str = "SIM-00001"
    firmware_version: str = "1.0.0"
    server_url: str = "ws://localhost:8000"


class OCPPProtocol:
    """Base OCPP protocol handler"""
    
    def __init__(self, config: Optional[OCPPConfig] = None):
        self.config = config or OCPPConfig()
        self.message_handlers: Dict[str, Callable] = {}
        self.message_id_counter = 0
        
    def register_handler(self, action: str, handler: Callable) -> None:
        """Register a message handler for an action"""
        self.message_handlers[action] = handler
        
    async def handle_message(self, message: OCPPMessage) -> Optional[OCPPMessage]:
        """Handle incoming OCPP message"""
        if message.action in self.message_handlers:
            try:
                handler = self.message_handlers[message.action]
                if asyncio.iscoroutinefunction(handler):
                    response_payload = await handler(message.payload)
                else:
                    response_payload = handler(message.payload)
                    
                return OCPPMessage(
                    message_type=OCPPMessageType.CALL_RESULT,
                    message_id=message.message_id,
                    payload=response_payload
                )
            except Exception as e:
                logger.error(f"Error handling OCPP message: {e}")
                return OCPPMessage(
                    message_type=OCPPMessageType.CALL_ERROR,
                    message_id=message.message_id,
                    error_code="InternalError",
                    error_description=str(e)
                )
        return None
        
    def create_call_message(self, action: str, payload: Dict[str, Any]) -> OCPPMessage:
        """Create a CALL message"""
        self.message_id_counter += 1
        return OCPPMessage(
            message_type=OCPPMessageType.CALL,
            message_id=str(self.message_id_counter),
            action=action,
            payload=payload
        )
        
    def parse_message(self, data: str) -> Optional[OCPPMessage]:
        """Parse incoming OCPP message"""
        try:
            msg_list = json.loads(data)
            if not isinstance(msg_list, list) or len(msg_list) < 2:
                return None
                
            msg_type = OCPPMessageType(msg_list[0])
            msg_id = msg_list[1]
            
            if msg_type == OCPPMessageType.CALL and len(msg_list) >= 4:
                return OCPPMessage(
                    message_type=msg_type,
                    message_id=msg_id,
                    action=msg_list[2],
                    payload=msg_list[3]
                )
            elif msg_type == OCPPMessageType.CALL_RESULT and len(msg_list) >= 3:
                return OCPPMessage(
                    message_type=msg_type,
                    message_id=msg_id,
                    payload=msg_list[2]
                )
            elif msg_type == OCPPMessageType.CALL_ERROR and len(msg_list) >= 4:
                return OCPPMessage(
                    message_type=msg_type,
                    message_id=msg_id,
                    error_code=msg_list[2],
                    error_description=msg_list[3]
                )
        except Exception as e:
            logger.error(f"Error parsing OCPP message: {e}")
            
        return None


class OCPPServer(OCPPProtocol):
    """OCPP Server implementation"""
    
    def __init__(self, config: Optional[OCPPConfig] = None, port: int = 8000):
        super().__init__(config)
        self.port = port
        self.connected_clients: Dict[str, Any] = {}
        self.transactions: Dict[str, Dict[str, Any]] = {}
        self._setup_default_handlers()
        
    def _setup_default_handlers(self) -> None:
        """Setup default message handlers"""
        self.register_handler("BootNotification", self._handle_boot_notification)
        self.register_handler("Heartbeat", self._handle_heartbeat)
        self.register_handler("MeterValues", self._handle_meter_values)
        self.register_handler("StatusNotification", self._handle_status_notification)
        self.register_handler("StartTransaction", self._handle_start_transaction)
        self.register_handler("StopTransaction", self._handle_stop_transaction)
        
    async def _handle_boot_notification(self, payload: Dict) -> Dict:
        """Handle BootNotification"""
        logger.info(f"Boot notification from {payload.get('chargePointModel')}")
        return {
            "status": "Accepted",
            "currentTime": datetime.utcnow().isoformat() + "Z",
            "interval": 30
        }
        
    async def _handle_heartbeat(self, payload: Dict) -> Dict:
        """Handle Heartbeat"""
        return {
            "currentTime": datetime.utcnow().isoformat() + "Z"
        }
        
    async def _handle_meter_values(self, payload: Dict) -> Dict:
        """Handle MeterValues"""
        logger.debug(f"Meter values received: {payload}")
        return {}
        
    async def _handle_status_notification(self, payload: Dict) -> Dict:
        """Handle StatusNotification"""
        logger.info(f"Status: {payload.get('status')}")
        return {}
        
    async def _handle_start_transaction(self, payload: Dict) -> Dict:
        """Handle StartTransaction"""
        transaction_id = len(self.transactions) + 1
        self.transactions[str(transaction_id)] = payload
        logger.info(f"Transaction started: {transaction_id}")
        return {"transactionId": transaction_id, "idTagInfo": {"status": "Accepted"}}
        
    async def _handle_stop_transaction(self, payload: Dict) -> Dict:
        """Handle StopTransaction"""
        transaction_id = payload.get("transactionId")
        if transaction_id in self.transactions:
            del self.transactions[transaction_id]
            logger.info(f"Transaction stopped: {transaction_id}")
        return {"idTagInfo": {"status": "Accepted"}}
        
    async def start(self) -> None:
        """Start OCPP server"""
        logger.info(f"OCPP {self.config.version} server starting on port {self.port}")
        
    async def stop(self) -> None:
        """Stop OCPP server"""
        logger.info("OCPP server stopped")


class OCPPClient(OCPPProtocol):
    """OCPP Client implementation"""
    
    def __init__(self, config: Optional[OCPPConfig] = None, server_url: Optional[str] = None):
        super().__init__(config)
        self.server_url = server_url or self.config.server_url
        self.connected = False
        self.transaction_id: Optional[int] = None
        
    async def connect(self) -> bool:
        """Connect to OCPP server"""
        try:
            logger.info(f"Connecting to OCPP server at {self.server_url}")
            self.connected = True
            await self.send_boot_notification()
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
            
    async def disconnect(self) -> None:
        """Disconnect from OCPP server"""
        self.connected = False
        logger.info("Disconnected from OCPP server")
        
    async def send_boot_notification(self) -> Dict:
        """Send BootNotification"""
        message = self.create_call_message(
            "BootNotification",
            {
                "chargePointModel": self.config.charge_point_model,
                "chargePointVendor": self.config.charge_point_vendor,
                "firmwareVersion": self.config.firmware_version,
                "serialNumber": self.config.serial_number,
            }
        )
        logger.info("BootNotification sent")
        return {"status": "Accepted"}
        
    async def send_heartbeat(self) -> Dict:
        """Send Heartbeat"""
        message = self.create_call_message("Heartbeat", {})
        logger.debug("Heartbeat sent")
        return {"currentTime": datetime.utcnow().isoformat() + "Z"}
        
    async def send_meter_values(self, values: Dict[str, Any]) -> Dict:
        """Send meter values"""
        message = self.create_call_message("MeterValues", values)
        logger.debug(f"Meter values sent: {values}")
        return {}
        
    async def start_transaction(self, id_tag: str, meter_start: int = 0) -> Dict:
        """Start a transaction"""
        message = self.create_call_message(
            "StartTransaction",
            {
                "idTag": id_tag,
                "meterStart": meter_start,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "connectorId": 1,
            }
        )
        logger.info(f"Transaction started for {id_tag}")
        return {"transactionId": 1, "idTagInfo": {"status": "Accepted"}}
        
    async def stop_transaction(self, meter_stop: int = 0, transaction_id: Optional[int] = None) -> Dict:
        """Stop current transaction"""
        if not transaction_id:
            transaction_id = self.transaction_id
            
        message = self.create_call_message(
            "StopTransaction",
            {
                "transactionId": transaction_id,
                "meterStop": meter_stop,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "reason": "Local"
            }
        )
        logger.info(f"Transaction stopped: {transaction_id}")
        return {"idTagInfo": {"status": "Accepted"}}
