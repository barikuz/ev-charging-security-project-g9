#!/usr/bin/env python3
"""
Charge Point (OCPP Client)
Connects to CSMS and translates OCPP messages to CAN commands.
Maps RemoteStart/Stop and SetChargingProfile to CAN bus messages.
"""
import asyncio
import datetime
import websockets
import can
import time
import json
from ocpp.v16 import ChargePoint as CP
from ocpp.v16 import call, call_result
from ocpp.routing import on
from ocpp.v16.enums import (
    Action, 
    Measurand, 
    UnitOfMeasure, 
    AuthorizationStatus, 
    RegistrationStatus,
    RemoteStartStopStatus,
    ChargingProfileStatus
)

class ChargePoint(CP):
    def __init__(self, id, ws, bus):
        super().__init__(id, ws)
        self.bus = bus
        self.transaction_id = None

    async def send_boot(self):
        """Send BootNotification to CSMS"""
        print("📤 Sending BootNotification...")
        res = await self.call(call.BootNotificationPayload(
            charge_point_model="SimCharger", 
            charge_point_vendor="EVSimVendor"
        ))
        print(f"✅ BootNotification accepted. Status: {res.status}")
        return res

    @on(Action.RemoteStartTransaction)
    async def on_remote_start_transaction(self, id_tag, connector_id=None, **kwargs):
        """
        Handle RemoteStartTransaction from CSMS
        Send CAN 0x200 (Start) command to charger module
        """
        print(f"🚀 RemoteStartTransaction received (idTag={id_tag}, connector={connector_id})")
        
        # Send START command via CAN
        msg = can.Message(
            arbitration_id=0x200,
            data=[],
            is_extended_id=False
        )
        self.bus.send(msg)
        print("📤 CAN: Sent START command (0x200)")
        
        self.transaction_id = 1  # Simplified transaction ID
        
        return call_result.RemoteStartTransactionPayload(
            status=RemoteStartStopStatus.accepted
        )

    @on(Action.RemoteStopTransaction)
    async def on_remote_stop_transaction(self, transaction_id, **kwargs):
        """
        Handle RemoteStopTransaction from CSMS
        Send CAN 0x201 (Stop) command to charger module
        """
        print(f"🛑 RemoteStopTransaction received (transactionId={transaction_id})")
        
        # Send STOP command via CAN
        msg = can.Message(
            arbitration_id=0x201,
            data=[],
            is_extended_id=False
        )
        self.bus.send(msg)
        print("📤 CAN: Sent STOP command (0x201)")
        
        self.transaction_id = None
        
        return call_result.RemoteStopTransactionPayload(
            status=RemoteStartStopStatus.accepted
        )

    @on(Action.SetChargingProfile)
    async def on_set_charging_profile(self, connector_id, cs_charging_profiles, **kwargs):
        """
        Handle SetChargingProfile from CSMS
        Extract current limit and send via CAN 0x210
        """
        print(f"⚡ SetChargingProfile received (connector={connector_id})")
        
        try:
            # Extract limit from charging schedule
            schedule = cs_charging_profiles['chargingSchedule']
            periods = schedule['chargingSchedulePeriod']
            
            if periods:
                limit = int(periods[0]['limit'])
                print(f"   → Current limit: {limit}A")
                
                # Send SET LIMIT command via CAN
                msg = can.Message(
                    arbitration_id=0x210,
                    data=[limit & 0xFF, (limit >> 8) & 0xFF],
                    is_extended_id=False
                )
                self.bus.send(msg)
                print(f"📤 CAN: Sent SET_LIMIT command (0x210) with value {limit}A")
            
            return call_result.SetChargingProfilePayload(
                status=ChargingProfileStatus.accepted
            )
        except Exception as e:
            print(f"❌ Error processing SetChargingProfile: {e}")
            return call_result.SetChargingProfilePayload(
                status=ChargingProfileStatus.rejected
            )

    async def meter_loop(self):
        """
        Read CAN 0x300 (current readings) and send MeterValues to CSMS
        """
        print("📊 Starting MeterValues reporting loop...")
        DATA_FILE = "/tmp/ev_current.json"
        
        while True:
            try:
                msg = self.bus.recv(timeout=0.5)
                if msg and msg.arbitration_id == 0x300:
                    # Parse current value from CAN message
                    current = msg.data[0] + (msg.data[1] << 8) if len(msg.data) >= 2 else 0
                    
                    print(f"RECEIVED: {current}")
                    
                    # Write to shared file for plotter
                    with open(DATA_FILE, 'w') as f:
                        json.dump({"timestamp": time.time(), "current": current}, f)
                    
                    # Send MeterValues to CSMS
                    await self.call(call.MeterValuesPayload(
                        connector_id=1,
                        meter_value=[{
                            "timestamp": datetime.datetime.utcnow().isoformat(),
                            "sampledValue": [{
                                "measurand": Measurand.current_import,
                                "unit": UnitOfMeasure.amp,
                                "value": str(current)
                            }]
                        }]
                    ))
                    print(f"� MeterValues sent to CSMS: {current}A")
            except Exception as e:
                print(f"⚠️  Error in meter loop: {e}")
            
            await asyncio.sleep(0.1)

async def main():
    print("=" * 60)
    print("🔌 Charge Point Starting...")
    print("=" * 60)
    
    # Connect to virtual CAN bus - STANDARDIZED
    print("🔗 Connecting to CAN bus (bustype=virtual, channel=vcan0, bitrate=500000)...")
    bus = can.interface.Bus(bustype="virtual", channel="vcan0", bitrate=500000)
    print("✅ CAN bus connected")
    
    # Connect to CSMS WebSocket
    print("🔗 Connecting to CSMS at ws://127.0.0.1:9000/CP1...")
    ws = await websockets.connect(
        "ws://127.0.0.1:9000/CP1", 
        subprotocols=["ocpp1.6"]
    )
    print("✅ WebSocket connected")
    
    # Create ChargePoint instance
    cp = ChargePoint("CP1", ws, bus)
    
    # Send boot notification
    await cp.send_boot()
    
    # Start meter reading loop
    asyncio.create_task(cp.meter_loop())
    
    # Start OCPP message handling
    print("🎯 Charge Point ready. Waiting for OCPP commands...")
    print()
    await cp.start()

if __name__ == "__main__":
    asyncio.run(main())
