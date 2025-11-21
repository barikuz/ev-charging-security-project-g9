# Termal Anomali Saldırısı (Thermal Anomaly Attack)

Bu belge, simülasyona eklenen **Termal Anomali (Thermal Runaway)** saldırı senaryosunu ve elde edilen sonuçları açıklar.

## 1. Saldırı Nedir? (What is the Attack?)

Bu saldırı senaryosu, elektrikli araç (EV) şarj konektöründe **fiziksel bir kusuru** veya **kötü niyetli bir müdahaleyi** simüle eder.

*   **Senaryo:** Şarj konektörünün temas noktalarında (pinlerde) yüksek direnç oluşması.
*   **Neden:** Korozyon, gevşek bağlantı veya saldırganın konektöre iletkenliği düşük (örneğin demir/iron) bir malzeme yerleştirmesi.
*   **Etki:** Akım geçerken oluşan yüksek direnç, **aşırı ısınmaya (Joule Heating)** neden olur.
    *   Normal Bakır (Copper) Direnci: `0.00005 Ohm` (Çok az ısınır)
    *   Saldırı (Demir/Iron) Direnci: `0.0035 Ohm` (Hızlı ısınır)

Simülatör, bu ısınmayı fiziksel formüllerle hesaplar ve sıcaklık **100°C**'yi geçerse güvenlik önlemi olarak şarjı durdurur.

## 2. Nasıl Çalıştırılır? (How to Run)

Testi çalıştırmak için aşağıdaki komutu kullanın:

```powershell
python tests/test_thermal_anomaly.py
```

Bu komut:
1.  Simülatörü başlatır.
2.  **"THERMAL_RUNAWAY"** saldırısını enjekte eder (Direnci artırır).
3.  60 saniyelik bir şarj oturumu gerçekleştirir.
4.  Sonuçları ekrana ve `thermal_anomaly_test.log` dosyasına yazar.

## 3. Sonuçların Açıklaması (Results Explanation)

60 saniyelik kısa bir test sonucunda elde edilen veriler şöyledir:

```json
"anomaly_counts": {"thermal_runaway": 2}
```
*   **Anlamı:** Saldırı başarıyla sisteme enjekte edildi. Simülatör "Demir" moduna geçti.

```json
"elapsed_time": 62.5
"messages": { ... }
```
*   **Anlamı:** Şarj işlemi kesintisiz devam etti.

### Neden Şarj Durmadı? (Why didn't it stop?)
Mevcut simülasyon parametrelerinde (`0.0035 Ohm` direnç ve `32 Amper` akım), 60 saniye içinde sıcaklık tehlikeli seviyeye (100°C) ulaşmadı. Isınma gerçekleşti ancak yavaş oldu.

*   **Başarılı Saldırı:** Saldırı kodu çalıştı ve fiziksel koşulları değiştirdi.
*   **Güvenlik İhlali:** Henüz gerçekleşmedi (Süre kısa veya direnç yeterince yüksek değil).

Daha uzun süreli testlerde veya daha yüksek direnç değerlerinde sistemin **"CRITICAL TEMPERATURE"** hatası verip kapandığını görebilirsiniz.
