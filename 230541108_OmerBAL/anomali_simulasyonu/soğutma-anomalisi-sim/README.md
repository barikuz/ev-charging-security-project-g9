# Soğutma Sistemi Anomalisi Simülasyonu

## Proje Açıklaması
Bu proje, bir elektrikli araç (EV) şarj istasyonunda soğutma sisteminin uzaktan devre dışı bırakılması anomalisini simüle etmek amacıyla geliştirilmiştir. Proje, eğitim ve simülasyon amaçlıdır ve gerçek cihazları etkilemez. Tüm CAN iletişimleri sanal `vcan0` arayüzü üzerinden gerçekleştirilecektir.

## Kurulum Adımları

1. **Gerekli Paketlerin Kurulumu**
   - Python 3.10+ sürümünü kullanmanızı öneririz.
   - Proje dizininde bir sanal ortam oluşturun:
     ```bash
     python3 -m venv venv
     ```
   - Sanal ortamı etkinleştirin:
     ```bash
     source venv/bin/activate
     ```
   - Gerekli Python paketlerini yükleyin:
     ```bash
     pip install -r requirements.txt
     ```

2. **vcan0 Arayüzünün Kurulumu**
   - Aşağıdaki komutları kullanarak `vcan0` arayüzünü kurun:
     ```bash
     sudo modprobe vcan
     sudo ip link add dev vcan0 type vcan
     sudo ip link set up vcan0
     ```

## Çalıştırma Adımları

1. `csms_sim.py` dosyasını arka planda çalıştırın:
   ```bash
   python src/csms_sim.py &
   ```
2. `charger_module.py` dosyasını arka planda çalıştırın:
   ```bash
   python src/charger_module.py &
   ```
3. `cp_agent.py` dosyasını çalıştırın:
   ```bash
   python src/cp_agent.py
   ```
4. Anomali modunu etkinleştirmek için `anomaly_injector.py` dosyasını çalıştırın:
   ```bash
   python src/anomaly_injector.py --inject
   ```
5. Test senaryolarını çalıştırmak için:
   ```bash
   pytest tests/test_flow.py
   ```

## Etik Uyarı
Bu proje, gerçek cihazlara asla uygulanmayacak şekilde tasarlanmıştır. Eğitim ve simülasyon amaçlıdır.

## Hata Çözüm İpuçları
- Eğer `vcan0` kurulmazsa, `ip link show` ile kontrol edin. `sudo` yetkisi gereklidir.
- `python-can` bağlanamıyorsa, `bustype='socketcan'` ve `channel='vcan0'` ayarlarını kullanın.
- Paket kurulum hatalarında pip'i güncellemek için:
  ```bash
  python -m pip install --upgrade pip
  ```
- Port çakışması veya izin sorunları için `sudo setcap` komutunu kullanabilirsiniz.

## Log Dosyaları
- Normal çalışma olayları `logs/normal.log` dosyasında kaydedilecektir.
- Anomalilere dair olaylar `logs/anomaly.log` dosyasında kaydedilecektir.
- Algılanan uyarılar `logs/alerts.log` dosyasında kaydedilecektir. 

## Örnek Log Satırı
```
[ALERT] Fan is OFF and temperature increased by 5°C over 5 samples.
```