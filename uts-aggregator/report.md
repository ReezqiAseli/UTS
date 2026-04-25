# Laporan Desain Aggregator Event

## 1. Idempotency & Toleransi Crash
Sistem menggunakan `SQLite` dengan volume persistensi Docker. Dedup dilakukan menggunakan *Composite Primary Key* `(topic, event_id)`. Ketika terjadi *container restart*, database tetap utuh. Saat *publisher* mengirim ulang data yang sama, *constraint* DB akan menolak sisipan, menjamin idempotency absolut dan mencegah data ganda.

## 2. Analisis Total Ordering
**Apakah Total Ordering (Pengurutan Total) dibutuhkan dalam konteks aggregator ini?**
Secara arsitektur umum, *TIDAK*. 
Dalam sistem terdistribusi, mencapai *Total Ordering* di seluruh event dan *topic* membutuhkan *global synchronization*, yang berdampak buruk pada latensi dan skalabilitas.

Untuk layanan aggregator ini, **Partial Ordering / Causal Ordering** (pengurutan per `topic` atau `entity_id` berdasar *timestamp*) sudah cukup. Event-event dari berbagai topik berbeda (misal: `user_clicks` dan `system_metrics`) independen satu sama lain dan tidak membutuhkan relasi urutan waktu.

## 3. Asumsi Desain
- Database SQLite dinilai cukup karena beban in memory queue dapat menangani spikes rate tinggi sebelum masuk disk secara sekuensial.
- *At-least-once delivery* diasumsikan datang dari layanan eksternal, sehingga kerjaan *aggregator* hanya membuang duplikat seefisien mungkin tanpa menginterupsi *pipeline*.