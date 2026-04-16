from typing import List, Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class PredictionResponse(BaseModel):
    analysis_id: int
    label: str
    probabilities: List[float]
    classes: List[str]
    confidence: float
    confidence_gap: float


class ExplanationResponse(BaseModel):
    method: Literal["gradcam", "lime"]
    image_base64: str
    mime_type: str = "image/png"


class AnalysisRecord(BaseModel):
    id: int
    filename: str
    content_type: str
    label: str
    probabilities: List[float]
    classes: List[str]
    confidence: float
    confidence_gap: float
    created_at: str


class AnalysisDetail(AnalysisRecord):
    image_base64: str


class ReportRequest(BaseModel):
    analysis_id: int
    gradcam_base64: str | None = None
    lime_base64: str | None = None

class User(BaseModel):
    id: int
    username: str
    email: str

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User
