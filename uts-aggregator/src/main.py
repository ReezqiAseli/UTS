import asyncio
import logging
import time
from typing import List, Union
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager

from .models import Event
from . import database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aggregator")

# In memory State
class AppState:
    start_time = time.time()
    received = 0
    duplicate_dropped = 0
    queue = None

# Consumer untuk memproses event dari queue
async def event_worker():
    while True:
        event = await AppState.queue.get()
        
        is_unique = await database.save_event(event.model_dump())
        
        if is_unique:
            logger.info(f"Processed: {event.topic} - {event.event_id}")
        else:
            AppState.duplicate_dropped += 1
            logger.warning(f"DUPLICATE DROPPED: {event.topic} - {event.event_id}")
            
        AppState.queue.task_done()

@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    
    AppState.queue = asyncio.Queue() 
    
    worker_task = asyncio.create_task(event_worker())
    yield
    worker_task.cancel()

app = FastAPI(lifespan=lifespan)

@app.post("/publish")
async def publish_events(events: Union[Event, List[Event]]):
    if isinstance(events, Event):
        events = [events]
        
    for event in events:
        AppState.received += 1
        await AppState.queue.put(event)
        
    return {"status": "accepted", "queued": len(events)}

@app.get("/events")
async def get_events(topic: str):
    events = await database.get_events_by_topic(topic)
    return {"topic": topic, "events": events}

@app.get("/stats")
async def get_stats():
    unique_processed, topics = await database.get_db_stats()
    uptime = time.time() - AppState.start_time
    
    return {
        "received": AppState.received,
        "unique_processed": unique_processed,
        "duplicate_dropped": AppState.duplicate_dropped,
        "topics": topics,
        "uptime_seconds": round(uptime, 2)
    }