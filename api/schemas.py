
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class CandidateReportInput(BaseModel):
    model_config = ConfigDict(extra="allow")

    candidate_name: Optional[str] = None
    resume_file: Optional[str] = None
    ats_score: Optional[float] = Field(default=None, ge=0, le=100)
    manual_review_required: bool = False


class ShortlistingThresholds(BaseModel):
    shortlist: float = Field(default=70, ge=0, le=100)
    review: float = Field(default=40, ge=0, le=100)

    @model_validator(mode="after")
    def validate_threshold_order(self):
        if self.review > self.shortlist:
            raise ValueError(
                "Review threshold cannot exceed shortlist threshold."
            )
        return self


class ShortlistingRequest(BaseModel):
    candidate_reports: list[CandidateReportInput]
    thresholds: ShortlistingThresholds = Field(
        default_factory=ShortlistingThresholds
    )
