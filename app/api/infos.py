
from app.utils.pdf_process import generate_pdf_report
from app.utils.infos_process import extract_dict_from_text
from app.utils.models import DiseaseInfo, DiseaseInput

from fastapi import APIRouter, HTTPException, Request
router = APIRouter()

def get_disease_info(request: Request,disease_name: str) -> DiseaseInfo:
    dict_str = request.app.state.info_chain.run(disease_name)
    disease_info = extract_dict_from_text(dict_str)
    return DiseaseInfo(infos=disease_info)




@router.post("/infos", response_model=DiseaseInfo)
async def give_full_infos(request: Request,requests: DiseaseInput):
    if not requests.disease_name:
        raise HTTPException(
            status_code=400,
            detail="At least one symptom is required"
        )
    disease_info=get_disease_info(request,requests.disease_name)
    filename = f"app/report/report.pdf"
    generate_pdf_report(disease_info.infos, filename)
    return disease_info
