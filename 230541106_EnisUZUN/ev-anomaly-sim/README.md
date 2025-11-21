# ⚡ EV Charging Anomaly Simulator

[English](#english) | [Türkçe](#turkce)

---

## <a name="english"></a>English

A complete, runnable simulation of **"Repeated Current Fluctuation During Charging"** anomaly in Electric Vehicle charging stations with **🧠 MemoryBank** - a persistent memory system for event logging and anomaly learning.

## 🎯 Overview

This project simulates an OCPP 1.6 charging infrastructure with:
- **CSMS (Central System)** - WebSocket server orchestrating charging commands
- **Charge Point** - OCPP client that bridges OCPP messages to CAN bus
- **Virtual Charger Module** - CAN device simulating power electronics
- **Live Plotter** - Real-time visualization of charging current
- **🧠 MemoryBank** - SQLite-based persistent memory for events, anomalies, and patterns

## 🏗️ Architecture

```
┌─────────────┐        OCPP 1.6         ┌──────────────┐
│    CSMS     │◄─────WebSocket──────────►│ Charge Point │
│  (Server)   │   ws://127.0.0.1:9000    │   (Client)   │
└─────────────┘                          └───────┬──────┘
                                                 │
                                          CAN Bus│(Virtual)
                                                 │
                    ┌────────────────────────────┼────────────┐
                    │                            │            │
              ┌─────▼──────┐                ┌───▼────────┐   │
              │  Charger   │                │  Current   │   │
              │   Module   │───────0x300───►│  Plotter   │   │
              │ (CAN Node) │                │  (Monitor) │   │
              └────────────┘                └────────────┘   │
                                                              │
                    Virtual CAN Bus (interface="virtual", channel=0)
```

## 📋 Requirements

- **OS**: macOS (tested on M2)
- **Python**: 3.11
- **Dependencies**:
  - matplotlib==3.8.2
  - python-can==4.4.2
  - ocpp==0.20.0
  - websockets==12.0
  - tabulate==0.9.0 (for MemoryBank viewer)

## 🚀 Quick Start

### 1. Create Virtual Environment

```bash
cd 230541106_EnisUZUN
python3.11 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Simulation

```bash
chmod +x run_all.sh
./run_all.sh
```

This will open 4 Terminal tabs:
1. **Charger Module** - CAN device simulator
2. **CSMS Server** - OCPP server
3. **Charge Point** - OCPP client
4. **Current Plotter** - Live graph

## 📁 Project Files

### Core Components

| File | Description |
|------|-------------|
| `charger_module.py` | Virtual CAN device that publishes current readings (0x300) and responds to control commands (0x200, 0x201, 0x210) |
| `csms.py` | OCPP 1.6 WebSocket server that orchestrates the anomaly by cycling SetChargingProfile, RemoteStart/Stop (🧠 MemoryBank enabled) |
| `cp.py` | OCPP client that translates OCPP messages to CAN commands and reports MeterValues (🧠 MemoryBank enabled) |
| `plot_current.py` | Real-time matplotlib visualization of charging current (🧠 shows historical anomalies) |
| `memory_bank.py` | SQLite-based persistent memory system for events, anomalies, sessions, and patterns |
| `memory_viewer.py` | Interactive tool to view and analyze MemoryBank data |
| `run_all.sh` | Launcher script that starts all components in separate Terminal tabs |

### Configuration Files

| File | Description |
|------|-------------|
| `requirements.txt` | Python package dependencies |
| `README.md` | This file |

## 🔌 CAN Message Protocol

| CAN ID | Direction | Purpose | Data Format |
|--------|-----------|---------|-------------|
| 0x200 | CP → Charger | Start charging | Empty |
| 0x201 | CP → Charger | Stop charging | Empty |
| 0x210 | CP → Charger | Set current limit | [limit_low, limit_high] (little-endian) |
| 0x300 | Charger → All | Current reading | [current_low, current_high] (little-endian) |

## 🎭 Anomaly Scenario

The CSMS executes this cycle repeatedly:

1. **SetChargingProfile(0A)** → Limit current to 0A
2. *Wait 2 seconds*
3. **SetChargingProfile(100A)** → Raise limit to 100A
4. *Wait 1 second*
5. **RemoteStartTransaction** → Start charging
6. *Wait 2 seconds*
7. **RemoteStopTransaction** → Stop charging
8. *Wait 3 seconds*
9. **Repeat**

This creates a repeating pattern of current fluctuations: **0A → 100A → 0A → 100A**

## 🖥️ Component Details

### Charger Module (`charger_module.py`)

- Runs on virtual CAN bus (interface="virtual", channel=0)
- Publishes current readings every 1 second on CAN ID 0x300
- Smoothly ramps current (20% per iteration) to simulate realistic behavior
- Responds to control commands from Charge Point

### CSMS (`csms.py`)

- WebSocket server on ws://127.0.0.1:9000/
- Implements OCPP 1.6 server-side operations
- Handles BootNotification and MeterValues from charge points
- Orchestrates anomaly scenario in infinite loop

### Charge Point (`cp.py`)

- OCPP 1.6 client connecting to CSMS
- Implements handlers for RemoteStartTransaction, RemoteStopTransaction, SetChargingProfile
- Translates OCPP commands to CAN messages
- Reads CAN 0x300 and sends MeterValues to CSMS every second

### Current Plotter (`plot_current.py`)

- Subscribes to CAN ID 0x300 (current readings)
- Displays live matplotlib graph with 60-second rolling window
- Shows anomaly detection indicator when fluctuations detected
- Real-time current value display

## 🛠️ Manual Testing

To run components individually:

```bash
# Terminal 1: Start charger module
source venv/bin/activate
python3 charger_module.py

# Terminal 2: Start CSMS server
source venv/bin/activate
python3 csms.py

# Terminal 3: Start charge point
source venv/bin/activate
python3 cp.py

# Terminal 4: Start plotter
source venv/bin/activate
python3 plot_current.py
```

## 🐛 Troubleshooting

### Issue: "No module named 'can'"
**Solution**: Ensure virtual environment is activated and dependencies are installed:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: Components can't communicate
**Solution**: Ensure all components use the same CAN bus configuration:
- `interface="virtual"`
- `channel=0`
- No `extended_id` or `is_extended_id=False`

### Issue: Plotter shows no data
**Solution**: 
1. Check that charger_module.py is running
2. Verify CAN bus is working: `python3 -c "import can; bus = can.interface.Bus(interface='virtual', channel=0); print('OK')"`

### Issue: WebSocket connection refused
**Solution**: Ensure CSMS is running before starting Charge Point

## 📊 Expected Output

When running correctly, you should see:

1. **Charger Module**: Current values ramping up/down
2. **CSMS**: Sending OCPP commands in cycles (🧠 recording to MemoryBank)
3. **Charge Point**: Receiving OCPP, sending CAN, reporting MeterValues (🧠 logging events)
4. **Plotter**: Live graph showing 0A ↔ 100A fluctuations with anomaly indicator and statistics

## 🧠 MemoryBank Features

The MemoryBank system provides persistent memory and learning capabilities:

### What MemoryBank Records

- **Events**: All OCPP messages, CAN communications, system events
- **Anomalies**: Detected anomalies with severity, patterns, and deviations
- **Sessions**: Charging session metadata (start/end time, energy, statistics)
- **Metrics**: Current, voltage, power measurements over time
- **Patterns**: Learned behavior patterns for anomaly detection

### Using MemoryBank Viewer

View and analyze collected data:

```bash
# Interactive menu
python3 memory_viewer.py

# Quick summary
python3 memory_viewer.py --summary

# View recent events
python3 memory_viewer.py --events 50

# View anomalies
python3 memory_viewer.py --anomalies 20

# View sessions
python3 memory_viewer.py --sessions 10

# Export data to JSON
python3 memory_viewer.py --export data_export.json

# Show statistics
python3 memory_viewer.py --stats
```

### Database Location

All data is stored in: `ev_charging_memory.db` (SQLite database)

You can view this database with any SQLite viewer or use the provided `memory_viewer.py` tool.

## 🔒 Technical Notes

- **Virtual CAN Bus**: Uses python-can's virtual bus (no kernel modules needed)
- **No socketcan/vcan**: Compatible with macOS without CAN hardware
- **Thread-safe**: CAN bus operations are thread-safe across processes
- **Asyncio**: OCPP components use asyncio for concurrent operations
- **Real-time**: All components update at 1-second intervals
- **🧠 Persistent Memory**: SQLite database for event history and learning

## 📝 License

This is a simulation/educational project. Use freely for learning and testing purposes.

## 🤝 Contributing

This is a complete, self-contained simulation. Modify as needed for your use case.

## ⚠️ Disclaimer

This is a **simulation** for testing and demonstration purposes. It mimics the behavior of real EV charging infrastructure but should not be used in production environments without proper adaptation and safety measures.

---

## <a name="turkce"></a>🇹🇷 Türkçe Dokümantasyon

### 📋 Genel Bakış

Bu proje, Elektrikli Araç (EV) şarj istasyonlarında **"Şarj Sırasında Tekrarlanan Akım Dalgalanması"** anomalisini simüle eden eksiksiz, çalıştırılabilir bir sistemdir. **🧠 MemoryBank** kalıcı hafıza sistemi ile olay kaydı ve anomali öğrenme özelliklerine sahiptir.

### 🎯 Sistem Bileşenleri

Bu proje bir OCPP 1.6 şarj altyapısını simüle eder:

- **CSMS (Merkezi Sistem)** - Şarj komutlarını yöneten WebSocket sunucusu
- **Charge Point (Şarj İstasyonu)** - OCPP mesajlarını CAN bus'a köprüleyen OCPP istemcisi
- **Sanal Şarj Modülü** - Güç elektroniğini simüle eden CAN cihazı
- **Canlı Grafik** - Şarj akımının gerçek zamanlı görselleştirmesi
- **🧠 MemoryBank** - Olay, anomali ve desen öğrenme için SQLite tabanlı kalıcı hafıza sistemi

### 🏗️ Mimari

```
┌─────────────┐        OCPP 1.6         ┌──────────────┐
│    CSMS     │◄─────WebSocket──────────►│ Charge Point │
│  (Sunucu)   │   ws://127.0.0.1:9000    │  (İstemci)   │
└─────────────┘                          └───────┬──────┘
                                                 │
                                          CAN Bus│(Sanal)
                                                 │
                    ┌────────────────────────────┼────────────┐
                    │                            │            │
              ┌─────▼──────┐                ┌───▼────────┐   │
              │   Şarj     │                │   Akım     │   │
              │  Modülü    │───────0x300───►│  Grafiği   │   │
              │ (CAN Node) │                │  (İzleme)  │   │
              └────────────┘                └────────────┘   │
                                                              │
                    Sanal CAN Bus (interface="virtual", channel=0)
```

### 📋 Gereksinimler

- **İşletim Sistemi**: macOS (M2 üzerinde test edildi)
- **Python**: 3.11
- **Bağımlılıklar**:
  - matplotlib==3.8.2
  - python-can==4.4.2
  - ocpp==0.20.0
  - websockets==12.0
  - tabulate==0.9.0 (MemoryBank görüntüleyici için)

### 🚀 Hızlı Başlangıç

#### 1. Sanal Ortam Oluşturun

```bash
cd 230541106_EnisUZUN
python3.11 -m venv venv
source venv/bin/activate
```

#### 2. Bağımlılıkları Yükleyin

```bash
pip install -r requirements.txt
```

#### 3. Simülasyonu Çalıştırın

```bash
chmod +x run_all.sh
./run_all.sh
```

Bu komut 4 Terminal sekmesi açacaktır:

1. **Şarj Modülü** - CAN cihaz simülatörü
2. **CSMS Sunucusu** - OCPP sunucusu
3. **Charge Point** - OCPP istemcisi
4. **Akım Grafiği** - Canlı grafik

### 📁 Proje Dosyaları

#### Ana Bileşenler

| Dosya | Açıklama |
|------|----------|
| `charger_module.py` | Akım ölçümlerini (0x300) yayınlayan ve kontrol komutlarına (0x200, 0x201, 0x210) yanıt veren sanal CAN cihazı |
| `csms.py` | SetChargingProfile ve RemoteStart/Stop döngüsü ile anomaliyi düzenleyen OCPP 1.6 WebSocket sunucusu (🧠 MemoryBank etkin) |
| `cp.py` | OCPP mesajlarını CAN komutlarına çeviren ve MeterValues raporlayan OCPP istemcisi (🧠 MemoryBank etkin) |
| `plot_current.py` | Şarj akımının gerçek zamanlı matplotlib görselleştirmesi (🧠 geçmiş anomalileri gösterir) |
| `memory_bank.py` | Olaylar, anomaliler, oturumlar ve desenler için SQLite tabanlı kalıcı hafıza sistemi |
| `memory_viewer.py` | MemoryBank verilerini görüntülemek ve analiz etmek için interaktif araç |
| `run_all.sh` | Tüm bileşenleri ayrı Terminal sekmelerinde başlatan başlatıcı script |

#### Yapılandırma Dosyaları

| Dosya | Açıklama |
|------|----------|
| `requirements.txt` | Python paket bağımlılıkları |
| `README.md` | Bu dosya |
| `MEMORYBANK.md` | MemoryBank detaylı kılavuz |

### 🔌 CAN Mesaj Protokolü

| CAN ID | Yön | Amaç | Veri Formatı |
|--------|-----|------|-------------|
| 0x200 | CP → Şarj Cihazı | Şarjı başlat | Boş |
| 0x201 | CP → Şarj Cihazı | Şarjı durdur | Boş |
| 0x210 | CP → Şarj Cihazı | Akım limitini ayarla | [limit_düşük, limit_yüksek] (little-endian) |
| 0x300 | Şarj Cihazı → Tümü | Akım ölçümü | [akım_düşük, akım_yüksek] (little-endian) |

### 🎭 Anomali Senaryosu

CSMS bu döngüyü sürekli tekrarlar:

1. **SetChargingProfile(0A)** → Akımı 0A'e sınırla
2. *2 saniye bekle*
3. **SetChargingProfile(100A)** → Limiti 100A'e yükselt
4. *1 saniye bekle*
5. **RemoteStartTransaction** → Şarjı başlat
6. *2 saniye bekle*
7. **RemoteStopTransaction** → Şarjı durdur
8. *3 saniye bekle*
9. **Tekrarla**

Bu, tekrarlayan bir akım dalgalanma deseni oluşturur: **0A → 100A → 0A → 100A**

### 📊 Beklenen Çıktı

Doğru çalıştığında görecekleriniz:

1. **Şarj Modülü**: Yukarı/aşağı rampalanan akım değerleri
2. **CSMS**: Döngüler halinde OCPP komutları gönderme (🧠 MemoryBank'e kaydediyor)
3. **Charge Point**: OCPP alıyor, CAN gönderiyor, MeterValues raporluyor (🧠 olayları logluyor)
4. **Grafik**: 0A ↔ 100A dalgalanmalarını gösteren canlı grafik, anomali göstergesi ve istatistikler

### 🧠 MemoryBank Özellikleri

MemoryBank sistemi kalıcı hafıza ve öğrenme yetenekleri sağlar:

#### MemoryBank Neyi Kaydeder

- **Olaylar**: Tüm OCPP mesajları, CAN iletişimi, sistem olayları
- **Anomaliler**: Şiddet, desenler ve sapmalarla tespit edilen anomaliler
- **Oturumlar**: Şarj oturumu meta verileri (başlangıç/bitiş zamanı, enerji, istatistikler)
- **Metrikler**: Zaman içinde akım, voltaj, güç ölçümleri
- **Desenler**: Anomali tespiti için öğrenilen davranış desenleri

#### MemoryBank Görüntüleyiciyi Kullanma

Toplanan verileri görüntüleyin ve analiz edin:

```bash
# İnteraktif menü
python3 memory_viewer.py

# Hızlı özet
python3 memory_viewer.py --summary

# Son olayları görüntüle
python3 memory_viewer.py --events 50

# Anomalileri görüntüle
python3 memory_viewer.py --anomalies 20

# Oturumları görüntüle
python3 memory_viewer.py --sessions 10

# Verileri JSON'a aktar
python3 memory_viewer.py --export data_export.json

# İstatistikleri göster
python3 memory_viewer.py --stats
```

#### Veritabanı Konumu

Tüm veriler şurada saklanır: `ev_charging_memory.db` (SQLite veritabanı)

Bu veritabanını herhangi bir SQLite görüntüleyici ile görüntüleyebilir veya sağlanan `memory_viewer.py` aracını kullanabilirsiniz.

#### Python API Kullanımı

```python
from memory_bank import MemoryBank

# MemoryBank'i başlat
memory = MemoryBank()

# Olay kaydet
memory.log_event(
    "OCPP_MESSAGE",
    "CSMS",
    "İşlem başlatıldı",
    {"transaction_id": 12345}
)

# Anomali kaydet
memory.record_anomaly(
    "CURRENT_FLUCTUATION",
    "HIGH",
    "Hızlı akım değişimi tespit edildi",
    current_value=150.0,
    expected_value=50.0
)

# İstatistikleri al
stats = memory.get_metric_statistics("current")
print(f"Ortalama akım: {stats['avg']:.2f} A")

# Özet rapor
summary = memory.get_dashboard_summary()
print(f"Toplam anomali: {summary['total_anomalies']}")
```

### 🔒 Teknik Notlar

- **Sanal CAN Bus**: python-can'ın sanal bus'ını kullanır (kernel modülü gerekmez)
- **socketcan/vcan yok**: CAN donanımı olmadan macOS ile uyumlu
- **Thread-safe**: CAN bus işlemleri process'ler arası thread-safe
- **Asyncio**: OCPP bileşenleri eşzamanlı işlemler için asyncio kullanır
- **Gerçek zamanlı**: Tüm bileşenler 1 saniyelik aralıklarla güncellenir
- **🧠 Kalıcı Hafıza**: Olay geçmişi ve öğrenme için SQLite veritabanı

### 🛠️ Manuel Test

Bileşenleri ayrı ayrı çalıştırmak için:

```bash
# Terminal 1: Şarj modülünü başlat
source venv/bin/activate
python3 charger_module.py

# Terminal 2: CSMS sunucusunu başlat
source venv/bin/activate
python3 csms.py

# Terminal 3: Charge point'i başlat
source venv/bin/activate
python3 cp.py

# Terminal 4: Grafiği başlat
source venv/bin/activate
python3 plot_current.py
```

### 🐛 Sorun Giderme

#### Sorun: "No module named 'can'"

**Çözüm**: Sanal ortamın etkinleştirildiğinden ve bağımlılıkların yüklendiğinden emin olun:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

#### Sorun: Bileşenler iletişim kuramıyor

**Çözüm**: Tüm bileşenlerin aynı CAN bus yapılandırmasını kullandığından emin olun:

- `interface="virtual"`
- `channel=0`
- `extended_id` yok veya `is_extended_id=False`

#### Sorun: Grafik veri göstermiyor

**Çözüm**:

1. charger_module.py'nin çalıştığını kontrol edin
2. CAN bus'ın çalıştığını doğrulayın: `python3 -c "import can; bus = can.interface.Bus(interface='virtual', channel=0); print('OK')"`

#### Sorun: WebSocket bağlantısı reddedildi

**Çözüm**: Charge Point'i başlatmadan önce CSMS'in çalıştığından emin olun

#### Sorun: MemoryBank veritabanı hatası

**Çözüm**: Veritabanını yedekleyin ve yeniden oluşturun:

```bash
cp ev_charging_memory.db ev_charging_memory.db.backup
rm ev_charging_memory.db
python3 csms.py  # Yeni veritabanı otomatik oluşturulur
```

### 📈 Kullanım Senaryoları

#### 1. Güvenlik Testi ve Anomali Analizi

```bash
# Simülasyonu çalıştır
./run_all.sh

# Kritik anomalileri incele
python3 memory_viewer.py --anomalies 20
```

#### 2. Performans ve İstatistik Analizi

```python
from memory_bank import MemoryBank

mb = MemoryBank()
stats = mb.get_metric_statistics("current")
print(f"Maksimum akım: {stats['max']:.2f} A")
print(f"Ortalama akım: {stats['avg']:.2f} A")
```

#### 3. Öğrenilen Desenleri İnceleme

```bash
python3 memory_viewer.py
# Menüden: "5. Show Learned Patterns"
```

#### 4. Veri Dışa Aktarma ve Raporlama

```bash
# Tüm verileri JSON'a aktar
python3 memory_viewer.py --export full_report.json

# Eski verileri temizle (7 günden eski)
python3 memory_viewer.py
# Menüden: "9. Clean Old Data"
```

### 🎓 Eğitim Amaçları

Bu proje şunları öğrenmek için kullanılabilir:

- OCPP protokolü ve EV şarj iletişimi
- CAN bus protokolü ve mesajlaşma
- Anomali tespit algoritmaları
- Gerçek zamanlı veri görselleştirme
- SQLite veritabanı yönetimi
- Python asyncio programlama
- WebSocket iletişimi

### 🔐 Güvenlik Uyarısı

⚠️ **ÖNEMLİ**: Bu bir simülasyon/eğitim projesidir!

- Gerçek üretim ortamında KULLANMAYIN
- Sadece test ve öğrenme amaçlıdır
- Güvenlik açıklarını kasıtlı olarak simüle eder
- İzole test ortamında çalıştırın

### 📚 Ek Kaynaklar

- **MEMORYBANK.md** - MemoryBank detaylı API dokümantasyonu
- **OCPP 1.6 Spesifikasyonu** - [openchargealliance.org](https://www.openchargealliance.org/protocols/ocpp-16/)
- **Python-CAN Dokümantasyonu** - [python-can.readthedocs.io](https://python-can.readthedocs.io/)

### 🤝 Katkıda Bulunma

Bu eksiksiz, bağımsız bir simülasyondur. İhtiyaçlarınıza göre değiştirebilirsiniz.

### 📝 Lisans

Bu bir simülasyon/eğitim projesidir. Öğrenme ve test amaçları için özgürce kullanılabilir.

### ⚠️ Feragatname

Bu, test ve gösterim amaçlı bir **simülasyondur**. Gerçek EV şarj altyapısının davranışını taklit eder ancak uygun adaptasyon ve güvenlik önlemleri olmadan üretim ortamlarında kullanılmamalıdır.

---

**Made with ⚡ for EV charging anomaly research**

**⚡ ile EV şarj anomali araştırması için yapıldı**
