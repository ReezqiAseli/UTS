import asyncio
import httpx
import uuid
import random
from datetime import datetime, timezone

# URL mengarah ke nama service Docker
API_URL = "http://aggregator:8080/publish"

async def main():
    print("Mulai simulasi pengiriman event...")
    events = []
    topics = ["user_clicks", "transactions", "system_metrics"]
    
    # Generate 4000 event unik
    for _ in range(4000):
        events.append({
            "topic": random.choice(topics),
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "simulated_publisher",
            "payload": {"value": random.randint(1, 100)}
        })
        
    # Generate 1200 duplikat dari event yang sudah ada
    duplicates = random.choices(events, k=1200)
    events.extend(duplicates)
    
    # Acak urutan pengiriman
    random.shuffle(events)
    
    print(f"Total event disiapkan: {len(events)}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Kirim dalam bentuk batch 100 events
        for i in range(0, len(events), 100):
            batch = events[i:i+100]
            try:
                response = await client.post(API_URL, json=batch)
                print(f"Batch {i//100 + 1} terkirim: {response.status_code}")
            except Exception as e:
                print(f"Error mengirim batch {i//100 + 1}: {e}")
            
    print("Pengiriman selesai.")

if __name__ == "__main__":
    # Delay dikit biar service aggregator siap menerima request
    import time
    time.sleep(3)
    asyncio.run(main())