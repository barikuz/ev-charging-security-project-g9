"""
Unit tests for anomaly injection
"""

import pytest
from src.anomalies.injector import (
    AnomalyInjector, AnomalyType, AnomalyConfig, AttackSeverity, 
    AttackScenario, AttackScenarios
)


@pytest.fixture
def anomaly_config():
    """Create anomaly configuration"""
    return AnomalyConfig(enabled=True, injection_rate=0.5)


@pytest.fixture
def anomaly_injector(anomaly_config):
    """Create anomaly injector"""
    return AnomalyInjector(anomaly_config)


def test_anomaly_injection(anomaly_injector):
    """Test anomaly injection"""
    result = anomaly_injector.inject("CAN_INJECTION", severity=AttackSeverity.HIGH)
    assert result is True
    assert len(anomaly_injector.get_active_anomalies()) > 0


def test_anomaly_removal(anomaly_injector):
    """Test anomaly removal"""
    anomaly_injector.inject("CAN_INJECTION")
    active = anomaly_injector.get_active_anomalies()
    assert len(active) > 0
    
    anomaly_id = f"CAN_INJECTION_0"
    result = anomaly_injector.remove_anomaly(anomaly_id)
    assert result is True


def test_modify_can_message(anomaly_injector):
    """Test CAN message modification"""
    original = b'\x00\x00\x00\x00\x00\x00\x00\x00'
    modified = anomaly_injector.modify_can_message(original, severity=1.0)
    
    assert isinstance(modified, bytes)
    assert len(modified) == len(original)


def test_dos_messages(anomaly_injector):
    """Test DoS message creation"""
    messages = anomaly_injector.create_dos_messages(count=10)
    assert len(messages) == 10
    assert all("id" in msg for msg in messages)
    assert all("data" in msg for msg in messages)


def test_spoofed_message(anomaly_injector):
    """Test spoofed message creation"""
    msg = anomaly_injector.create_spoofed_message(0x123, b'\xFF' * 8)
    assert msg["id"] == 0x123
    assert msg["spoofed"] is True


def test_attack_scenario():
    """Test attack scenario"""
    scenario = AttackScenarios.can_injection_attack()
    assert scenario.name == "CAN Injection Attack"
    assert len(scenario.anomalies) > 0


def test_statistics(anomaly_injector):
    """Test anomaly statistics"""
    anomaly_injector.inject("CAN_INJECTION")
    anomaly_injector.inject("DOS_ATTACK")
    
    stats = anomaly_injector.get_statistics()
    assert stats["total_injected"] == 2
    assert "CAN_INJECTION" in stats["anomaly_counts"]
