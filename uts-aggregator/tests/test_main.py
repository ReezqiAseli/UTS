import os

os.environ["DB_PATH"] = "data/test_aggregator.db"

import pytest
import asyncio
import sqlite3
import time
import uuid
from fastapi.testclient import TestClient

from src.main import app, AppState
from src.database import init_db, DB_PATH

@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    
    # Hapus seluruh data di dalam tabel
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM processed_events")
    conn.commit()
    conn.close()
    
    # Reset in memory state
    AppState.received = 0
    AppState.duplicate_dropped = 0
    
    # Kosongkan queue jika ada
    if hasattr(AppState.queue, '_queue') and AppState.queue is not None:
        AppState.queue._queue.clear()
        
    yield

# TEST 1: Validasi Skema Valid
def test_publish_valid_schema():
    with TestClient(app) as client:
        payload = {
            "topic": "test_topic",
            "event_id": "999",
            "timestamp": "2026-04-24T10:00:00Z",
            "source": "pytest",
            "payload": {"key": "value"}
        }
        response = client.post("/publish", json=payload)
        assert response.status_code == 200
        assert response.json()["queued"] == 1

# TEST 2: Validasi Skema Tidak Valid
def test_invalid_schema():
    client = TestClient(app)
    payload = {"topic": "test"}
    response = client.post("/publish", json=payload)
    assert response.status_code == 422

# TEST 3: Deduplikasi Aktif ---
@pytest.mark.asyncio
async def test_deduplication():
    with TestClient(app) as client:
        payload = {
            "topic": "test_topic",
            "event_id": "123",
            "timestamp": "2026-04-24T10:00:00Z",
            "source": "pytest",
            "payload": {}
        }
        # Kirim 3x event yang sama
        client.post("/publish", json=payload)
        client.post("/publish", json=payload)
        client.post("/publish", json=payload)
        
        await asyncio.sleep(0.5) # Tunggu Consumer
        
        res_events = client.get("/events?topic=test_topic")
        assert len(res_events.json()["events"]) == 1
        
        stats = client.get("/stats").json()
        assert stats["received"] == 3
        assert stats["unique_processed"] == 1
        assert stats["duplicate_dropped"] == 2

# TEST 4: Persistensi & Restart Simulation
@pytest.mark.asyncio
async def test_persistence_after_restart():
    payload = {
        "topic": "restart_topic",
        "event_id": "persist_1",
        "timestamp": "2026-04-24T10:00:00Z",
        "source": "pytest",
        "payload": {}
    }
    
    # Sebelum Restart
    with TestClient(app) as client:
        client.post("/publish", json=payload)
        await asyncio.sleep(0.2)
        
    # SIMULASI CONTAINER RESTART
    # Memori RAM terhapus, tapi DB SQLite tetap ada
    AppState.received = 0
    AppState.duplicate_dropped = 0
    
    # Setelah Restart
    with TestClient(app) as client:
        client.post("/publish", json=payload) # Mengirim duplikat dari data sebelum restart
        await asyncio.sleep(0.2)
        
        stats = client.get("/stats").json()

        assert stats["unique_processed"] == 1
        assert stats["duplicate_dropped"] == 1

# TEST 5: Konsistensi GET /events & /stats
@pytest.mark.asyncio
async def test_get_events_and_stats_consistency():
    events_batch = [
        {"topic": "topic_A", "event_id": "A1", "timestamp": "2026-04-24T10:00:00Z", "source": "test", "payload": {}},
        {"topic": "topic_A", "event_id": "A2", "timestamp": "2026-04-24T10:00:00Z", "source": "test", "payload": {}},
        {"topic": "topic_B", "event_id": "B1", "timestamp": "2026-04-24T10:00:00Z", "source": "test", "payload": {}}
    ]
    
    with TestClient(app) as client:
        client.post("/publish", json=events_batch)
        await asyncio.sleep(0.5)
        
        # Validasi /stats
        stats = client.get("/stats").json()
        assert stats["received"] == 3
        assert stats["unique_processed"] == 3
        assert "topic_A" in stats["topics"]
        assert "topic_B" in stats["topics"]
        
        # Validasi /events filtering
        res_a = client.get("/events?topic=topic_A").json()
        assert len(res_a["events"]) == 2
        
        res_b = client.get("/events?topic=topic_B").json()
        assert len(res_b["events"]) == 1

# TEST 6: Stress Kecil (Waktu Eksekusi)
@pytest.mark.asyncio
async def test_stress_small_batch():
    # Siapkan 100 event
    batch = []
    for i in range(100):
        batch.append({
            "topic": "stress_topic",
            "event_id": str(uuid.uuid4()),
            "timestamp": "2026-04-24T10:00:00Z",
            "source": "test",
            "payload": {"index": i}
        })
        
    with TestClient(app) as client:
        # waktu penerimaan API
        start_time = time.time()
        res = client.post("/publish", json=batch)
        exec_time = time.time() - start_time
        
        assert res.status_code == 200
        assert res.json()["queued"] == 100

        assert exec_time < 0.5 
        
        # Tunggu background worker menyelesaikan 100 insert ke SQLite
        await asyncio.sleep(1.0)
        stats = client.get("/stats").json()
        assert stats["unique_processed"] == 100