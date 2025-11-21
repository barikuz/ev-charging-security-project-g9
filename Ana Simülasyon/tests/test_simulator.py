"""
Tests for the main simulator
"""

import pytest
import asyncio
from src.simulator.main import EVChargingSimulator, SimulatorConfig
from src.can_bus.simulator import CANConfig
from src.ocpp.protocol import OCPPConfig
from src.v2g.communicator import V2GConfig
from src.anomalies.injector import AnomalyConfig


@pytest.fixture
def simulator_config():
    """Create simulator configuration"""
    return SimulatorConfig(
        name="Test Simulator",
        can_enabled=True,
        ocpp_enabled=True,
        v2g_enabled=True,
        anomaly_enabled=True,
    )


@pytest.fixture
def simulator(simulator_config):
    """Create simulator instance"""
    return EVChargingSimulator(simulator_config)


@pytest.mark.asyncio
async def test_simulator_initialization(simulator):
    """Test simulator initialization"""
    assert simulator.can_bus is not None
    assert simulator.ocpp_server is not None
    assert simulator.ocpp_client is not None
    assert simulator.v2g is not None
    assert simulator.anomaly_injector is not None


@pytest.mark.asyncio
async def test_simulator_start_stop(simulator):
    """Test simulator start and stop"""
    await simulator.start()
    assert simulator.running is True
    
    await simulator.stop()
    assert simulator.running is False


@pytest.mark.asyncio
async def test_anomaly_injection(simulator):
    """Test anomaly injection in simulator"""
    result = simulator.inject_anomaly("CAN_INJECTION", severity="HIGH")
    assert result is True


def test_simulator_statistics(simulator):
    """Test simulator statistics"""
    stats = simulator.get_statistics()
    assert "elapsed_time" in stats
    assert "is_running" in stats
    assert "messages" in stats


@pytest.mark.asyncio
async def test_short_charging_session(simulator):
    """Test a short charging session"""
    result = await simulator.simulate_charging_session(duration=5.0)
    assert result["status"] == "completed"
    assert result["statistics"]["can_messages_sent"] >= 0
