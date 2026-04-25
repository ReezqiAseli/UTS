import sqlite3
import asyncio
import os

DB_PATH = os.getenv("DB_PATH", "data/aggregator.db")

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    # Composite Primary Key untuk idempotency
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_events (
            topic TEXT,
            event_id TEXT,
            timestamp TEXT,
            source TEXT,
            payload TEXT,
            PRIMARY KEY (topic, event_id)
        )
    ''')
    conn.commit()
    conn.close()

def save_event_sync(event_dict: dict) -> bool:
    """Mengembalikan True jika berhasil disimpan (unik), False jika duplikat."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''INSERT INTO processed_events (topic, event_id, timestamp, source, payload) 
               VALUES (?, ?, ?, ?, ?)''',
            (event_dict['topic'], event_dict['event_id'], 
             str(event_dict['timestamp']), event_dict['source'], str(event_dict['payload']))
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Constraint PRIMARY KEY gagal -> Duplikat
        return False
    finally:
        conn.close()

async def save_event(event_dict: dict) -> bool:
    # Menjalankan IO blocking SQLite di thread terpisah
    return await asyncio.to_thread(save_event_sync, event_dict)

def get_stats_sync():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM processed_events')
    unique_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT DISTINCT topic FROM processed_events')
    topics = [row[0] for row in cursor.fetchall()]
    conn.close()
    return unique_count, topics

async def get_db_stats():
    return await asyncio.to_thread(get_stats_sync)

def get_events_sync(topic: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT event_id, timestamp, source, payload FROM processed_events WHERE topic = ?', (topic,))
    rows = cursor.fetchall()
    conn.close()
    return [{"event_id": r[0], "timestamp": r[1], "source": r[2], "payload": r[3]} for r in rows]

async def get_events_by_topic(topic: str):
    return await asyncio.to_thread(get_events_sync, topic)