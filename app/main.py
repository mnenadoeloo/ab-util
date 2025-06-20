import logging
from typing import List

from fastapi import FastAPI, HTTPException, status
from pydantic import ValidationError
from app.models import GenerateResponseRequest, AnswerOutput, Review, ReviewGenerationRequest, ReviewGenerationResponse, GenerationResponse, ProcessedReview
from starlette.responses import Response, JSONResponse
from app.services import service_router
from app.settings import settings
from .prometheus_metrics import generate_latest, CONTENT_TYPE_LATEST


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="A/B Testing Router",
    description="Балансировщик для A/B-тестирования сервисов",
    version="1.0.0",
)

@app.post("/api/v1/llm/generate-responses", response_model=ReviewGenerationResponse)
async def generate_review_responses(request: GenerateResponseRequest) -> ReviewGenerationResponse:
    if not request.reviews:
        raise HTTPException(
            status_code=400,
            detail="No reviews provided in the request"
        )

    try:
        # Отправляем запрос напрямую, без конвертации
        answer_outputs: List[AnswerOutput] = await service_router.route_request(
            request,
            AnswerOutput
        )

        return ReviewGenerationResponse(generations=answer_outputs)

    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@app.get("/health")
async def health_check():
    """Эндпоинт для проверки работоспособности сервиса"""
    return {"status": "ok"}

@app.get("/config")
async def get_config():
    """Информация о текущей конфигурации"""
    return {
        "mode": settings.mode,
        "services": {
            name: {"url": service.url, "weight": service.weight} 
            for name, service in settings.services.items()
        },
        "timeout": settings.timeout,
        "fallback_enabled": settings.fallback_enabled
    }

@app.get("/metrics")
async def get_metrics():
    """Get service metrics"""
    logger.info("[SERVER] '/metrics'-endpoint is running...")
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
