# V2G Botnet Attack Simulation Framework

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Profesyonel simülasyon çerçevesi: V2G (Vehicle-to-Grid) altyapısına yönelik botnet saldırılarının OCPP protokolü üzerinden analizi.

## 📋 İçindekiler

- [Özellikler](#özellikler)
- [Kurulum](#kurulum)
- [Kullanım](#kullanım)
- [Konfigürasyon](#konfigürasyon)
- [Çıktılar](#çıktılar)
- [Örnekler](#örnekler)
- [Teknik Detaylar](#teknik-detaylar)

## ✨ Özellikler

### Temel Yetenekler
- ✅ **OCPP Protokol Simülasyonu**: RemoteStartTransaction ve RemoteStopTransaction komutları
- ✅ **Gerçekçi Güç Dinamikleri**: Ramp-rate sınırlı güç değişimleri
- ✅ **Komut Dağılım Kontrolü**: Senkron veya jitter'lı saldırı senaryoları
- ✅ **Ölçüm Gürültüsü**: Opsiyonel Gaussian gürültü ekleme
- ✅ **Kapsamlı Loglama**: Detaylı olay kayıtları ve sistem durumu takibi

### Analiz ve Raporlama
- 📊 **Otomatik Görselleştirme**: 3 farklı grafik türü (toplam yük, istasyon profilleri, EV katkısı)
- 📈 **İstatistiksel Metrikler**: Ortalama, standart sapma, min/max değerler
- 📄 **Detaylı Raporlar**: Metin tabanlı simülasyon özeti
- 💾 **Veri Dışa Aktarma**: JSON formatında yapılandırılmış veri

### Profesyonel Özellikler
- 🔧 **CLI Desteği**: Komut satırı argümanları ile esnek kullanım
- ⚙️ **Konfigürasyon Dosyası**: JSON tabanlı parametre yönetimi
- 🛡️ **Hata Yönetimi**: Kapsamlı validasyon ve hata yakalama
- 📝 **Dokümantasyon**: Detaylı kod ve kullanıcı dokümantasyonu

## 🚀 Kurulum

### Gereksinimler
- Python 3.8 veya üzeri
- pip paket yöneticisi

### Adımlar

1. **Depoyu klonlayın veya dosyaları indirin**
```powershell
cd C:\Users\Yusuf\Desktop\v2gsimulasyon
```

2. **Gerekli paketleri yükleyin**
```powershell
pip install numpy matplotlib
```

3. **Kurulumu test edin**
```powershell
python v2g_botnet_sim.py --help
```

## 💻 Kullanım

### Basit Kullanım

Varsayılan parametrelerle simülasyon çalıştırma:
```powershell
python v2g_botnet_sim.py
```

### Gelişmiş Kullanım

#### Komut Satırı Argümanları ile
```powershell
python v2g_botnet_sim.py --T-max 200 --n-stations 20 --attack-time 120 --verbose
```

#### Konfigürasyon Dosyası ile
```powershell
python v2g_botnet_sim.py --config config_scenario1.json --output-dir results_scenario1
```

### CLI Parametreleri

| Parametre | Açıklama | Varsayılan |
|-----------|----------|------------|
| `--config` | Konfigürasyon JSON dosyası yolu | None |
| `--output-dir` | Çıktı klasörü | `simulation_output` |
| `--T-max` | Toplam simülasyon süresi (s) | 100 |
| `--n-stations` | İstasyon sayısı | 10 |
| `--attack-time` | Saldırı zamanı (s) | 60 |
| `--jitter-window` | Komut jitter penceresi (s) | 0 |
| `--noise-std` | Güç gürültüsü std sapma (kW) | 0.0 |
| `--seed` | Random seed | 42 |
| `--verbose` | Detaylı loglama | False |

## ⚙️ Konfigürasyon

### Konfigürasyon Dosyası Örneği (`config.json`)

```json
{
  "T_max": 150,
  "dt": 1,
  "base_load_kw": 500.0,
  "n_stations": 15,
  "attack_time_s": 75,
  "initial_discharge_kw": -10.0,
  "attack_charge_kw": 20.0,
  "ramp_rate_kw_per_s": 10.0,
  "jitter_window_s": 5,
  "noise_std_kw": 0.5,
  "seed": 42
}
```

### Parametre Açıklamaları

- **T_max**: Toplam simülasyon süresi (saniye)
- **dt**: Zaman adımı boyutu (saniye)
- **base_load_kw**: EV dışı şebeke baz yükü (kW)
- **n_stations**: Toplam şarj istasyonu sayısı
- **attack_time_s**: Saldırının tetiklenme zamanı (saniye)
- **initial_discharge_kw**: İlk 5 istasyon için V2G deşarj gücü (kW, negatif değer)
- **attack_charge_kw**: Son 5 istasyon için saldırı sonrası şarj gücü (kW)
- **ramp_rate_kw_per_s**: Maksimum güç değişim hızı (kW/saniye)
- **jitter_window_s**: Komut dağılım penceresi (0 = senkron)
- **noise_std_kw**: Ölçüm gürültüsü standart sapması (kW)
- **seed**: Rastgele sayı üreteci tohumu (tekrarlanabilirlik için)

## 📊 Çıktılar

Simülasyon aşağıdaki dosyaları `output-dir` klasöründe oluşturur:

### 1. Grafikler
- **`v2g_attack_load.png`**: Toplam şebeke yükünün zamana göre değişimi
- **`v2g_attack_station_powers.png`**: Tüm istasyonların güç profilleri (2 panel)
- **`v2g_attack_ev_contribution.png`**: Net EV katkısının şebeke yüküne etkisi

### 2. Veri Dosyaları
- **`simulation_config.json`**: Kullanılan konfigürasyon parametreleri
- **`simulation_data.json`**: Zaman serisi verileri (tüm istasyonlar + toplam yük)

### 3. Raporlar
- **`simulation_report.txt`**: Detaylı metin raporu (metrikler, istatistikler, özet)

### Örnek Rapor Çıktısı
```
======================================================================
V2G BOTNET ATTACK SIMULATION REPORT
======================================================================
Generated: 2025-11-12 14:30:45

CONFIGURATION
----------------------------------------------------------------------
  Simulation duration:        100 seconds
  Time step:                  1 seconds
  Number of stations:         10
  Attack time:                60 seconds
  Base grid load:             500.0 kW
  Initial discharge power:    -10.0 kW
  Attack charge power:        20.0 kW
  Ramp rate:                  10.0 kW/s
  Command jitter window:      0 seconds
  Noise std deviation:        0.0 kW

ATTACK IMPACT METRICS
----------------------------------------------------------------------
  Baseline load (pre-attack):      450.0 kW
  Expected post-attack load:       600.0 kW
  Peak load observed:              600.0 kW
  Peak time:                       64 seconds
  Load swing:                      150.0 kW
  Swing percentage:                33.3 %
```

## 🎯 Örnekler

### Örnek 1: Temel Saldırı Senaryosu
```powershell
python v2g_botnet_sim.py
```

### Örnek 2: Jitter'lı (Dağıtılmış) Saldırı
```powershell
python v2g_botnet_sim.py --jitter-window 10 --output-dir results_jittered
```

### Örnek 3: Gürültülü Ortam Simülasyonu
```powershell
python v2g_botnet_sim.py --noise-std 1.0 --seed 123 --verbose
```

### Örnek 4: Büyük Ölçekli Senaryo
```powershell
python v2g_botnet_sim.py --T-max 300 --n-stations 50 --attack-time 150
```

## 🔬 Teknik Detaylar

### Simülasyon Mimarisi

```
SimConfig → V2GBotnetSim → Stations (1..N)
     ↓              ↓              ↓
Validation    Event System    Power Dynamics
     ↓              ↓              ↓
     └──────→ Time Loop ←─────────┘
                  ↓
        Data Collection & Analysis
                  ↓
        Visualization & Reporting
```

### Saldırı Mekanizması

1. **Başlangıç Durumu (t < 60s)**
   - İstasyon 1-5: V2G deşarj modu (-10 kW)
   - İstasyon 6-10: Beklemede (0 kW)
   - Toplam yük: ~450 kW

2. **Saldırı Anı (t = 60s)**
   - OCPP RemoteStopTransaction → İstasyon 1-5 (hedef: 0 kW)
   - OCPP RemoteStartTransaction → İstasyon 6-10 (hedef: +20 kW)

3. **Saldırı Sonrası (t > 60s)**
   - İstasyon 1-5: Ramp-down ile 0 kW'a geçiş
   - İstasyon 6-10: Ramp-up ile 20 kW'a geçiş
   - Toplam yük: ~600 kW (%33 artış)

### Güç Dinamikleri

Ramp-rate sınırlı güç değişimi:
```
P(t+dt) = P(t) + clip(P_target - P(t), -R*dt, +R*dt) + N(0, σ²)
```

Burada:
- `P(t)`: Anık güç
- `P_target`: Hedef güç
- `R`: Ramp oranı (kW/s)
- `dt`: Zaman adımı
- `N(0, σ²)`: Gaussian gürültü

## 📝 Lisans

MIT License - Araştırma ve eğitim amaçlı kullanım için açık kaynaklıdır.

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/YeniOzellik`)
3. Değişikliklerinizi commit edin (`git commit -m 'Yeni özellik eklendi'`)
4. Branch'i push edin (`git push origin feature/YeniOzellik`)
5. Pull Request oluşturun

## 📧 İletişim

Sorular ve öneriler için issue açabilirsiniz.

---

**Not**: Bu simülasyon araştırma amaçlıdır. Gerçek sistemlerde test etmeden önce uygun izinleri alınız.
