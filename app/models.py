from pydantic import BaseModel, Field
from typing import List, Optional, Union, Dict, Any
from pydantic import validator

class Review(BaseModel):
    id_review: str = Field(..., description="Unique review identifier")
    id_user: str = Field(..., description="User identifier")
    user_name: str = Field(..., description="User name")
    nm_id: Union[int, str] = Field(..., description="Product identifier")
    review: str = Field(..., description="Review text")
    rating: int = Field(..., ge=1, le=5, description="Review rating")
    recommendations: bool = Field(..., description="Recommendations flag")

    @validator('rating')
    def validate_rating(cls, v):
        if not isinstance(v, int) or v < 1 or v > 5:
            return 1
        return v

    @validator('nm_id')
    def validate_nm_id(cls, v):
        if isinstance(v, str):
            try:
                return int(v)
            except (ValueError, TypeError):
                raise ValueError("nm_id must be convertible to integer")
        return v

    @classmethod
    def from_kafka_input(cls, kafka_input: 'KafkaReviewInput') -> Optional['Review']:
        """Convert a KafkaReviewInput to a Review object"""
        review_text = []
        if kafka_input.text:
            review_text.append(kafka_input.text)
        if kafka_input.pros:
            review_text.append(f"Плюсы: {kafka_input.pros}")
        if kafka_input.cons:
            review_text.append(f"Минусы: {kafka_input.cons}")
                
        combined_text = ' '.join(review_text).strip()
        
        if not combined_text:
            return None

        return cls(
            id_review=str(kafka_input.id),
            id_user=str(kafka_input.globalUserId),
            user_name=str(kafka_input.wbUserDetails.name),
            nm_id=int(kafka_input.nmId),
            review=combined_text,
            rating=kafka_input.ProductValuation or 4,
            recommendations=kafka_input.recommendations
        )

class WBUserDetails(BaseModel):
    name: str = Field(..., description="User name from Wildberries")

class NmIdData(BaseModel):
    title: str = Field(default="Unknown", description="Product title")
    category: str = Field(default="Unknown", description="Product category")

class ProcessedReview(BaseModel):
    review: Review = Field(..., description="Original review data")
    product_data: NmIdData = Field(..., description="Product data")

class Recommendations(BaseModel):
    items: Optional[List] = Field(..., description="Products we recommend")
    summary: Optional[str] = Field(..., description="Additional text if there are any recommendations")

class GenerationResponse(BaseModel):
    response: str = Field(..., description="Generated response")
    metadata: ProcessedReview = Field(..., description="Review processing metadata")
    recommendations: Recommendations = Field(..., description="Related products recommendation")

class ReviewGenerationResponse(BaseModel):
    generations: List[GenerationResponse] = Field(..., description="Generated responses for reviews")

class SingleReviewInput(BaseModel):
    id: Union[int, str] = Field(..., description="Review ID")
    globalUserId: Union[int, str] = Field(..., description="Global user ID")
    wbUserId: Union[int, str] = Field(..., description="Wildberries user ID")
    imtId: Union[int, str] = Field(..., description="IMT ID")
    nmId: Union[int, str] = Field(..., description="Product ID")
    wbUserDetails: WBUserDetails = Field(..., description="User details")
    text: Optional[str] = Field(None, description="Main review text")
    pros: Optional[str] = Field(None, description="Positive aspects")
    cons: Optional[str] = Field(None, description="Negative aspects")
    ProductValuation: Optional[int] = Field(None, description="Product rating")

class ReviewResponse(BaseModel):
    id: Union[int, str] = Field(..., description="Review ID")
    nmId: Union[int, str] = Field(..., description="Product ID")
    text: Optional[str] = Field(None, description="Main review text")
    pros: Optional[str] = Field(None, description="Positive aspects")
    cons: Optional[str] = Field(None, description="Negative aspects")
    ProductValuation: Optional[int] = Field(None, description="Product rating")
    response: Optional[str] = Field(None, description="Review answer")

class ReviewInput(BaseModel):
    id: Union[int, str] = Field(..., description="Review ID")
    globalUserId: Union[int, str] = Field(..., description="Global user ID")
    wbUserId: Union[int, str] = Field(..., description="Wildberries user ID")
    imtId: Union[int, str] = Field(..., description="IMT ID")
    nmId: Union[int, str] = Field(..., description="Product ID")
    wbUserDetails: WBUserDetails = Field(..., description="User details")
    text: Optional[str] = Field(None, description="Main review text")
    pros: Optional[str] = Field(None, description="Positive aspects")
    cons: Optional[str] = Field(None, description="Negative aspects")
    ProductValuation: Optional[int] = Field(None, description="Product rating")

class AnswerOutput(BaseModel):
    response: Optional[str] = None
    metadata: Optional[dict] = None

class GenerateResponseRequest(BaseModel):
    reviews: List[ReviewInput] = Field(..., description="List of reviews to process in Kafka message format")

class ReviewGenerationRequest(BaseModel):
    reviews: List[Review] = Field(..., description="List of reviews to process in Kafka message format")