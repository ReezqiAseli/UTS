# UTS Sistem Terdistribusi

Layanan aggregator berbasis Python (FastAPI + asyncio) yang dirancang untuk menangani pengiriman event dengan volume tinggi, memastikan idempotency melalui deduplikasi data, dan menjamin persistensi data meskipun terjadi kegagalan sistem (crash).

## Fitur Utama

- **Asynchronous Processing**: Menggunakan `asyncio.Queue` untuk memisahkan proses penerimaan HTTP request dengan penulisan ke database.
- **Idempotency & Deduplication**: Mencegah pemrosesan ulang event yang sama menggunakan (Composite Primary Key) pada SQLite.
- **Fault Tolerance**: Data tetap aman dan deduplikasi tetap berjalan setelah restart container berkat volume persistensi.
- **Automated Simulation**: Terintegrasi dengan service publisher yang mengirimkan >5.000 event secara otomatis.

## Link Demonstrasi
https://youtu.be/CVQJ6T--_P0?si=yuNXoY1bQEMXCa9q

## Cara Run

## 1. Menggunakan Docker Compose
docker-compose up --build
## 2. Jika mau reset databasenya (optional)
docker-compose down -v
## 3. Buka SwaggerUI
http://localhost:8080/docs
## 4. Cek Stats
http://localhost:8080/stats
## 5. Cek Data Event
http://localhost:8080/events?topic=user_clicks



