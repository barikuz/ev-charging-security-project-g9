# 🤖 AI Anomaly Detection System - Quick Start Guide

## 📋 3 ADIMDA AI SİSTEMİNİ ÇALIŞTIRIN

### 🎯 ADIM 1: Veri Toplama (60 saniye)
```bash
# Simülasyonu başlat
./run_all.sh

# YENİ bir terminal aç ve veri topla
cd /Users/enisuzun/Desktop/230541106_EnisUZUN
source venv/bin/activate
python data_collector.py
```

**Ne olacak:**
- 60 saniye boyunca şarj verisi toplanır
- `training_data.csv` dosyası oluşturulur
- Normal ve anomali örnekleri etiketlenir

---

### 🧠 ADIM 2: Model Eğitimi (10 saniye)
```bash
python train_model.py
```

**Ne olacak:**
- Random Forest modeli eğitilir
- Model doğruluğu gösterilir (genellikle %90+)
- `anomaly_model.pkl` dosyası kaydedilir
- `model_report.txt` raporu oluşturulur

---

### 🚀 ADIM 3: AI Sistemini Başlat
```bash
# Eski simülasyonu durdur (Ctrl+C)
# Sonra AI sistemini başlat:
./run_ai.sh
```

**Ne olacak:**
- 3 Terminal tab açılır:
  1. **Charging Simulator** → Anomali üretir
  2. **AI Detector** → Gerçek zamanlı tahmin yapar
  3. **AI-Enhanced Graph** → Tahminleri gösterir

---

## 📊 GRAFİKTE GÖRECEKLER

### Renkler:
- 🔵 **Mavi çizgi** → Gerçek current değeri
- 🔴 **Kırmızı nokta** → AI "anomali" dedi
- 🟢 **Yeşil arka plan** → AI "normal" dedi
- 🔴 **Kırmızı arka plan** → AI "anomali" dedi

### Bilgiler:
- Sağ üst köşe: Anlık durum + AI güven skoru
- Sol alt köşe: Anomali oranı istatistiği

---

## 🎯 MODEL PERFORMANSI

Eğitim sonrası göreceğiniz metrikler:

```
🎯 Accuracy: 94.2%
📊 Precision: 92.5%
📊 Recall: 96.8%
```

**Anlamları:**
- **Accuracy**: Genel doğruluk oranı
- **Precision**: AI "anomali" dediğinde ne kadar doğru
- **Recall**: Gerçek anomalilerin ne kadarını yakaladı

---

## 🔧 SORUN GİDERME

### "Model not found" hatası:
```bash
# Önce veri topla, sonra eğit:
python data_collector.py  # 60 saniye bekle
python train_model.py
```

### "CSV not found" hatası:
```bash
# Simülasyon çalışıyor mu kontrol et:
cat /tmp/ev_current.json

# Yoksa simülasyonu başlat:
./run_all.sh
```

### ML kütüphaneleri eksik:
```bash
source venv/bin/activate
pip install -r requirements_ml.txt
```

---

## 📁 OLUŞTURULAN DOSYALAR

| Dosya | Açıklama |
|-------|----------|
| `training_data.csv` | Toplanan eğitim verisi |
| `anomaly_model.pkl` | Eğitilmiş ML model |
| `scaler.pkl` | Veri normalizasyon objesi |
| `model_report.txt` | Model performans raporu |
| `/tmp/ev_predictions.json` | Gerçek zamanlı tahminler |

---

## 🎓 MODEL HAK

KINDA

**Kullanılan Algoritma:** Random Forest Classifier

**Özellikler (Features):**
1. Anlık current değeri
2. Current değişim hızı
3. 5 noktalık hareketli ortalama
4. 10 noktalık hareketli ortalama
5. Standart sapma
6. Son 10 nokta max değer
7. Son 10 nokta min değer
8. Son 10 nokta değer aralığı

**Etiketleme Mantığı:**
- Anomali = Hızlı değişimler (>5A/0.1s)
- Anomali = Yüksek varyans (std>3A)
- Anomali = Geniş aralık (range>10A)
- Normal = Sabit veya yavaş değişim

---

## 💡 İPUÇLARI

1. **Daha iyi sonuçlar için:**
   - Veri toplarken en az 2-3 tam döngü bekleyin
   - Farklı anomali patternleri oluşturun

2. **Modeli yeniden eğitmek için:**
   ```bash
   rm training_data.csv anomaly_model.pkl
   python data_collector.py
   python train_model.py
   ```

3. **Gerçek zamanlı istatistikleri görmek için:**
   ```bash
   # AI Detector terminalinde Ctrl+C yapın
   # İstatistikleri göreceksiniz
   ```

---

## 🎉 BAŞARILAR!

Artık kendi AI anomaly detection sisteminiz var!

**Sorular için:** README.md dosyasına bakın
**Kodları incelemek için:** Tüm dosyalar açık kaynak
