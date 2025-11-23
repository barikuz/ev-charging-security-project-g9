# filepath: /soğutma-anomalisi-sim/soğutma-anomalisi-sim/tests/test_flow.py

import asyncio
import pytest
from src.detector import Detector
from src.anomaly_injector import AnomalyInjector
from src.charger_module import ChargerModule

# Bu dosya, normal ve anormal senaryolar için testler içerir.

@pytest.fixture
def setup_detector():
    detector = Detector()
    return detector

@pytest.fixture
def setup_charger_module():
    charger = ChargerModule()
    return charger

@pytest.mark.asyncio
async def test_normal_flow(setup_detector, setup_charger_module):
    # Normal akışta, fan durumu OFF değil ve sıcaklık artışı yok.
    setup_charger_module.send_meter_values(temperature=20)  # Normal sıcaklık
    await asyncio.sleep(1)  # Zaman tanı
    assert not setup_detector.check_alerts()  # Hiçbir alarm olmamalı

@pytest.mark.asyncio
async def test_anomaly_flow(setup_detector, setup_charger_module):
    # Anomali akışında, fan OFF ve sıcaklık artışı var.
    anomaly_injector = AnomalyInjector(inject=True)
    anomaly_injector.inject_anomaly()  # Anomali enjekte et
    setup_charger_module.send_meter_values(temperature=25)  # Sıcaklık artışı
    await asyncio.sleep(1)  # Zaman tanı
    assert setup_detector.check_alerts()  # Alarm olmalı

# Testlerin çalıştırılması için pytest kullanılır.