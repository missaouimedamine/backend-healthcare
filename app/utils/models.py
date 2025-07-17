from pydantic import BaseModel
from typing import Optional

class SymptomAnalysisRequest(BaseModel):
    symptoms: str
    language: Optional[str] = "en"
    detailed: Optional[bool] = False

# Pydantic model: only the diagnoses dictionary
class AnalysisResult(BaseModel):
    diagnoses: dict  # disease -> confidence (0.0 to 1.0)

class DiseaseInfo(BaseModel):
    infos: dict

class DiseaseInput(BaseModel):
    disease_name: str
    language: Optional[str] = "en"

class ChatRequest(BaseModel):
    question: str