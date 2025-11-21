"""
Unit tests for CAN bus simulator
"""

import pytest
import asyncio
from src.can_bus.simulator import CANBusSimulator, CANMessage, CANConfig, EVCANMessages


@pytest.fixture
def can_simulator():
    """Create a CAN bus simulator instance"""
    config = CANConfig(channel="test_channel")
    return CANBusSimulator(config)


@pytest.mark.asyncio
async def test_can_message_creation(can_simulator):
    """Test CAN message creation"""
    msg = CANMessage(
        arbitration_id=0x123,
        data=b'\x01\x02\x03\x04\x05\x06\x07\x08'
    )
    assert msg.arbitration_id == 0x123
    assert msg.data == b'\x01\x02\x03\x04\x05\x06\x07\x08'


@pytest.mark.asyncio
async def test_can_send_message(can_simulator):
    """Test sending a CAN message"""
    msg = CANMessage(arbitration_id=0x100, data=b'\x00' * 8)
    result = await can_simulator.send_message(msg)
    assert result is True
    assert can_simulator.message_count == 1


@pytest.mark.asyncio
async def test_can_message_listener(can_simulator):
    """Test CAN message listener callback"""
    received_messages = []
    
    def listener(msg):
        received_messages.append(msg)
    
    can_simulator.add_listener(listener)
    msg = CANMessage(arbitration_id=0x200, data=b'\xFF' * 8)
    await can_simulator.send_message(msg)
    
    await asyncio.sleep(0.1)
    assert len(received_messages) == 1
    assert received_messages[0].arbitration_id == 0x200


@pytest.mark.asyncio
async def test_battery_status_message():
    """Test battery status CAN message"""
    msg = EVCANMessages.battery_status(soc=75, temperature=35, voltage=400)
    assert msg.arbitration_id == 0x100
    assert msg.data[0] == 75  # SOC


@pytest.mark.asyncio
async def test_charging_state_message():
    """Test charging state CAN message"""
    msg = EVCANMessages.charging_state(state=1, current=32, power=10000)
    assert msg.arbitration_id == 0x101
    assert msg.data[0] == 1  # State


def test_can_statistics(can_simulator):
    """Test CAN bus statistics"""
    stats = can_simulator.get_statistics()
    assert "total_messages" in stats
    assert "is_running" in stats
    assert stats["total_messages"] == 0
