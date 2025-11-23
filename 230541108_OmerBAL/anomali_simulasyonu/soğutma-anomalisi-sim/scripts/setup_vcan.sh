#!/bin/bash
# Bu script, Kali Linux üzerinde sanal CAN arayüzü (vcan0) kurulumunu yapar.

# vcan modülünü yükle
sudo modprobe vcan

# vcan0 arayüzünü oluştur
sudo ip link add dev vcan0 type vcan

# vcan0 arayüzünü etkinleştir
sudo ip link set up vcan0

echo "vcan0 arayüzü başarıyla kuruldu ve etkinleştirildi."