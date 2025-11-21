"""
Unit tests for OCPP protocol
"""

import pytest
import asyncio
from src.ocpp.protocol import (
    OCPPServer, OCPPClient, OCPPMessage, OCPPConfig, 
    OCPPMessageType, ChargePointStatus
)


@pytest.fixture
def ocpp_config():
    """Create OCPP configuration"""
    return OCPPConfig(
        version="1.6",
        charge_point_model="TestCP",
        serial_number="TEST-001"
    )


@pytest.fixture
def ocpp_server(ocpp_config):
    """Create OCPP server"""
    return OCPPServer(ocpp_config)


@pytest.fixture
def ocpp_client(ocpp_config):
    """Create OCPP client"""
    return OCPPClient(ocpp_config)


def test_ocpp_message_creation():
    """Test OCPP message creation"""
    msg = OCPPMessage(
        message_type=OCPPMessageType.CALL,
        message_id="1",
        action="BootNotification",
        payload={"model": "TestCP"}
    )
    assert msg.message_id == "1"
    assert msg.action == "BootNotification"


def test_ocpp_message_to_list():
    """Test OCPP message conversion to list"""
    msg = OCPPMessage(
        message_type=OCPPMessageType.CALL,
        message_id="1",
        action="Heartbeat",
        payload={}
    )
    msg_list = msg.to_list()
    assert msg_list[0] == OCPPMessageType.CALL.value
    assert msg_list[1] == "1"
    assert msg_list[2] == "Heartbeat"


@pytest.mark.asyncio
async def test_ocpp_server_boot_notification(ocpp_server):
    """Test server handling boot notification"""
    msg = OCPPMessage(
        message_type=OCPPMessageType.CALL,
        message_id="1",
        action="BootNotification",
        payload={"chargePointModel": "TestCP"}
    )
    response = await ocpp_server.handle_message(msg)
    assert response.message_type == OCPPMessageType.CALL_RESULT
    assert response.payload["status"] == "Accepted"


@pytest.mark.asyncio
async def test_ocpp_client_connect(ocpp_client):
    """Test client connection"""
    result = await ocpp_client.connect()
    assert result is True
    assert ocpp_client.connected is True


@pytest.mark.asyncio
async def test_ocpp_client_send_heartbeat(ocpp_client):
    """Test sending heartbeat"""
    await ocpp_client.connect()
    result = await ocpp_client.send_heartbeat()
    assert "currentTime" in result


@pytest.mark.asyncio
async def test_ocpp_server_transaction(ocpp_server):
    """Test transaction handling"""
    start_msg = OCPPMessage(
        message_type=OCPPMessageType.CALL,
        message_id="1",
        action="StartTransaction",
        payload={"idTag": "TEST123", "meterStart": 0}
    )
    response = await ocpp_server.handle_message(start_msg)
    assert "transactionId" in response.payload


def test_charge_point_status():
    """Test charge point status enum"""
    assert ChargePointStatus.AVAILABLE.value == "Available"
    assert ChargePointStatus.CHARGING.value == "Charging"
