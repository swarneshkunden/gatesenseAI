import logging
from fastapi import APIRouter, Depends, HTTPException
from schemas import TranslationRequest, ScriptRequest
from rate_limiter import rate_limit_default
from gemini_service import GeminiService

logger = logging.getLogger("gatesenseAI.routes.translation")
router = APIRouter(prefix="/api/translation", tags=["Multilingual Assistance"])


@router.post("/translate", dependencies=[Depends(rate_limit_default)])
async def translate_query(req: TranslationRequest):
    """
    Translates a fan's verbal/text query into English, evaluates urgency/stress,
    and returns a context-sensitive volunteer response translated back to their language.
    """
    logger.info(f"Received translation request. Stress level: {req.stress_level}, Urgency: {req.urgency_level}")
    try:
        result = GeminiService.translate_query(
            text=req.text,
            fan_lang=req.fan_language,
            fan_origin=req.fan_origin,
            urgency=req.urgency_level,
            stress=req.stress_level
        )
        return {"status": "success", "result": result}
    except Exception as exc:
        logger.error(f"Translation failure: {str(exc)}")
        raise HTTPException(status_code=503, detail=str(exc))


@router.post("/broadcast-script", dependencies=[Depends(rate_limit_default)])
async def generate_broadcast_script(req: ScriptRequest):
    """
    Generates a megaphone announcement script in multiple languages for volunteers
    to read out loud during specific scenarios.
    """
    logger.info(f"Generating broadcast script for gates: {req.target_gates} in languages: {req.languages}")
    result = GeminiService.generate_broadcast(
        scenario=req.scenario,
        target_gates=req.target_gates,
        languages=req.languages
    )
    return {"status": "success", "result": result}
