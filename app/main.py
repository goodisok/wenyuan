# -*- coding: utf-8 -*-
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import __version__
from app.api.routes import router as api_router
from app.config import settings

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
templates.env.globals["app_version"] = __version__

app = FastAPI(
    title="问元",
    description="探问天地人三元 · 八字排盘 · 大运流年 · AI 命理解读",
    version=__version__,
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.include_router(api_router, prefix="/api", tags=["api"])


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/chart", response_class=HTMLResponse)
async def chart_page(request: Request):
    return templates.TemplateResponse(request, "chart.html")


@app.get("/privacy", response_class=HTMLResponse)
async def privacy(request: Request):
    return templates.TemplateResponse(request, "privacy.html")


@app.get("/support", response_class=HTMLResponse)
async def support(request: Request):
    return templates.TemplateResponse(request, "support.html")


@app.get("/health")
async def health():
    return {"status": "ok", "version": __version__}


def run():
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug,
    )


if __name__ == "__main__":
    run()
