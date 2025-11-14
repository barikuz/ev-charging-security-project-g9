"""
Unit tests for V2G communication
"""

import pytest
import asyncio
from src.v2g.communicator import V2GCommunicator, V2GConfig, V2GMessage, V2GAuthType


@pytest.fixture
def v2g_config():
    """Create V2G configuration"""
    return V2GConfig(
        protocol_version="2020",
        max_power_ac=16000,
        max_power_dc=350000
    )


@pytest.fixture
def v2g_communicator(v2g_config):
    """Create V2G communicator"""
    return V2GCommunicator(v2g_config)


@pytest.mark.asyncio
async def test_v2g_discovery(v2g_communicator):
    """Test V2G discovery"""
    message = {"type": V2GMessage.DISCOVERY_REQ.value}
    response = await v2g_communicator.handle_message(message)
    
    assert response["type"] == V2GMessage.DISCOVERY_RES.value
    assert "chargePointAddress" in response


@pytest.mark.asyncio
async def test_v2g_service_discovery(v2g_communicator):
    """Test V2G service discovery"""
    message = {"type": V2GMessage.SERVICE_DISCOVERY_REQ.value}
    response = await v2g_communicator.handle_message(message)
    
    assert response["type"] == V2GMessage.SERVICE_DISCOVERY_RES.value
    assert "services" in response
    assert len(response["services"]) > 0


@pytest.mark.asyncio
async def test_v2g_session_start(v2g_communicator):
    """Test V2G session start"""
    message = {"type": V2GMessage.SESSION_START_REQ.value}
    response = await v2g_communicator.handle_message(message)
    
    assert response["type"] == V2GMessage.SESSION_START_RES.value
    assert "sessionID" in response
    assert v2g_communicator.session_active is True


@pytest.mark.asyncio
async def test_v2g_charging_status(v2g_communicator):
    """Test V2G charging status"""
    # Start session first
    await v2g_communicator.handle_message({"type": V2GMessage.SESSION_START_REQ.value})
    
    # Then get charging status
    message = {"type": V2GMessage.CHARGING_STATUS_REQ.value, "requestedPower": 10000}
    response = await v2g_communicator.handle_message(message)
    
    assert response["type"] == V2GMessage.CHARGING_STATUS_RES.value
    assert response["responseCode"] == "OK"


@pytest.mark.asyncio
async def test_v2g_session_stop(v2g_communicator):
    """Test V2G session stop"""
    # Start session
    await v2g_communicator.handle_message({"type": V2GMessage.SESSION_START_REQ.value})
    assert v2g_communicator.session_active is True
    
    # Stop session
    message = {"type": V2GMessage.SESSION_STOP_REQ.value}
    response = await v2g_communicator.handle_message(message)
    
    assert response["type"] == V2GMessage.SESSION_STOP_RES.value
    assert v2g_communicator.session_active is False


@pytest.mark.asyncio
async def test_v2g_authentication(v2g_communicator):
    """Test V2G authentication"""
    result = await v2g_communicator.authenticate(V2GAuthType.EIM, {"certificate": "test"})
    assert result is True
    assert v2g_communicator.authenticated is True


def test_v2g_session_info(v2g_communicator):
    """Test V2G session info"""
    info = v2g_communicator.get_session_info()
    assert "sessionActive" in info
    assert "authenticated" in info
    assert "protocolVersion" in info
