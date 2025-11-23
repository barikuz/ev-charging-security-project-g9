# Bu dosya, soğutma sisteminin kapalı olduğunu simüle eden anomali enjekte eder.
# INJECT_ANOMALY=true ortam değişkeni ile tetiklenir.

import os
import time
import can
import logging
import sys

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/anomaly.log'),
        logging.StreamHandler()
    ]
)

class AnomalyInjector:
    def __init__(self):
        # Ortam değişkeni veya CLI parametresinden anomali flag'ı oku
        self.inject_anomaly = os.getenv('INJECT_ANOMALY', 'false').lower() == 'true'
        
        # CLI parametresi de kontrol et
        if '--inject' in sys.argv:
            self.inject_anomaly = True
        
        # Yeni interface parametresi kullan (deprecated uyarısını çöz)
        self.bus = can.interface.Bus(channel='vcan0', interface='socketcan')
        logging.info(f"Anomaly Injector başlatıldı. Anomali modu: {self.inject_anomaly}")
    
    def send_fan_off_message(self):
        """
        Fan kapalı (OFF) mesajını gönder.
        Arbitration ID: 0x124, Data: [0x01, 0x00] (Fan OFF)
        """
        msg = can.Message(
            arbitration_id=0x124,
            data=[0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
            is_extended_id=False
        )
        self.bus.send(msg)
        logging.warning("🔴 Fan OFF mesajı gönderildi - ANOMALI BAŞLADI!")
    
    def send_fan_on_message(self):
        """
        Fan açık (ON) mesajını gönder.
        Arbitration ID: 0x124, Data: [0x01, 0x01] (Fan ON)
        """
        msg = can.Message(
            arbitration_id=0x124,
            data=[0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
            is_extended_id=False
        )
        self.bus.send(msg)
        logging.info("🟢 Fan ON mesajı gönderildi - Sistem normal")
    
    def run(self):
        """
        Anomali enjeksiyonunu çalıştır.
        """
        try:
            if self.inject_anomaly:
                # Fan'ı kapat
                self.send_fan_off_message()
                time.sleep(10)  # 10 saniye anomali durumunda kal
                
                # Fan'ı aç
                self.send_fan_on_message()
                logging.info("Anomali simülasyonu tamamlandı.")
            else:
                logging.info("Anomali enjeksiyonu aktif değil. Normal mod çalışıyor.")
                # Normal modda Fan ON gönder
                self.send_fan_on_message()
        
        except KeyboardInterrupt:
            logging.info("Anomaly Injector durduruldu.")
        except Exception as e:
            logging.error(f"Hata: {e}")
        finally:
            self.bus.shutdown()

if __name__ == "__main__":
    injector = AnomalyInjector()
    injector.run()