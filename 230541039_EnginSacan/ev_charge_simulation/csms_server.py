import asyncio
import logging
import websockets
from datetime import datetime

# GEREKLİ İMPORTLAR EKLENDİ
from ocpp.v16 import ChargePoint as cp 
from ocpp.v16 import call_result
from ocpp.v16.enums import RegistrationStatus, Action  # <-- 'Action' eklendi
from ocpp.routing import on  # <-- '@on' dekore edicisini doğru yerden import et

logging.basicConfig(level=logging.INFO)


class CentralSystem(cp):
    """
    Bu sınıf, Merkez'e (CSMS) bağlanan her bir Şarj İstasyonunu (CP)
    temsil eder.
    """

    # HATA BURADAYDI: Kütüphaneye bu metodun hangi 'Action' için olduğunu
    # bildiren '@on(...)' dekore edicisi eksikti.
    @on(Action.boot_notification)
    async def on_boot_notification(self, charge_point_vendor, charge_point_model, **kwargs):
        """ CP'den BootNotification aldığımızda. """
        print(f"MERKEZ (CSMS): '{self.id}' BootNotification aldı (Model: {charge_point_model}).")
        
        # CP'ye onay yanıtı gönder
        return call_result.BootNotification(
            current_time=datetime.utcnow().isoformat() + "Z",
            interval=10,  # Heartbeat interval
            status=RegistrationStatus.accepted
        )

    @on(Action.meter_values)
    async def on_meter_values(self, connector_id, meter_value, **kwargs):
        """ CP'den MeterValues aldığımızda. """
        print("---------------------------------------------")
        print(f"MERKEZ (CSMS): '{self.id}' sitesinden MeterValues alındı:")
        
        # HATA DÜZELTMESİ (SON DENEME):
        # Kütüphane, JSON'daki 'sampledValue' anahtarını
        # Python'da 'sampled_value' (snake_case) olarak dönüştürüyor.
        try:
            for mv in meter_value:
                # 'sampled_value' (snake_case) kullan
                for sv in mv['sampled_value']: 
                    # 'measurand' ve 'value' (zaten snake_case'e yakın)
                    if sv['measurand'] == "Energy.Active.Import.Register":
                        print(f"  -> OKUNAN DEĞER: {sv['value']} kWh")
        except Exception as e:
            print(f"  -> MeterValues verisi işlenirken hata: {e}")
            
        print("---------------------------------------------")
        
        # CP'ye onay mesajı gönder
        return call_result.MeterValues()
        """ CP'den MeterValues aldığımızda. """
        print("---------------------------------------------")
        print(f"MERKEZ (CSMS): '{self.id}' sitesinden MeterValues alındı:")
        
        # HATA DÜZELTMESİ (TEKRAR):
        # 'mv' bir sözlüktür (dict). Veriye nesne gibi (mv.sampled_value)
        # değil, sözlük anahtarı (mv['sampledValue']) ile erişmeliyiz.
        # Anahtarlar, JSON'daki gibi BÜYÜK/küçük harfe duyarlıdır.
        try:
            for mv in meter_value:
                # mv['sampledValue'] (CamelCase) kullan
                for sv in mv['sampledValue']: 
                    # sv['measurand'] ve sv['value'] (camelCase) kullan
                    if sv['measurand'] == "Energy.Active.Import.Register":
                        print(f"  -> OKUNAN DEĞER: {sv['value']} kWh")
        except Exception as e:
            print(f"  -> MeterValues verisi işlenirken hata: {e}")
            
        print("---------------------------------------------")
        
        # CP'ye onay mesajı gönder
        return call_result.MeterValues()

async def on_connect(websocket):
    """ 
    Yeni bir CP bağlandığında 'websockets' bu fonksiyonu çağırır.
    """
    try:
        # 'path' bilgisi 'websocket.request.path' içindedir
        charge_point_id = websocket.request.path.strip('/') 
        
        print(f"MERKEZ (CSMS): CP '{charge_point_id}' bağlanıyor...")
        
        # Bağlanan CP için CentralSystem nesnesi oluştur
        cs = CentralSystem(charge_point_id, websocket)
        
        # Bağlantı açık kaldığı sürece mesajları dinle
        await cs.start()

    except Exception as e:
        logging.error(f"MERKEZ (CSMS): Bağlantı hatası: {e}", exc_info=True)


async def main():
    print("CSMS Sunucusu 9000 portunda başlatıldı... (Decorator'lu Versiyon)")
    
    server = await websockets.serve(
        on_connect,
        '0.0.0.0',
        9000,
        subprotocols=['ocpp1.6']
    )
    
    await server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCSMS Sunucusu kapatıldı.")