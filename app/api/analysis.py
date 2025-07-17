from fastapi import APIRouter, HTTPException,Request
import json

from app.utils.models import AnalysisResult, SymptomAnalysisRequest
from typing import Union

import re

router = APIRouter()



def process_rag_response(rag_response: Union[str, None]) -> AnalysisResult:
    if not rag_response or not rag_response.strip():
        raise ValueError("Empty response from RAG model")

    # Extract JSON array from any extra text
    match = re.search(r'\[\s*\{.*?\}\s*\]', rag_response, re.DOTALL)
    if not match:
        raise ValueError("No valid JSON array found in response")

    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}")

    if not isinstance(data, list) or not data:
        raise ValueError("Parsed JSON is not a valid non-empty list")

    # Build the diagnoses dict
    diagnoses = {
        item.get("disease", "Unknown"): item.get("probability", 0) / 100
        for item in data
    }
    
    return AnalysisResult(diagnoses=diagnoses)



def analyze_symptoms(request: Request, symptoms: str) -> AnalysisResult:
    try:
        rag_response = request.app.state.diagnosis_chain.run(symptoms)
        return process_rag_response(rag_response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Symptom analysis failed: {str(e)}")


@router.post("/analyze", response_model=AnalysisResult)
async def analyze_selected_symptoms(request: Request, body: SymptomAnalysisRequest):
    if not body.symptoms:
        raise HTTPException(status_code=400, detail="At least one symptom is required")
    return analyze_symptoms(request, body.symptoms)


