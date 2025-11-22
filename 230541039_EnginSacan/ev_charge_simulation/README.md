# Elektrikli Araç Şarj İstasyonu Güvenlik Simülasyonu (OCPP & CAN-Bus)

Bu proje, bir Elektrikli Araç Şarj İstasyonu (CP) ile Merkezi Yönetim Sistemi (CSMS) arasındaki OCPP haberleşmesini ve istasyon içi donanımların (Akıllı Sayaç) CAN-Bus veri akışını simüle eder.

Projenin temel amacı, **"Kötücül Firmware Enjeksiyonu ve Fatura Dolandırıcılığı"** siber saldırı senaryosunu uygulamalı olarak göstermektir.

---

## 🎯 Proje Senaryosu

Bu simülasyon, aynı altyapı üzerinde iki farklı durumu modeller:

### 1. ✅ Normal Akış (Dürüst İstasyon)
* **Sayaç:** Gerçek enerji tüketimini (örn. 10.5 kWh) CAN-Bus üzerinden yayınlar.
* **İstasyon:** Veriyi okur ve değiştirmeden OCPP protokolü ile Merkeze iletir.
* **Sonuç:** Kullanıcıya doğru fatura çıkarılır.

### 2. ⚠️ Anormal Akış (Saldırı Simülasyonu)
* **Tehdit Modeli:** Saldırganın istasyonun firmware'ini ele geçirdiği varsayılır (Aşama 1 & 2 atlanmıştır, doğrudan etki simüle edilir).
* **Eylem:** İstasyon, sayaçtan gelen gerçek veriyi okur ancak Merkeze göndermeden önce manipüle eder (örn. %90 düşürür).
* **Sonuç:** Enerji hırsızlığı ve hatalı faturalandırma.

---

## 🛠️ Gereksinimler

* **İşletim Sistemi:** Linux
    * *Not: Proje, Linux çekirdeğine özgü `SocketCAN` (vcan) teknolojisini kullandığı için Windows üzerinde doğrudan çalışmaz.*
* **Dil:** Python 3.8+
* **Yetki:** Sanal ağ arayüzü oluşturmak için `sudo` yetkisi gereklidir.

---

## 🚀 Kurulum (Otomatik)

Projeyi klonladıktan sonra, gerekli `can-utils` araçlarını kuran, sanal ortamı (venv) oluşturan ve kütüphaneleri yükleyen otomatik scripti çalıştırın:

1.  Terminali açın ve proje dizinine girin.
2.  Kurulum scriptini çalıştırın:

```
chmod +x setup.sh
./setup.sh
```

## ▶️ Simülasyonu Çalıştırma

Simülasyonu çalıştırmak için **3 adet terminal penceresi** gerekir.

Her terminalde önce sanal ortamı aktif edin:

```
source venv/bin/activate
```

Merkezi Yönetim Sistemi (Terminal 1)

```
python csms_server.py
```

Beklenen çıktı:

```
CSMS Sunucusu 9000 portunda başlatıldı...
```

Şarj İstasyonu (Terminal 2) 

Normal Senaryo:

```
python cp_simulator_NORMAL.py
```

Anormal (Saldırı) Senaryosu:

```
python cp_simulator_ANORMAL.py
```

Beklenen çıktı:

```
Merkeze (CSMS) bağlanıldı... CAN Bus dinleniyor...
```

Akıllı Sayaç (Terminal 3)

```
python smart_meter.py
```

Beklenen çıktı:

```
SAYAÇ -> CAN [0x300]: 10.5 kWh gönderildi
```


