import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["version"] == "1.2.0"


def test_index_page():
    res = client.get("/")
    assert res.status_code == 200
    assert "问元" in res.text
    assert "开始排盘" in res.text
    assert "闰月" in res.text


def test_chart_page():
    res = client.get("/chart")
    assert res.status_code == 200
    assert "chart-root" in res.text


def test_privacy_page():
    res = client.get("/privacy")
    assert res.status_code == 200
    assert "隐私" in res.text
    assert "不持久化" in res.text


def test_api_chart_solar_male():
    res = client.post(
        "/api/chart",
        json={
            "date_type": "solar",
            "birth_date": "1990-05-15",
            "birth_time": "12:30",
            "gender": "male",
            "is_leap_month": False,
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    data = body["data"]
    assert len(data["pillars"]) == 4
    assert data["meta"]["day_dishi"]
    assert data.get("insight")
    assert data.get("qiyun")
    assert "pillars_relations" in data


def test_api_chart_female_lunar():
    res = client.post(
        "/api/chart",
        json={
            "date_type": "lunar",
            "birth_date": "1990-04-21",
            "birth_time": "08:00",
            "gender": "female",
            "is_leap_month": False,
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert body["data"]["meta"]["gender_label"] == "女"


def test_api_chart_leap_month():
    res = client.post(
        "/api/chart",
        json={
            "date_type": "lunar",
            "birth_date": "2020-04-01",
            "birth_time": "10:00",
            "gender": "female",
            "is_leap_month": True,
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert body["data"]["meta"]["is_leap_month"] is True


def test_api_chart_invalid_date():
    res = client.post(
        "/api/chart",
        json={
            "date_type": "solar",
            "birth_date": "1990-02-30",
            "birth_time": "12:00",
            "gender": "male",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is False


def test_api_chart_validation_error():
    res = client.post(
        "/api/chart",
        json={"birth_date": "bad", "birth_time": "12:00", "gender": "male"},
    )
    assert res.status_code == 422


def test_api_analyze_without_api_key(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "deepseek_api_key", "")
    chart_res = client.post(
        "/api/chart",
        json={
            "date_type": "solar",
            "birth_date": "1990-05-15",
            "birth_time": "12:30",
            "gender": "male",
        },
    )
    chart = chart_res.json()["data"]
    res = client.post("/api/analyze", json={"chart": chart, "style": "classic"})
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is False
    assert "DEEPSEEK_API_KEY" in (body.get("error") or "")


def test_api_analyze_ai_disabled(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "ai_enabled", False)
    monkeypatch.setattr(settings, "deepseek_api_key", "test-key")
    chart_res = client.post(
        "/api/chart",
        json={
            "date_type": "solar",
            "birth_date": "1990-05-15",
            "birth_time": "12:30",
            "gender": "male",
        },
    )
    chart = chart_res.json()["data"]
    res = client.post("/api/analyze", json={"chart": chart, "style": "classic"})
    assert res.status_code == 503


def test_api_ask_without_key(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "deepseek_api_key", "")
    chart_res = client.post(
        "/api/chart",
        json={
            "date_type": "solar",
            "birth_date": "1990-05-15",
            "birth_time": "12:30",
            "gender": "male",
        },
    )
    chart = chart_res.json()["data"]
    res = client.post(
        "/api/ask",
        json={"chart": chart, "question": "当前大运如何？", "style": "classic"},
    )
    assert res.status_code == 200
    assert res.json()["success"] is False


def test_api_ask_round_limit():
    chart_res = client.post(
        "/api/chart",
        json={
            "date_type": "solar",
            "birth_date": "1990-05-15",
            "birth_time": "12:30",
            "gender": "male",
        },
    )
    chart = chart_res.json()["data"]
    history = []
    for i in range(8):
        history.extend([
            {"role": "user", "content": f"问{i}"},
            {"role": "assistant", "content": f"答{i}"},
        ])
    res = client.post(
        "/api/ask",
        json={"chart": chart, "question": "第九问", "history": history, "style": "classic"},
    )
    assert res.status_code == 200
    assert res.json()["success"] is False
    assert "上限" in res.json()["error"]
