from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

from app.core.bazi import BaziService
from app.schemas import AnalyzeRequest, AnalyzeResponse, ChartRequest, ChartResponse
from app.services.ai import AIAnalysisService

router = APIRouter()


@router.post("/chart", response_model=ChartResponse)
async def create_chart(body: ChartRequest) -> ChartResponse:
    try:
        chart = BaziService.build_chart(body.to_birth_input())
        return ChartResponse(success=True, data=chart)
    except ValueError as e:
        return ChartResponse(success=False, error=str(e))
    except Exception:
        return ChartResponse(success=False, error="排盘失败，请检查输入")


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_chart(body: AnalyzeRequest) -> AnalyzeResponse:
    try:
        text = await AIAnalysisService.analyze(body.chart, body.style)
        return AnalyzeResponse(success=True, analysis=text)
    except ValueError as e:
        return AnalyzeResponse(success=False, error=str(e))
    except Exception as e:
        return AnalyzeResponse(success=False, error=f"分析失败: {e}")
