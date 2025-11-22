#!/bin/bash

echo "--- Elektrikli Araç Şarj Simülasyonu Kurulumu Başlıyor ---"

# 1. Sistem Paketlerini Güncelle ve can-utils Kur
echo "[1/5] Sistem paketleri güncelleniyor ve can-utils kuruluyor..."
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv can-utils

# 2. Sanal Ortam (venv) Oluştur
echo "[2/5] Python sanal ortamı (venv) oluşturuluyor..."
if [ -d "venv" ]; then
    echo "      (venv klasörü zaten var, atlanıyor.)"
else
    python3 -m venv venv
    echo "      (venv oluşturuldu.)"
fi

# 3. Kütüphaneleri Yükle
echo "[3/5] Gerekli Python kütüphaneleri yükleniyor..."
source venv/bin/activate
pip install -r requirements.txt

# 4. vcan0 Arayüzünü Kur (Sanal CAN Hattı)
echo "[4/5] Sanal CAN (vcan0) arayüzü ayarlanıyor..."
# Modülü yükle
sudo modprobe vcan
# Arayüzü ekle (hata verirse -zaten varsa- görmezden gel)
sudo ip link add dev vcan0 type vcan 2> /dev/null
# Arayüzü ayağa kaldır
sudo ip link set up vcan0

echo "--- Kurulum Tamamlandı! ---"
echo "Simülasyonu başlatmak için README.md dosyasındaki adımları takip edin."