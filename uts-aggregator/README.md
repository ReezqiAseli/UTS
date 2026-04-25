# UTS Sistem Terdistribusi

Layanan aggregator berbasis Python (FastAPI + asyncio) yang dirancang untuk menangani pengiriman event dengan volume tinggi, memastikan idempotency melalui deduplikasi data, dan menjamin persistensi data meskipun terjadi kegagalan sistem (crash).

## Fitur Utama

- **Asynchronous Processing**: Menggunakan `asyncio.Queue` untuk memisahkan proses penerimaan HTTP request dengan penulisan ke database.
- **Idempotency & Deduplication**: Mencegah pemrosesan ulang event yang sama menggunakan (Composite Primary Key) pada SQLite.
- **Fault Tolerance**: Data tetap aman dan deduplikasi tetap berjalan setelah restart container berkat volume persistensi.
- **Automated Simulation**: Terintegrasi dengan service publisher yang mengirimkan >5.000 event secara otomatis.
