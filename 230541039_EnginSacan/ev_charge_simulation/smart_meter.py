import can
import time

def send_meter_reading(bus, energy_kwh):
    """
    CAN bus üzerinden enerji okuma (kWh) bilgisi gönderir.
    CAN ID 0x300, 4 byte'lık veri (enerji değeri * 10)
    """
    try:
        # Enerji değerini (float) bir integer'a (örn: 50.5 kWh -> 505)
        # 4 byte (32-bit) olarak paketleyelim.
        energy_int = int(energy_kwh * 10)
        
        # 4 byte'a (32-bit integer) dönüştür
        # little-endian (düşük byte önce)
        data_payload = energy_int.to_bytes(4, byteorder='little')

        message = can.Message(
            arbitration_id=0x300,
            data=data_payload,
            is_extended_id=False
        )
        
        bus.send(message)
        print(f"SAYAÇ -> CAN [0x300]: {energy_kwh} kWh gönderildi (Payload: {data_payload.hex()})")

    except can.CanError:
        print("CAN mesajı gönderilemedi.")

def main():
    print("Smart Meter Simülatörü başlatıldı (vcan0)...")
    try:
        bus = can.interface.Bus(channel='vcan0', bustype='socketcan')
    except OSError:
        print("vcan0 arayüzü bulunamadı.")
        print("Lütfen 'sudo ip link set up vcan0' komutunu çalıştırdığınızdan emin olun.")
        return

    current_energy = 0
    while True:
        current_energy += 10.5  # Her 5 saniyede 10.5 kWh eklendiğini varsay
        send_meter_reading(bus, round(current_energy, 1))
        time.sleep(5)

if __name__ == "__main__":
    main()