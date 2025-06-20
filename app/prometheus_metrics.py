import time
from typing import List
import asyncio
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter, Histogram, Gauge

_ERRORS_COUNTER = Counter("ab_util_reviews_errors_total", 
                          "Общее количество ошибок")
_FAILED_PIPELINES_COUNTER = Counter("ab_util_reviews_failed_pipelines", 
                                    "Общее количество неудачных пайплайнов")
_ACTIVE_THREADS = Gauge("ab_util_reviews_active_threads", 
                        "Количество активных потоков")
_MESSAGES_COUNTER = Counter("ab_util_reviews_received_messages_total", 
                            "Общее количество обработанных сообщений")
_CLASSIFIED_MESSAGES_COUNTER = Counter("ab_util_reviews_classified_messages_total", 
                                       "Общее количество сообщений по классам", 
                                       ["class"])
_PIPELINE_LATENCY = Histogram("ab_util_reviews_pipeline_latency_seconds", 
                              "Время обработки одного сообщения", 
                              buckets=[1, 2.5, 5, 7.5, 10, 15, 20, 25, 30])

stuff_lock = asyncio.Lock()

async def update_total_errors() -> None:
    """Update the error counter"""
    async with stuff_lock:
        _ERRORS_COUNTER.inc()

async def update_pipeline_errors() -> None:
    """Update the pipeline error counter"""
    async with stuff_lock:
        _FAILED_PIPELINES_COUNTER.inc()

async def update_resource_metrics(semaphore: asyncio.Semaphore,
                                  total_threads: int) -> None:
    """Update resource utilization metrics"""
    async with stuff_lock:
        active_threads = total_threads - semaphore._value
        _ACTIVE_THREADS.set(active_threads)

async def update_service_metrics(messages: List[dict] | None,
                                 latency: float | None) -> None:
    """Update message processing metrics"""
    async with stuff_lock:
        if messages:
            _MESSAGES_COUNTER.inc(len(messages))
            for message in messages:
                class_name = message.get("label") or message.get("pred_label") or "unknown"
                _CLASSIFIED_MESSAGES_COUNTER.labels(class_name).inc()
        if latency is not None:
            _PIPELINE_LATENCY.observe(latency)