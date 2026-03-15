from pydantic import BaseModel


class FeedbackRequest(BaseModel):
    worked: bool


class FeedbackResponse(BaseModel):
    message: str
    votes_worked: int
    votes_failed: int
    confidence_score: float
