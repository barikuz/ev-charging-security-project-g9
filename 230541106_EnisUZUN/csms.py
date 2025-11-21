#!/usr/bin/env python3
"""
Central System Management System (CSMS)
OCPP 1.6 WebSocket server that orchestrates charging anomaly scenarios.
Periodically sends SetChargingProfile commands to simulate current fluctuations.
"""
import asyncio
import datetime
import websockets
from ocpp.v16 import ChargePoint as CP
from ocpp.v16 import call, call_result
from ocpp.routing import on
from ocpp.v16.enums import RegistrationStatus, Action

# Store connected charge points
CPs = {}

class CentralSystem(CP):
    @on(Action.BootNotification)
    async def on_boot_notification(self, charge_point_model, charge_point_vendor, **kwargs):
        """Handle BootNotification from charge point"""
        print(f"✅ BootNotification received from {self.id}")
        print(f"   Model: {charge_point_model}")
        print(f"   Vendor: {charge_point_vendor}")
        
        # Store the charge point connection
        CPs[self.id] = self
        
        return call_result.BootNotificationPayload(
            current_time=datetime.datetime.utcnow().isoformat(),
            interval=10,
            status=RegistrationStatus.accepted
        )

    @on(Action.MeterValues)
    async def on_meter_values(self, connector_id, meter_value, **kwargs):
        """Handle MeterValues from charge point"""
        try:
            for mv in meter_value:
                for sample in mv.get("sampledValue", []):
                    value = sample.get("value", "0")
                    measurand = sample.get("measurand", "unknown")
                    unit = sample.get("unit", "")
                    print(f"📊 MeterValues from {self.id}: {value}{unit} ({measurand})")
        except Exception as e:
            print(f"⚠️  Error parsing MeterValues: {e}")
        
        return call_result.MeterValuesPayload()

async def send_anomaly():
    """
    Orchestrate the anomaly scenario:
    1. Wait for charge points to connect
    2. Cycle through: Set limit to 0A → Set limit to 100A → Start → Stop
    3. This creates repeated current fluctuations
    """
    print("⏳ Waiting 3 seconds for charge points to connect...")
    await asyncio.sleep(3)
    
    print()
    print("=" * 60)
    print("🎭 Starting Anomaly Scenario: Repeated Current Fluctuations")
    print("=" * 60)
    print()
    
    cycle = 0
    while True:
        if not CPs:
            print("⚠️  No charge points connected. Waiting...")
            await asyncio.sleep(2)
            continue
        
        cycle += 1
        print(f"🔄 Anomaly Cycle #{cycle}")
        print("-" * 60)
        
        for cp_id, cp in list(CPs.items()):
            try:
                # Step 1: Set charging profile to 0A (restrict current)
                print(f"📉 [{cp_id}] Setting current limit to 0A...")
                await cp.call(call.SetChargingProfilePayload(
                    connector_id=1,
                    cs_charging_profiles={
                        "chargingProfileId": 7,
                        "stackLevel": 0,
                        "chargingProfilePurpose": "TxProfile",
                        "chargingProfileKind": "Absolute",
                        "chargingSchedule": {
                            "chargingRateUnit": "A",
                            "chargingSchedulePeriod": [{"startPeriod": 0, "limit": 0}]
                        }
                    }
                ))
                
                await asyncio.sleep(2)
                
                # Step 2: Set charging profile to 100A (allow high current)
                print(f"📈 [{cp_id}] Setting current limit to 100A...")
                await cp.call(call.SetChargingProfilePayload(
                    connector_id=1,
                    cs_charging_profiles={
                        "chargingProfileId": 8,
                        "stackLevel": 0,
                        "chargingProfilePurpose": "TxProfile",
                        "chargingProfileKind": "Absolute",
                        "chargingSchedule": {
                            "chargingRateUnit": "A",
                            "chargingSchedulePeriod": [{"startPeriod": 0, "limit": 100}]
                        }
                    }
                ))
                
                await asyncio.sleep(1)
                
                # Step 3: Start transaction
                print(f"🚀 [{cp_id}] Sending RemoteStartTransaction...")
                await cp.call(call.RemoteStartTransactionPayload(
                    id_tag="ANOM_TEST",
                    connector_id=1
                ))
                
                await asyncio.sleep(2)
                
                # Step 4: Stop transaction
                print(f"🛑 [{cp_id}] Sending RemoteStopTransaction...")
                await cp.call(call.RemoteStopTransactionPayload(
                    transaction_id=1
                ))
                
                print()
                
            except Exception as e:
                print(f"❌ Error sending commands to {cp_id}: {e}")
        
        # Wait before next cycle
        await asyncio.sleep(3)

async def handler(ws, path):
    """Handle new WebSocket connections from charge points"""
    cp_id = path.strip("/") or "CP1"
    print(f"🔗 New connection from charge point: {cp_id}")
    
    cp = CentralSystem(cp_id, ws)
    
    try:
        await cp.start()
    except websockets.exceptions.ConnectionClosed:
        print(f"⚠️  Connection closed for {cp_id}")
    finally:
        if cp_id in CPs:
            del CPs[cp_id]
            print(f"🔌 Charge point {cp_id} disconnected")

async def main():
    print("=" * 60)
    print("🏢 Central System Management System (CSMS) Starting...")
    print("=" * 60)
    print()
    
    # Start WebSocket server
    server = await websockets.serve(
        handler, 
        "127.0.0.1", 
        9000, 
        subprotocols=["ocpp1.6"]
    )
    
    print("✅ CSMS WebSocket server running on ws://127.0.0.1:9000/")
    print("   Waiting for charge point connections...")
    print()
    
    # Start anomaly orchestration
    asyncio.create_task(send_anomaly())
    
    # Keep server running
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
