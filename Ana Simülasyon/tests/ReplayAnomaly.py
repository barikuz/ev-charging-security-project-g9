from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Tuple
import time


# 230541082 Bahadır Atalay
# CAN bus replay saldırılarını tespit ve engelleme filtresi


@dataclass
class CANMessage:
    can_id: int
    payload: bytes        # payload as bytes
    seq: int              # monotonic sequence number (unique token)
    timestamp: datetime   # arrival time

class CANReplayFilter:
    def __init__(self, replay_window_seconds: float = 5.0):
        # son görülen sequence numaraları can_id -> last_seq
        self.last_seq: dict[int, int] = {}
        # (can_id, payload) -> last_seen_timestamp
        self.last_seen: dict[Tuple[int, bytes], datetime] = {}
        # kısa süre içinde aynı can_id+payload tekrarını replay saymak için pencere
        self.replay_window = timedelta(seconds=replay_window_seconds)

    def process_msg(self, msg: CANMessage) -> Tuple[bool, str]:
        key: Tuple[int, bytes] = (msg.can_id, msg.payload)
        now = msg.timestamp

        # 1) Seq tabanlı kontrol (eğer seq mevcutsa)
        if msg.can_id in self.last_seq:
            prev_seq = self.last_seq[msg.can_id]
            # seq aynı veya daha küçükse - replay veya tekrar gönderim / geri sarmalayıcı
            if msg.seq <= prev_seq:
                reason = (f"REJECTED - sequence not increasing for CAN ID {msg.can_id}: "
                          f"prev_seq={prev_seq}, incoming_seq={msg.seq}")
                return False, reason

        # 2) Payload tekrar kontrolü (aynı can_id+payload kısa süre içinde gelmişse)
        if key in self.last_seen:
            last_time = self.last_seen[key]
            if now - last_time <= self.replay_window:
                reason = (f"REJECTED - replay detected for CAN ID {msg.can_id} payload={msg.payload} "
                          f"(last seen {now - last_time} ago)")
                return False, reason

        # Kabul: durumları güncelle
        self.last_seq[msg.can_id] = msg.seq
        self.last_seen[key] = now

        # Simule: ECU'ya iletildi
        return True, f"ACCEPTED - forwarded to ECU (CAN ID {msg.can_id}, seq={msg.seq})"

# Demo: örnek mesaj akışı (bazı replay/tekrar mesajlar içeriyor)
def demo():
    f = CANReplayFilter(replay_window_seconds=3.0)

    base = datetime.now()
    msgs = [
        # Normal: seq artıyor -> kabul
        CANMessage(0x100, b'\x01\x02\x03', seq=1, timestamp=base + timedelta(seconds=0)),
        CANMessage(0x100, b'\x01\x02\x04', seq=2, timestamp=base + timedelta(seconds=0.5)),
        # Replay: aynı payload, kısa süre (window içinde) -> reddedilir
        CANMessage(0x100, b'\x01\x02\x03', seq=3, timestamp=base + timedelta(seconds=1.0)),
        # Seq gerilemesi: aynı CAN ID için seq küçük -> reddedilir
        CANMessage(0x100, b'\x05\x06', seq=2, timestamp=base + timedelta(seconds=2.0)),
        # Farklı CAN ID, normal
        CANMessage(0x200, b'\xaa\xbb', seq=1, timestamp=base + timedelta(seconds=2.5)),
        # Aynı payload ama window sonrası -> kabul (eski mesaj artık replay sayılmaz)
        CANMessage(0x100, b'\x01\x02\x03', seq=4, timestamp=base + timedelta(seconds=5.5)),
        # Tekrar aynı seq ile gelirse (seq=4 tekrar) -> reddedilir
        CANMessage(0x100, b'\x01\x02\x03', seq=4, timestamp=base + timedelta(seconds=6.0)),
        # Yeni seq, yeni payload -> kabul
        CANMessage(0x100, b'\x07\x08', seq=5, timestamp=base + timedelta(seconds=6.5)),
    ]

    print("=== CAN Replay Filter Demo ===\n")
    for m in msgs:
        accepted, reason = f.process_msg(m)
        ts = m.timestamp.strftime("%H:%M:%S.%f")[:-3]
        status = "OK" if accepted else "ANOMALY"
        print(f"[{ts}] CAN_ID=0x{m.can_id:X} seq={m.seq} payload={m.payload.hex()} -> {status}: {reason}")
        # küçük gecikme gösterimi (simüle)
        time.sleep(0.05)

if __name__ == "__main__":
    demo()
