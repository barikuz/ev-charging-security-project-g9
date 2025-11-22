# OCPP Mesaj Sırası Bozulması Anomali Testi

- Anomali: StartTransaction, MeterValues, StopTransaction mesajlarının sırasının bozulması.
- Amaç: Mesaj sırası hatalarını (erken Stop, çift Start, tx id eksikliği vb.) tespit etmek.
- Dosyalar:
  - `client.py`: EmuOCPP ile senaryo üretip sonuçları `results.csv`'ye yazar.
  - `results.csv`: Simülasyon sonrası üretilen test sonuçları.
- Nasıl Çalıştırılır:
  1. EmuOCPP ortamı ayağa kaldırılır.
  2. `client.py` çalıştırılır.
  3. Oluşan `results.csv` üzerinde mesaj sırası/erken Stop gibi anomaliler analiz edilir.

