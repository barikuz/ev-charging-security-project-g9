import asyncio
import json
import logging
import random
from datetime import datetime, timezone
from contextlib import suppress
import websockets

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    force=True
)

# ---- Merkez Sistem (CSMS) ----
class CentralSystem:
    def __init__(self):
        self.baseline = None

    async def handle_connection(self, websocket):
        async for message in websocket:
            try:
                data = json.loads(message)
                energy = float(data["energy_wh"])
                station = data["station"]

                if self.baseline is None:
                    self.baseline = energy
                    logging.info(f"[CSMS] Baseline set to {self.baseline:.2f} Wh")
                    continue

                deviation = ((energy - self.baseline) / self.baseline) * 100
                logging.info(
                    f"[CSMS] {station}: energy={energy:.2f} Wh | deviation={deviation:.2f}%"
                )

                if abs(deviation) > 8:
                    logging.warning(
                        f"[ALERT] BillingAnomalyDetected for {station} (deviation={deviation:.2f}%)"
                    )

            except Exception as e:
                logging.exception("Error processing message: %s", e)

    async def start(self):
        async with websockets.serve(self.handle_connection, "localhost", 9000):
            logging.info("CSMS is listening on ws://localhost:9000/")
            await asyncio.Future()  # Sonsuza kadar dinle


# ---- Şarj İstasyonu (Charge Station) ----
class ChargeStation:
    def __init__(self, name):
        self.name = name
        self.energy_wh = 100000.0
        self.scale_factor = 1.0

    async def send_meter_values(self):
        async with websockets.connect("ws://localhost:9000") as ws:
            while True:
                delta = random.uniform(50, 150)
                self.energy_wh += delta * self.scale_factor

                payload = {
                    "station": self.name,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "energy_wh": self.energy_wh
                }

                await ws.send(json.dumps(payload))
                logging.info(
                    f"[{self.name}] Sent energy={self.energy_wh:.2f} "
                    f"(scale={self.scale_factor})"
                )

                await asyncio.sleep(5)

    async def tamper_scale(self, delay=40):
        await asyncio.sleep(delay)
        self.scale_factor = 0.85
        logging.warning(
            f"[{self.name}] ⚠️ Scale factor tampered to {self.scale_factor} after {delay}s"
        )


# ---- Ana kontrol akışı ----
async def main():
    csms = CentralSystem()
    station = ChargeStation("Station1")

    csms_task = asyncio.create_task(csms.start())
    await asyncio.sleep(0.2)

    station_task = asyncio.create_task(station.send_meter_values())
    tamper_task = asyncio.create_task(station.tamper_scale(40))

    await asyncio.sleep(90)
    station_task.cancel()
    tamper_task.cancel()
    csms_task.cancel()

    with suppress(asyncio.CancelledError):
        await station_task
        await tamper_task
        await csms_task

    logging.info("Simulation finished.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Shutting down gracefully.")
