"""Tests for target engine 2.0 and review endpoints."""
from datetime import date, datetime, timezone, timedelta

from fastapi.testclient import TestClient

from app.models.time_trace import TimeTrace
from app.services.evaluation import evaluate_targets_for_date


def _auth(client: TestClient, email: str, username: str) -> tuple[dict, int]:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": username, "password": "testpass123"},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": "testpass123"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    me = client.get("/api/v1/users/me", headers=headers)
    return headers, me.json()["id"]


def _create_target(
    client: TestClient,
    headers: dict,
    period: str,
    target_seconds: int,
    effective_from: datetime,
) -> int:
    response = client.post(
        "/api/v1/targets",
        json={
            "period": period,
            "target_seconds": target_seconds,
            "effective_from": effective_from.isoformat(),
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _manual_session(
    client: TestClient,
    headers: dict,
    start: datetime,
    end: datetime,
    note: str = "work",
    category_id: int | None = None,
) -> None:
    payload = {
        "start_time": start.isoformat(),
        "end_time": end.isoformat(),
        "note": note,
    }
    if category_id is not None:
        payload["category_id"] = category_id
    response = client.post("/api/v1/sessions/manual", json=payload, headers=headers)
    assert response.status_code == 201, response.text


def test_weekly_monthly_and_tomorrow_targets_are_evaluated(client: TestClient, db_session):
    headers, user_id = _auth(client, "engine_periods@example.com", "engineperiods")

    _create_target(
        client,
        headers,
        "weekly",
        7200,
        datetime(2025, 12, 1, 0, 0, tzinfo=timezone.utc),
    )
    _create_target(
        client,
        headers,
        "monthly",
        14400,
        datetime(2025, 12, 1, 0, 0, tzinfo=timezone.utc),
    )
    _create_target(
        client,
        headers,
        "tomorrow",
        7200,
        datetime(2025, 12, 16, 0, 0, tzinfo=timezone.utc),
    )

    _manual_session(
        client,
        headers,
        datetime(2025, 12, 1, 9, 0, tzinfo=timezone.utc),
        datetime(2025, 12, 1, 12, 0, tzinfo=timezone.utc),
    )
    _manual_session(
        client,
        headers,
        datetime(2025, 12, 16, 9, 0, tzinfo=timezone.utc),
        datetime(2025, 12, 16, 10, 0, tzinfo=timezone.utc),
    )
    _manual_session(
        client,
        headers,
        datetime(2025, 12, 20, 9, 0, tzinfo=timezone.utc),
        datetime(2025, 12, 20, 11, 0, tzinfo=timezone.utc),
    )

    assert evaluate_targets_for_date(date(2025, 12, 6), db_session, user_id=user_id) == []

    weekly = evaluate_targets_for_date(date(2025, 12, 7), db_session, user_id=user_id)
    assert len(weekly) == 1
    assert weekly[0].status == "met"
    assert weekly[0].actual_seconds == 10800

    tomorrow = evaluate_targets_for_date(date(2025, 12, 16), db_session, user_id=user_id)
    assert len(tomorrow) == 1
    assert tomorrow[0].status == "missed"
    assert tomorrow[0].deficit_seconds == 3600

    monthly = evaluate_targets_for_date(date(2025, 12, 31), db_session, user_id=user_id)
    assert len(monthly) == 1
    assert monthly[0].status == "met"
    assert monthly[0].actual_seconds == 21600


def test_time_debt_is_created_and_compensated(client: TestClient, db_session):
    headers, user_id = _auth(client, "engine_debt@example.com", "enginedebt")
    _create_target(
        client,
        headers,
        "daily",
        10800,
        datetime(2025, 12, 10, 0, 0, tzinfo=timezone.utc),
    )

    _manual_session(
        client,
        headers,
        datetime(2025, 12, 10, 9, 0, tzinfo=timezone.utc),
        datetime(2025, 12, 10, 11, 0, tzinfo=timezone.utc),
    )
    missed = evaluate_targets_for_date(date(2025, 12, 10), db_session, user_id=user_id)
    assert missed[0].status == "missed"
    assert missed[0].deficit_seconds == 3600

    dashboard = client.get("/api/v1/targets/dashboard", headers=headers)
    assert dashboard.status_code == 200
    metric = dashboard.json()["metrics"][0]
    assert metric["active_debt_seconds"] == 3600
    assert metric["suggested_compensation_seconds"] == 1800

    _manual_session(
        client,
        headers,
        datetime(2025, 12, 11, 9, 0, tzinfo=timezone.utc),
        datetime(2025, 12, 11, 13, 0, tzinfo=timezone.utc),
    )
    met = evaluate_targets_for_date(date(2025, 12, 11), db_session, user_id=user_id)
    assert met[0].status == "met"

    dashboard = client.get("/api/v1/targets/dashboard", headers=headers).json()
    metric = dashboard["metrics"][0]
    assert metric["active_debt_seconds"] == 0
    assert any(event["rule_type"] == "compensation" for event in dashboard["events"])


def test_daily_and_weekly_reviews_include_stats_targets_traces_and_markdown(client: TestClient, db_session):
    headers, user_id = _auth(client, "review@example.com", "reviewuser")
    category = client.post("/api/v1/categories", json={"name": "Study"}, headers=headers).json()
    _create_target(
        client,
        headers,
        "daily",
        7200,
        datetime(2025, 12, 8, 0, 0, tzinfo=timezone.utc),
    )

    _manual_session(
        client,
        headers,
        datetime(2025, 12, 8, 9, 0, tzinfo=timezone.utc),
        datetime(2025, 12, 8, 12, 0, tzinfo=timezone.utc),
        note="deep work",
        category_id=category["id"],
    )
    db_session.add(TimeTrace(
        user_id=user_id,
        content="复盘时痕",
        created_at=datetime(2025, 12, 8, 20, 0, tzinfo=timezone.utc),
    ))
    db_session.commit()
    evaluate_targets_for_date(date(2025, 12, 8), db_session, user_id=user_id)

    daily = client.get("/api/v1/reviews/daily?date=2025-12-08", headers=headers)
    assert daily.status_code == 200, daily.text
    daily_data = daily.json()
    assert daily_data["total_seconds"] == 10800
    assert daily_data["top_category"]["category_name"] == "Study"
    assert daily_data["target_summary"]["met_count"] == 1
    assert daily_data["time_traces"][0]["content"] == "复盘时痕"
    assert "# 日报复盘 2025-12-08" in daily_data["markdown"]

    weekly = client.get("/api/v1/reviews/weekly?date=2025-12-08", headers=headers)
    assert weekly.status_code == 200, weekly.text
    weekly_data = weekly.json()
    assert weekly_data["total_seconds"] == 10800
    assert weekly_data["average_daily_seconds"] == 1542
    assert weekly_data["best_day"]["date"] == "2025-12-08"
    assert weekly_data["gap_days"] == 6
    assert "# 周报复盘 2025-12-08 - 2025-12-14" in weekly_data["markdown"]
