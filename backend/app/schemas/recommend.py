from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


class RecommendationRequest(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=200)
    age: int = Field(..., ge=1, le=99)
    city_tier: str = Field(..., min_length=1)
    lifestyle: str = Field(..., min_length=1)
    pre_existing_conditions: List[str] = []
    income_band: str = Field(..., min_length=1)

    @field_validator("full_name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Full name cannot be blank")
        return v.strip()


class BestFit(BaseModel):
    policy_name: str
    insurer: str
    premium: str
    cover_amount: str


class PeerComparison(BaseModel):
    policy_name: str
    insurer: str
    premium: str
    cover_amount: str
    waiting_period: str
    key_benefit: str
    suitability_score: int


class CoverageDetail(BaseModel):
    inclusions: List[str]
    exclusions: List[str]
    sub_limits: str
    co_pay: str
    claim_type: str


class RecommendationResponse(BaseModel):
    best_fit: Optional[BestFit] = None
    peer_comparison: List[PeerComparison] = []
    coverage_detail: Optional[CoverageDetail] = None
    why_this_policy: str
    citations: List[str] = []
