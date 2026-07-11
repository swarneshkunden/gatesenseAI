from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

class TranslationRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000, description="Fan text to translate")
    fan_language: Optional[str] = Field(default="Auto", max_length=50)
    fan_origin: Optional[str] = Field(default="Unknown", max_length=50)
    urgency_level: str = Field(default="casual", description="urgency: casual, important, urgent, emergency")
    stress_level: str = Field(default="calm", description="stress: calm, anxious, panicked")

    @field_validator('urgency_level')
    @classmethod
    def validate_urgency(cls, v: str) -> str:
        valid = ["casual", "important", "urgent", "emergency"]
        if v.lower() not in valid:
            raise ValueError(f"urgency_level must be one of {valid}")
        return v.lower()

    @field_validator('stress_level')
    @classmethod
    def validate_stress(cls, v: str) -> str:
        valid = ["calm", "anxious", "panicked"]
        if v.lower() not in valid:
            raise ValueError(f"stress_level must be one of {valid}")
        return v.lower()

class ScriptRequest(BaseModel):
    scenario: str = Field(..., min_length=5, max_length=1000, description="The routing or operational instructions context")
    target_gates: List[str] = Field(..., min_length=1, max_length=10)
    languages: List[str] = Field(..., min_length=1, max_length=5)

    @field_validator('target_gates')
    @classmethod
    def validate_gates(cls, v: List[str]) -> List[str]:
        for gate in v:
            if len(gate) > 50:
                raise ValueError("Gate name too long")
        return v

    @field_validator('languages')
    @classmethod
    def validate_languages(cls, v: List[str]) -> List[str]:
        for lang in v:
            if len(lang) > 30:
                raise ValueError("Language name too long")
        return v

class CrowdStateUpdate(BaseModel):
    zone_id: str = Field(..., min_length=1, max_length=50)
    occupancy_rate: float = Field(..., ge=0.0, le=100.0)
    throughput_rate: float = Field(..., ge=0.0, le=10000.0)
