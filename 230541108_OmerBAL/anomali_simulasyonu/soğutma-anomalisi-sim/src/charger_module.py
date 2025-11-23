# Bu dosya, şarj istasyonunun sıcaklık ve enerji verilerini CAN üzerinden gönderir.
# vcan0 sanal CAN veri yolunda periyodik MeterValues mesajları yollar.

import can
import time
import random
import logging

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/charger.log'),
        logging.StreamHandler()
    ]
)

def send_meter_values(bus):
    """
    Sıcaklık ve enerji verilerini CAN mesajı olarak gönder.
    Veri formatı: [sıcaklık (0-100), enerji (0-255)]
    """
    # Sıcaklık: 20-30°C arasında rastgele
    temperature = random.uniform(20, 30)
    temp_byte = int(temperature)  # 0-255 arasında olmalı
    
    # Enerji: 0-100Wh arasında rastgele
    energy = random.uniform(0, 100)
    energy_byte = int(energy) % 256  # 0-255 arasında olmalı
    
    # CAN mesajı oluştur - data parametresi liste olmalı ve tüm değerler 0-255 arasında
    message = can.Message(
        arbitration_id=0x123,
        data=[temp_byte, energy_byte, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
        is_extended_id=False
    )
    
    bus.send(message)
    logging.info(f"Sent: Temperature={temperature:.1f}°C, Energy={energy:.1f}Wh")

def main():
    """
    Ana fonksiyon: vcan0'a bağlan ve periyodik veriler gönder.
    """
    try:
        # Yeni interface parametresi kullan (deprecated uyarısını çöz)
        bus = can.interface.Bus(channel='vcan0', interface='socketcan')
        logging.info("Charger Module başlatıldı, vcan0'a bağlandı.")
        
        # Periyodik olarak veri gönder (her 2 saniyede bir)
        while True:
            send_meter_values(bus)
            time.sleep(2)
    
    except KeyboardInterrupt:
        logging.info("Charger Module durduruldu.")
        bus.shutdown()
    except Exception as e:
        logging.error(f"Hata: {e}")

if __name__ == "__main__":
    main()