import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from app.core.bazi import BaziService
from app.core.insight import ensure_ai_insight, public_insight
from app.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    AskRequest,
    AskResponse,
    ChartRequest,
    ChartResponse,
)
from app.services.ai import AIAnalysisService

logger = logging.getLogger(__name__)
router = APIRouter()


def _wants_sse(request: Request) -> bool:
    accept = request.headers.get("accept", "")
    return "text/event-stream" in accept


def _ai_disabled_response():
    return JSONResponse(
        status_code=503,
        content={"success": False, "error": "AI 解读暂时关闭，请稍后再试"},
    )


@router.post("/chart", response_model=ChartResponse)
async def create_chart(body: ChartRequest) -> ChartResponse:
    try:
        chart = BaziService.build_chart(body.to_birth_input())
        chart = dict(chart)
        chart["insight"] = public_insight(chart["insight"])
        return ChartResponse(success=True, data=chart)
    except ValueError as e:
        return ChartResponse(success=False, error=str(e))
    except Exception:
        logger.exception("排盘失败")
        return ChartResponse(success=False, error="排盘失败，请检查输入")


@router.post("/analyze")
async def analyze_chart(body: AnalyzeRequest, request: Request):
    try:
        insight = ensure_ai_insight(body.chart, body.insight or body.chart.get("insight"))
        if _wants_sse(request):
            gen = AIAnalysisService.analyze_sse(body.chart, body.style, insight)
            return StreamingResponse(gen, media_type="text/event-stream")
        text = await AIAnalysisService.analyze(body.chart, body.style, insight)
        return AnalyzeResponse(success=True, analysis=text)
    except ValueError as e:
        msg = str(e)
        status = 503 if "暂时关闭" in msg else 200
        if status == 503:
            return _ai_disabled_response()
        return AnalyzeResponse(success=False, error=msg)
    except Exception:
        logger.exception("AI 分析失败")
        return AnalyzeResponse(success=False, error="分析失败，请稍后重试")


@router.post("/ask")
async def ask_chart(body: AskRequest, request: Request):
    try:
        insight = ensure_ai_insight(body.chart, body.insight or body.chart.get("insight"))
        if _wants_sse(request):
            gen = AIAnalysisService.ask_sse(
                body.chart,
                body.question,
                body.style,
                insight,
                body.analysis,
                body.history,
            )
            return StreamingResponse(gen, media_type="text/event-stream")
        answer = await AIAnalysisService.ask(
            body.chart,
            body.question,
            body.style,
            insight,
            body.analysis,
            body.history,
        )
        return AskResponse(success=True, answer=answer)
    except ValueError as e:
        msg = str(e)
        if "暂时关闭" in msg:
            return _ai_disabled_response()
        return AskResponse(success=False, error=msg)
    except Exception:
        logger.exception("AI 问答失败")
        return AskResponse(success=False, error="问答失败，请稍后重试")
