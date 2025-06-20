import logging

from app.models import ReviewInput, AnswerOutput
from fastapi import FastAPI, HTTPException

app = FastAPI()
logger = logging.getLogger(__name__)

@app.post("/respond")
async def respond(review: ReviewInput):
    try:
        logger.info(f"Получен отзыв: {review.model_dump()}")
        logger.info(f"Отзыв: {review}")
        
        response = AnswerOutput(
            response=review.text,
            metadata={
                "review": {
                    "id": review.id,
                    "wbUserId": review.wbUserId,
                    "userName": getattr(review.wbUserDetails, 'name', None),
                    "nmId": review.nmId,
                    "review": review.text,
                    "rating": review.ProductValuation or 4,
                    "recommendations": review.recommendations
                }
            }
        )
        return response
    except Exception as e:
        logger.error(f"Ошибка при обработке отзыва: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")