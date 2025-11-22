import asyncio
import can
import logging
import websockets  # <-- Yeni eklendi
from ocpp.v16 import ChargePoint as cp
from ocpp.v16 import call
from datetime import datetime

logging.basicConfig(level=logging.INFO)

# Global değişken: CSMS'e bağlı CP nesnesini tutmak için
connected_charge_point = None

class MyChargePoint(cp):
    
    async def send_meter_values(self, kwh_value):
        """ CSMS'e (Merkez) MeterValues gönderir. """
        payload = call.MeterValues(
            connector_id=1,
            transaction_id=12345,  # Senaryo için sabit bir ID
            meter_value=[
                {
                    "timestamp": datetime.utcnow().isoformat() + "Z", # 'Z' eklendi (UTC)
                    "sampledValue": [
                        {
                            "value": str(kwh_value),
                            "context": "Sample.Periodic",
                            "measurand": "Energy.Active.Import.Register",
                            "unit": "kWh"
                        }
                    ]
                }
            ]
        )
        
        try:
            print(f"ISTASYON (CP) -> MERKEZ (CSMS): {kwh_value} kWh raporlanıyor...")
            response = await self.call(payload)
            # print(f"ISTASYON (CP): MeterValues onayı alındı: {response}")
        except Exception as e:
            print(f"ISTASYON (CP): MeterValues gönderilemedi! Hata: {e}")

    # BootNotification göndermek için ayrı bir metod ekledik
    async def send_boot_notification(self):
        """ CSMS'e BootNotification gönderir. """
        payload = call.BootNotification(
            charge_point_vendor="Grup Projesi",
            charge_point_model="Sim-v1"
        )
        try:
            response = await self.call(payload)
            print(f"ISTASYON (CP): BootNotification onayı alındı: {response}")
        except Exception as e:
            print(f"ISTASYON (CP): BootNotification gönderilemedi! Hata: {e}")


async def can_listener(bus, cp_instance):
    """ vcan0 arayüzünü dinler ve 0x300 ID'li mesajları işler. """
    print("ISTASYON (CP): CAN Bus (vcan0) dinleniyor...")
    
    # HATA 2 (Düzeltme):
    # 1. Okuyucuyu argümansız başlat
    reader = can.AsyncBufferedReader()
    
    # 2. Notifier'ı oluşturup bus'ı reader'a bağla
    #    (ve mevcut asyncio döngüsünü kullan)
    loop = asyncio.get_running_loop()
    notifier = can.Notifier(bus, [reader], loop=loop)
    
    try:
        # 'async for' ile asenkron okuyucu üzerinden mesajları bekle
        async for message in reader:
            if message.arbitration_id == 0x300:
                # Gelen 4 byte'lık veriyi (little-endian) integer'a çevir
                energy_int = int.from_bytes(message.data[:4], byteorder='little')
                
                # Veriyi kWh float değerine dönüştür (gönderirken *10 yapmıştık)
                energy_kwh = round(energy_int / 10.0, 1)
                
                print(f"ISTASYON (CP): CAN [0x300] alındı. Okunan değer: {energy_kwh} kWh")

                # Eğer CP, CSMS'e bağlıysa, bu veriyi OCPP ile gönder
                if cp_instance:
                    # Görevi arka planda çalıştır (await yapma ki CAN dinlemeyi bloklamasın)
                    asyncio.create_task(cp_instance.send_meter_values(energy_kwh))
                else:
                    print("ISTASYON (CP): CSMS bağlantısı henüz yok. MeterValues gönderilemiyor.")

    except Exception as e:
        print(f"CAN dinleyici hatası: {e}")
    finally:
        notifier.stop() # Notifier'ı durdurmak önemli
        print("ISTASYON (CP): CAN dinleyici durdu.")


# BU FONKSİYON TAMAMEN YENİDEN YAZILDI
async def main_cp(bus):
    global connected_charge_point
    
    # URL, CSMS sunucusunda path'e göre CP ID'si beklediğimiz için ID'yi içermeli
    url = "ws://127.0.0.1:9000/CP_001" 
    
    can_task = None
    try:
        # 'websockets.connect' doğru async context manager'dır
        async with websockets.connect(
            url,
            subprotocols=['ocpp1.6']
        ) as ws:
            
            print("ISTASYON (CP): Merkeze (CSMS) bağlanıldı.")
            
            # Bağlantı (ws) var, şimdi ChargePoint nesnemizi oluşturuyoruz
            charge_point = MyChargePoint('CP_001', ws)
            connected_charge_point = charge_point # Global değişkeni ayarla

            # İKİ GÖREVİ AYNI ANDA BAŞLATMALIYIZ:
            # 1. CAN dinleyici (vcan0'dan okur)
            # 2. OCPP dinleyici (Merkezden gelen mesajları dinler)

            # 1. CAN dinleyiciyi arka planda bir görev olarak başlat
            can_task = asyncio.create_task(can_listener(bus, charge_point))
            
            # İlk BootNotification'ı gönder
            await charge_point.send_boot_notification()

            # 2. Ana OCPP döngüsünü başlat (Merkez'den gelen mesajları dinler)
            # Bu fonksiyon, bağlantı kapanana kadar (veya hata alana kadar) çalışır.
            await charge_point.start()

    except Exception as e:
        print(f"ISTASYON (CP): Bağlantı hatası: {e}")
        if isinstance(e, websockets.exceptions.ConnectionClosedError):
            print("     -> CSMS sunucusu çalışmıyor veya bağlantıyı reddetti.")
    finally:
        # Program kapanırken CAN görevini de temizle
        if can_task and not can_task.done():
            can_task.cancel()
        if connected_charge_point:
            connected_charge_point = None
        print("ISTASYON (CP): Bağlantı kapandı.")


if __name__ == "__main__":
    try:
        can_bus = can.interface.Bus(channel='vcan0', interface='socketcan', receive_own_messages=False)
        # 'bustype' uyarısı için 'interface' olarak güncellendi
    except OSError:
        print("vcan0 arayüzü bulunamadı.")
        print("Lütfen 'sudo ip link set up vcan0' komutunu çalıştırdığınızdan emin olun.")
        exit(1)

    print("İstasyon (CP) Simülatörü [NORMAL MOD] başlatıldı...")
    try:
        asyncio.run(main_cp(can_bus))
    except KeyboardInterrupt:
        print("\nİstasyon (CP) kapatıldı.")
    finally:
        can_bus.shutdown()