import asyncio
import logging
import json
import hashlib
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
import random

# LOG KONFİGÜRASYONU


log_dir = Path("logs")   # ← Doğru klasör adı
log_dir.mkdir(exist_ok=True)

timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = log_dir / f"simulation_log_{timestamp_str}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("Simulator")


# GÜVENLİK MONİTÖRÜ

class SecurityMonitor:
    def __init__(self):
        self.events = []
        self.attacks = []
        self.blocked = 0
        self.total_attacks = 0

    def record(self, ts, energy, status):
        self.events.append({"timestamp": ts, "energy": energy, "status": status})

    def log_attack(self, attack_type, reason, blocked=True):
        self.total_attacks += 1
        if blocked:
            self.blocked += 1

        entry = {
            "type": attack_type,
            "reason": reason,
            "blocked": blocked,
            "time": datetime.now(timezone.utc).isoformat()
        }

        self.attacks.append(entry)
        logger.warning(f"[UYARI] {attack_type} | Engellendi = {blocked} | Sebep: {reason}")

    def save_report(self):
        report_path = log_dir / f"security_report_{timestamp_str}.json"

        data = {
            "events": self.events,
            "attacks": self.attacks,
            "total_attacks": self.total_attacks,
            "blocked": self.blocked
        }

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        logger.info(f"Güvenlik raporu kaydedildi: {report_path}")


#  ŞARJ İSTASYONU 

class ChargingStation:
    def __init__(self, station_id):
        self.id = station_id
        self.energy = 1000.0
        self.start_time = datetime.now(timezone.utc)

    def generate_packet(self, elapsed_seconds):
        # Gerçekçi enerji artışı: 9 ila 11 Wh
        increment = 10 + random.uniform(-1, 1)
        self.energy += increment

        ts = self.start_time + timedelta(seconds=elapsed_seconds)

        packet = {
            "stationId": self.id,
            "energyWh": round(self.energy, 2),
            "timestamp": ts.isoformat(),
            "nonce": hashlib.sha256(os.urandom(8)).hexdigest()[:8]
        }

        # Paket imzası
        packet["signature"] = hashlib.sha256(
            json.dumps(packet, sort_keys=True).encode()
        ).hexdigest()

        return packet


# SALDIRGAN

class Attacker:
    def __init__(self):
        self.stolen = None

    def capture(self, packet):
        logger.info("[SALDIRGAN] Geçerli paket yakalandı.")
        self.stolen = packet.copy()

    def replay(self):
        if not self.stolen:
            return None
        logger.info("[SALDIRGAN] TEKRAR GÖNDERİM paketi gönderiliyor...")
        return self.stolen.copy()

    def manipulate_timestamp(self):
        if not self.stolen:
            return None
        logger.info("[SALDIRGAN] ZAMAN DAMGASI MANİPÜLASYON paketi gönderiliyor...")
        pkt = self.stolen.copy()
        pkt["timestamp"] = datetime.now(timezone.utc).isoformat()
        return pkt


# CSMS GÜVENLİK DUVARI


class CSMS:
    def __init__(self, monitor):
        self.monitor = monitor
        self.last_energy = 0
        self.last_timestamp = datetime.min.replace(tzinfo=timezone.utc)
        self.seen_signatures = set()

    def process(self, packet):
        ts = datetime.fromisoformat(packet["timestamp"])
        energy = packet["energyWh"]
        sig = packet["signature"]

        # --- KURAL 1: Tekrar imza tespiti ---
        if sig in self.seen_signatures:
            self.monitor.log_attack("Tekrar Saldırısı", "İmza tekrar kullanıldı")
            self.monitor.record(packet["timestamp"], energy, "REDDEDİLDİ")
            return False

        # --- KURAL 2: zaman ileri gitmeli ---
        if ts <= self.last_timestamp:
            self.monitor.log_attack("Zaman Damgası Saldırısı", "Zaman artmıyor")
            self.monitor.record(packet["timestamp"], energy, "REDDEDİLDİ")
            return False

        # --- KURAL 3: enerji mantıklı olmalı (azalamaz) ---
        if energy < self.last_energy:
            self.monitor.log_attack("Manipülasyon Saldırısı", "Enerji yasadışı şekilde azaldı")
            self.monitor.record(packet["timestamp"], energy, "REDDEDİLDİ")
            return False

        # Kabul
        logger.info(f"[CSMS] KABUL EDİLDİ: {energy}Wh")
        self.seen_signatures.add(sig)
        self.last_energy = energy
        self.last_timestamp = ts
        self.monitor.record(packet["timestamp"], energy, "KABUL EDİLDİ")
        return True



# SIMÜLASYON DÖNGÜSÜ


async def run_simulation():
    logger.info("=== GÜVENLİK SIMÜLASYONU BAŞLIYOR ===")

    monitor = SecurityMonitor()
    csms = CSMS(monitor)
    station = ChargingStation("EV-TR-001")
    attacker = Attacker()

    for tick in range(1, 20):
        await asyncio.sleep(0.2)

        # Normal trafik
        if tick <= 5:
            pkt = station.generate_packet(tick * 10)
            csms.process(pkt)

            if tick == 5:
                attacker.capture(pkt)

        # Replay saldırısı
        elif tick == 8:
            pkt = attacker.replay()
            csms.process(pkt)

        # Zaman damgası manipülasyonu saldırısı
        elif tick == 12:
            pkt = attacker.manipulate_timestamp()
            csms.process(pkt)

        # Normal akış devam ediyor
        else:
            pkt = station.generate_packet(tick * 10)
            csms.process(pkt)

    monitor.save_report()
    logger.info("=== SIMÜLASYON TAMAMLANDI ===")





if __name__ == "__main__":
    try:
        asyncio.run(run_simulation())
    except KeyboardInterrupt:
        print("Durduruldu.")
