#!/usr/bin/env python3
import asyncio
from ocpp.v16 import ChargePoint as CP, call_result
from ocpp.routing import on
from ocpp.v16.enums import Action, RegistrationStatus
import datetime

class TestCP(CP):
    @on(Action.BootNotification)
    def on_boot_notification(self, charge_point_model, charge_point_vendor, **kwargs):
        print(f"✅ Handler called! Model: {charge_point_model}, Vendor: {charge_point_vendor}")
        return call_result.BootNotificationPayload(
            current_time=datetime.datetime.utcnow().isoformat(),
            interval=10,
            status=RegistrationStatus.accepted
        )

# Test
cp = TestCP("TEST", None)
print(f"Route map: {cp.route_map}")
print(f"BootNotification in route_map: {Action.BootNotification in cp.route_map}")
if Action.BootNotification in cp.route_map:
    print(f"Handlers: {cp.route_map[Action.BootNotification]}")
