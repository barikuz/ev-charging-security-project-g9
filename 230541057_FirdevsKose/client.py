import asyncio, websockets, json, uuid, argparse, csv, os, time
from datetime import datetime, timezone

def now_ts(): return datetime.now(timezone.utc).isoformat()
def mid(): return str(uuid.uuid4())[:8]

# ---- OCPP 1.6 payloads ----
def boot_payload():
    return {
        "chargePointVendor": "DemoVendor",
        "chargePointModel": "DemoModel",
        "chargePointSerialNumber": "CP-01",
        "firmwareVersion": "1.0.0",
        "iccid": "8988307000000000000",
        "imsi": "001010123456789",
        "meterType": "DemoMeter",
        "meterSerialNumber": "M-001"
    }

def start_payload():
    return {"connectorId":1, "idTag":"TAG1", "meterStart":0, "timestamp": now_ts()}

def mv_payload(tx, val):
    return {
        "connectorId":1,
        "transactionId": tx,
        "meterValue":[
            {"timestamp": now_ts(),
             "sampledValue":[{"value": str(val), "measurand":"Energy.Active.Import.Register"}]}
        ]
    }

def stop_payload(tx, m=10):
    return {"transactionId": tx, "meterStop": m, "timestamp": now_ts(), "idTag":"TAG1"}

async def send(ws, arr):
    await ws.send(json.dumps(arr))
    try:
        return await asyncio.wait_for(ws.recv(), timeout=1.5)
    except Exception:
        return None

async def run(url, scenario, count, out):
    new = not os.path.exists(out)
    with open(out, "a", newline="") as f:
        w = csv.writer(f)
        if new: w.writerow(["session_id","event","message_id","ts_epoch","ts_iso"])
        # IMPORTANT: OCPP 1.6 subprotocol
        async with websockets.connect(url, subprotocols=["ocpp1.6"], ping_interval=20) as ws:
            # 0) BootNotification
            bmsg = [2, mid(), "BootNotification", boot_payload()]
            await send(ws, bmsg)
            w.writerow(["BOOT","BootNotification", bmsg[1], time.time(), now_ts()])
            await asyncio.sleep(0.2)

            # N adet oturum
            for i in range(count):
                tx = mid()
                # 1) Start
                s1 = [2, mid(), "StartTransaction", start_payload()]
                await send(ws,s1); w.writerow([tx,"Start",s1[1],time.time(),now_ts()]); await asyncio.sleep(0.1)

                if scenario=="out_of_order":
                    # 2) Stop'u bilerek erken gönder
                    st = [2, mid(), "StopTransaction", stop_payload(tx, m=3+i)]
                    await send(ws,st); w.writerow([tx,"Stop(early)",st[1],time.time(),now_ts()]); await asyncio.sleep(0.2)
                    # 3) MeterValues'u geç gönder
                    mv = [2, mid(), "MeterValues", mv_payload(tx, val=2.0+i)]
                    await send(ws,mv); w.writerow([tx,"MeterValues(late)",mv[1],time.time(),now_ts()])
                elif scenario=="duplicate_start":
                    s2 = [2, mid(), "StartTransaction", start_payload()]
                    await send(ws,s2); w.writerow([tx,"Start(DUP)",s2[1],time.time(),now_ts()]); await asyncio.sleep(0.2)
                    st = [2, mid(), "StopTransaction", stop_payload(tx)]
                    await send(ws,st); w.writerow([tx,"Stop",st[1],time.time(),now_ts()])
                elif scenario=="missing_meter":
                    st = [2, mid(), "StopTransaction", stop_payload(tx, m=0)]
                    await send(ws,st); w.writerow([tx,"Stop(no MV)",st[1],time.time(),now_ts()])
                else:
                    mv = [2, mid(), "MeterValues", mv_payload(tx, val=5.0+i)]
                    await send(ws,mv); w.writerow([tx,"MeterValues",mv[1],time.time(),now_ts()]); await asyncio.sleep(0.2)
                    st = [2, mid(), "StopTransaction", stop_payload(tx)]
                    await send(ws,st); w.writerow([tx,"Stop",st[1],time.time(),now_ts()])
                await asyncio.sleep(0.8)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--url", required=True)
    p.add_argument("--scenario", default="out_of_order", choices=["normal","out_of_order","duplicate_start","missing_meter"])
    p.add_argument("--count", type=int, default=5)
    p.add_argument("--out", default="results.csv")
    a=p.parse_args()
    asyncio.run(run(a.url,a.scenario,a.count,a.out))
