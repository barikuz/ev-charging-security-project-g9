🔒 İmzalı MeterValues Replay & Timestamp Manipülasyonu Senaryosu

Bu bölümde, şarj istasyonu ile CSMS arasındaki MeterValues trafiğinde iki kritik saldırı türü simüle edilir:

Replay Attack: Saldırgan, daha önce yakaladığı imzalı paketi tekrar gönderir.

Timestamp Manipulation: Saldırgan, paketin zaman damgasını değiştirerek veri bütünlüğünü bozar.

Simülasyon; istasyonun ürettiği imzalı enerji paketlerini, saldırganın müdahalelerini ve CSMS’nin bu paketleri nasıl doğrulayıp engellediğini gösterir.
CSMS, her pakette zaman sırası, enerji artışı ve imza tekrarı kontrolleri yaparak anormallikleri tespit eder. Saldırı durumlarında olaylar güvenlik monitörüne kaydedilir ve işlem reddedilir.

Simülasyon sonunda tüm olaylar ve tespit edilen saldırılar security_report.json dosyasına kaydedilir.
