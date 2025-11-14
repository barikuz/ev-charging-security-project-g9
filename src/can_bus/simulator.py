"""
CAN Bus Simulator Module
Handles CAN message generation, processing, and communication
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class CANMessage:
    """Represents a CAN message"""
    arbitration_id: int
    data: bytes
    dlc: int = 8
    is_extended_id: bool = False
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    error_frame: bool = False
    remote_frame: bool = False
    fd_frame: bool = False
    
    def __post_init__(self):
        if len(self.data) > self.dlc:
            self.data = self.data[:self.dlc]
        if len(self.data) < self.dlc:
            self.data = self.data + bytes(self.dlc - len(self.data))


@dataclass
class CANConfig:
    """CAN Bus configuration"""
    channel: str = "vcan0"
    bustype: str = "virtual"
    bitrate: int = 500000  # 500 kbps standard
    sample_point: float = 0.75
    sjw: int = 1
    

class CANBusSimulator:
    """Simulates CAN bus communication"""
    
    def __init__(self, config: Optional[CANConfig] = None):
        self.config = config or CANConfig()
        self.message_buffer: List[CANMessage] = []
        self.listeners: List[callable] = []
        self.running = False
        self.message_count = 0
        
    def add_listener(self, callback: callable) -> None:
        """Add a callback listener for received messages"""
        self.listeners.append(callback)
        
    def remove_listener(self, callback: callable) -> None:
        """Remove a callback listener"""
        if callback in self.listeners:
            self.listeners.remove(callback)
            
    async def send_message(self, message: CANMessage) -> bool:
        """Send a CAN message"""
        try:
            self.message_buffer.append(message)
            self.message_count += 1
            logger.debug(f"CAN message sent: ID=0x{message.arbitration_id:03X}, Data={message.data.hex()}")
            await self._notify_listeners(message)
            return True
        except Exception as e:
            logger.error(f"Error sending CAN message: {e}")
            return False
            
    async def receive_messages(self, timeout: float = 1.0) -> List[CANMessage]:
        """Receive CAN messages with timeout"""
        start_time = datetime.now().timestamp()
        messages = []
        
        while datetime.now().timestamp() - start_time < timeout:
            if self.message_buffer:
                messages.append(self.message_buffer.pop(0))
            await asyncio.sleep(0.01)
            
        return messages
        
    async def _notify_listeners(self, message: CANMessage) -> None:
        """Notify all registered listeners of new message"""
        for listener in self.listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(message)
                else:
                    listener(message)
            except Exception as e:
                logger.error(f"Error in listener callback: {e}")
                
    def start(self) -> None:
        """Start the CAN bus simulator"""
        self.running = True
        logger.info(f"CAN bus simulator started on {self.config.channel}")
        
    def stop(self) -> None:
        """Stop the CAN bus simulator"""
        self.running = False
        logger.info("CAN bus simulator stopped")
        
    def get_statistics(self) -> Dict[str, Any]:
        """Get CAN bus statistics"""
        return {
            "total_messages": self.message_count,
            "buffer_size": len(self.message_buffer),
            "is_running": self.running,
            "config": {
                "channel": self.config.channel,
                "bustype": self.config.bustype,
                "bitrate": self.config.bitrate,
            }
        }


# Common CAN message types for EV charging
class EVCANMessages:
    """Common CAN message definitions for EV charging"""
    
    @staticmethod
    def battery_status(soc: int, temperature: int, voltage: int) -> CANMessage:
        """Generate battery status CAN message"""
        data = bytes([
            soc & 0xFF,  # State of Charge (0-100%)
            temperature & 0xFF,  # Battery temperature
            (voltage >> 8) & 0xFF,  # Voltage MSB
            voltage & 0xFF,  # Voltage LSB
            0x00, 0x00, 0x00, 0x00
        ])
        return CANMessage(arbitration_id=0x100, data=data)
    
    @staticmethod
    def charging_state(state: int, current: int, power: int) -> CANMessage:
        """Generate charging state CAN message"""
        data = bytes([
            state & 0xFF,  # 0=Idle, 1=Charging, 2=Error
            current & 0xFF,  # Charging current in Amps
            (power >> 8) & 0xFF,  # Power MSB
            power & 0xFF,  # Power LSB
            0x00, 0x00, 0x00, 0x00
        ])
        return CANMessage(arbitration_id=0x101, data=data)
    
    @staticmethod
    def error_status(error_code: int, severity: int) -> CANMessage:
        """Generate error status CAN message"""
        data = bytes([
            error_code & 0xFF,  # Error code
            severity & 0xFF,  # 0=Info, 1=Warning, 2=Error, 3=Critical
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00
        ])
        return CANMessage(arbitration_id=0x102, data=data)
