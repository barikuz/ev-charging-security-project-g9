# Bu dosya, CAN veri yolundan gelen mesajları dinler ve anomali tespiti yapar.
# Kural: Fan kapalı (0x01) + Sıcaklık artışı = ALARM

import can
import logging
from collections import deque
import time

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/alerts.log'),
        logging.StreamHandler()
    ]
)

class AnomalyDetector:
    def __init__(self):
        self.bus = can.interface.Bus(channel='vcan0', interface='socketcan')
        self.temperature_history = deque(maxlen=5)  # Son 5 sıcaklık değeri
        self.fan_status = None  # Fan durumu (ON/OFF)
        self.alert_triggered = False
        
    def check_anomaly(self):
        """
        Anomali kuralını kontrol et:
        - Fan kapalı (Fan OFF) VE
        - Sıcaklık 5 saniye içinde 5°C artmış
        """
        if len(self.temperature_history) < 2:
            return False
        
        temp_diff = self.temperature_history[-1] - self.temperature_history[0]
        
        if self.fan_status == "OFF" and temp_diff >= 5.0:
            return True
        
        return False
    
    def run(self):
        """
        CAN mesajlarını dinle ve anomali tespiti yap.
        """
        logging.info("Anomaly Detector başlatıldı, vcan0'u dinliyor...")
        
        try:
            for msg in self.bus:
                if msg.arbitration_id == 0x123:
                    # Charger modülünden sıcaklık ve enerji verisi
                    if len(msg.data) >= 2:
                        temperature = msg.data[0]
                        energy = msg.data[1]
                        
                        self.temperature_history.append(temperature)
                        logging.info(f"Received: Temperature={temperature}°C, Energy={energy}Wh")
                
                elif msg.arbitration_id == 0x124:
                    # Anomali injector'dan Fan durumu
                    if len(msg.data) >= 2:
                        fan_flag = msg.data[1]
                        self.fan_status = "OFF" if fan_flag == 0x00 else "ON"
                        logging.info(f"Fan Status Updated: {self.fan_status}")
                
                # Anomali kontrolü yap
                if self.check_anomaly() and not self.alert_triggered:
                    logging.warning("⚠️ ANOMALI TESPİT EDİLDİ! Soğutma sistemi kapalı + Sıcaklık artışı!")
                    self.alert_triggered = True
                elif not self.check_anomaly():
                    self.alert_triggered = False
        
        except KeyboardInterrupt:
            logging.info("Anomaly Detector durduruldu.")
        except Exception as e:
            logging.error(f"Hata: {e}")
        finally:
            self.bus.shutdown()

if __name__ == "__main__":
    detector = AnomalyDetector()
    detector.run()