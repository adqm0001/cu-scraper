import os
from datetime import datetime, timedelta, timezone

from jose import jwt

from poller import build_grade_change_email
from tokens import create_unsubscribe_token, read_unsubscribe_token, unsubscribe_url

USER = {"username": "jdoe", "password": "pw", "email": "j@example.com", "is_test": False, "grade_emails_enabled": True}
DEMO = {**USER, "username": "__test_user__", "is_test": True}


def login_token(user_id="7"):
    return jwt.encode(
        {"sub": user_id, "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        os.environ["JWT_SECRET"],
        algorithm="HS256",
    )


def record_calls(calls, result=True):
    async def _fn(*args):
        calls.append(args)
        return result
    return _fn


def test_unsubscribe_token_round_trip():
    assert read_unsubscribe_token(create_unsubscribe_token(7)) == "7"


def test_login_token_cannot_unsubscribe():
    assert read_unsubscribe_token(login_token()) is None


def test_tampered_unsubscribe_token_is_rejected():
    token = create_unsubscribe_token(7)
    assert read_unsubscribe_token(token[:-2] + ("A" if token[-2] != "A" else "B") + token[-1]) is None


def test_unsubscribe_token_cannot_log_in(client):
    response = client.get("/grades", headers={"Authorization": f"Bearer {create_unsubscribe_token(7)}"})
    assert response.status_code == 401


def test_unsubscribe_url_has_no_email_address():
    url = unsubscribe_url(7)
    assert "/unsubscribe?token=" in url
    assert "@" not in url


def test_grade_email_includes_unsubscribe_link():
    _, body = build_grade_change_email({"202530": [{"subject": "ECOR", "course": "1031", "finalgrade": "A"}]}, "https://x/unsubscribe?token=abc")
    assert "Unsubscribe from grade updates" in body
    assert "https://x/unsubscribe?token=abc" in body


def test_unsubscribe_endpoint_turns_off_grade_emails(client, monkeypatch):
    calls = []
    monkeypatch.setattr("server.set_grade_emails", record_calls(calls))

    response = client.post("/unsubscribe", json={"token": create_unsubscribe_token(7)})

    assert response.status_code == 200
    assert calls == [("7", False)]


def test_unsubscribe_endpoint_rejects_login_token(client, monkeypatch):
    calls = []
    monkeypatch.setattr("server.set_grade_emails", record_calls(calls))

    response = client.post("/unsubscribe", json={"token": login_token()})

    assert response.status_code == 400
    assert calls == []


def test_unsubscribe_endpoint_rejects_unknown_user(client, monkeypatch):
    monkeypatch.setattr("server.set_grade_emails", record_calls([], result=False))

    response = client.post("/unsubscribe", json={"token": create_unsubscribe_token(999)})

    assert response.status_code == 400


def test_unsubscribe_is_not_possible_with_get(client):
    response = client.get(f"/unsubscribe?token={create_unsubscribe_token(7)}")
    assert response.status_code == 405


def test_notification_toggle_updates_setting(client, monkeypatch, as_user, async_mock):
    as_user("7")
    calls = []
    monkeypatch.setattr("server.get_user_credentials", async_mock(USER))
    monkeypatch.setattr("server.set_grade_emails", record_calls(calls))

    response = client.patch("/users/me/notifications", headers={"Authorization": "Bearer x"}, json={"grade_emails_enabled": False})

    assert response.status_code == 200
    assert response.json() == {"grade_emails_enabled": False}
    assert calls == [("7", False)]


def test_notification_toggle_blocked_for_demo(client, monkeypatch, as_user, async_mock):
    as_user("7")
    calls = []
    monkeypatch.setattr("server.get_user_credentials", async_mock(DEMO))
    monkeypatch.setattr("server.set_grade_emails", record_calls(calls))

    response = client.patch("/users/me/notifications", headers={"Authorization": "Bearer x"}, json={"grade_emails_enabled": False})

    assert response.status_code == 403
    assert calls == []


def test_notification_toggle_requires_login(client):
    response = client.patch("/users/me/notifications", json={"grade_emails_enabled": False})
    assert response.status_code == 401
