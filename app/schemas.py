from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ChartRequest(BaseModel):
    date_type: Literal["solar", "lunar"] = "solar"
    birth_date: str = Field(..., description="YYYY-MM-DD")
    birth_time: str = Field(..., description="HH:mm")
    gender: Literal["male", "female"] = "male"
    is_leap_month: bool = False

    @field_validator("birth_date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        parts = v.split("-")
        if len(parts) != 3:
            raise ValueError("日期格式应为 YYYY-MM-DD")
        y, m, d = (int(x) for x in parts)
        if not (1900 <= y <= 2100 and 1 <= m <= 12 and 1 <= d <= 31):
            raise ValueError("日期超出有效范围")
        return v

    @field_validator("birth_time")
    @classmethod
    def validate_time(cls, v: str) -> str:
        parts = v.split(":")
        if len(parts) != 2:
            raise ValueError("时间格式应为 HH:mm")
        h, mi = (int(x) for x in parts)
        if not (0 <= h <= 23 and 0 <= mi <= 59):
            raise ValueError("时间无效")
        return v

    def to_birth_input(self):
        from app.core.bazi import BirthInput

        y, m, d = (int(x) for x in self.birth_date.split("-"))
        h, mi = (int(x) for x in self.birth_time.split(":"))
        return BirthInput(
            date_type=self.date_type,
            year=y, month=m, day=d,
            hour=h, minute=mi,
            gender=self.gender,
            is_leap_month=self.is_leap_month,
        )


class ChartResponse(BaseModel):
    success: bool = True
    data: dict | None = None
    error: str | None = None


class AnalyzeRequest(BaseModel):
    chart: dict = Field(..., description="完整排盘结果")
    insight: dict | None = Field(None, description="客户端 insight（服务端忽略，仅兼容旧版）")
    style: Literal["classic", "modern"] = "modern"


class AnalyzeResponse(BaseModel):
    success: bool
    analysis: str | None = None
    error: str | None = None


class AskRequest(BaseModel):
    chart: dict = Field(..., description="完整排盘结果")
    insight: dict | None = Field(None, description="客户端 insight（服务端忽略，仅兼容旧版）")
    analysis: str = ""
    question: str = Field(..., min_length=1, max_length=500)
    history: list[dict[str, str]] = Field(default_factory=list)
    style: Literal["classic", "modern"] = "modern"

    @field_validator("history")
    @classmethod
    def validate_history(cls, v: list[dict[str, str]]) -> list[dict[str, str]]:
        if len(v) > 100:
            raise ValueError("历史对话过长")
        for item in v:
            if item.get("role") not in ("user", "assistant") or not item.get("content"):
                raise ValueError("history 格式无效")
        return v


class AskResponse(BaseModel):
    success: bool
    answer: str | None = None
    error: str | None = None
