import bcrypt
from jose import jwt


FAKE_INFO = ("John Doe", "100000000", {}, {}, {"202530": []}, [])


def test_register_success(client, monkeypatch, async_mock):
    monkeypatch.setattr("server.db_register", async_mock((1, FAKE_INFO)))
    monkeypatch.setattr("server.fetch_and_store_grades", async_mock(None))
    monkeypatch.setattr("server.send_welcome_email", lambda *a, **k: None)

    response = client.post(
        "/register",
        json={"username": "jdoe", "password": "pw", "email": "j@example.com"},
    )

    assert response.status_code == 200
    assert "accessToken" in response.json()


def test_register_duplicate_username(client, monkeypatch, async_mock):
    monkeypatch.setattr("server.db_register", async_mock("username already exists"))

    response = client.post(
        "/register",
        json={"username": "jdoe", "password": "pw", "email": "j@example.com"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "username already exists"


def test_register_invalid_carleton_credentials(client, monkeypatch, async_mock):
    monkeypatch.setattr("server.db_register", async_mock("invalid credentials"))

    response = client.post(
        "/register",
        json={"username": "jdoe", "password": "pw", "email": "j@example.com"},
    )

    assert response.status_code == 401


def test_login_success(client, monkeypatch, async_mock):
    hashed = bcrypt.hashpw(b"pw", bcrypt.gensalt()).decode()
    monkeypatch.setattr(
        "server.get_user",
        async_mock({"user_id": 1, "hashed_password": hashed}),
    )

    response = client.post("/login", json={"username": "jdoe", "password": "pw"})

    assert response.status_code == 200
    assert "accessToken" in response.json()


def test_login_wrong_password(client, monkeypatch, async_mock):
    hashed = bcrypt.hashpw(b"correct", bcrypt.gensalt()).decode()
    monkeypatch.setattr(
        "server.get_user",
        async_mock({"user_id": 1, "hashed_password": hashed}),
    )

    response = client.post("/login", json={"username": "jdoe", "password": "wrong"})

    assert response.status_code == 401


def test_login_unknown_user(client, monkeypatch, async_mock):
    monkeypatch.setattr("server.get_user", async_mock("username not found"))

    response = client.post("/login", json={"username": "ghost", "password": "pw"})

    assert response.status_code == 401


def test_get_grades_requires_auth(client):
    response = client.get("/grades")
    assert response.status_code == 401


def test_get_grades_rejects_bad_token(client):
    response = client.get("/grades", headers={"Authorization": "Bearer garbage"})
    assert response.status_code == 401


def test_get_grades_returns_data(client, monkeypatch, as_user, async_mock):
    as_user("1")
    monkeypatch.setattr(
        "server.db_get_grades",
        async_mock(({"202530": [{"crn": "30001", "finalgrade": "A+"}]}, "2026-01-01T00:00:00")),
    )

    response = client.get("/grades", headers={"Authorization": "Bearer x"})

    assert response.status_code == 200
    body = response.json()
    assert body["last_updated"] == "2026-01-01T00:00:00"
    assert body["grades"]["202530"][0]["finalgrade"] == "A+"


def test_get_me_returns_username_and_email_only(client, monkeypatch, as_user, async_mock):
    as_user("1")
    monkeypatch.setattr(
        "server.get_user_credentials",
        async_mock({"username": "jdoe", "password": "SECRET", "email": "j@example.com", "is_test": False, "grade_emails_enabled": True}),
    )

    response = client.get("/users/me", headers={"Authorization": "Bearer x"})

    assert response.status_code == 200
    body = response.json()
    assert body == {"username": "jdoe", "email": "j@example.com", "is_demo": False, "grade_emails_enabled": True}
    assert "password" not in body


def test_get_me_requires_auth(client):
    response = client.get("/users/me")
    assert response.status_code == 401


def test_update_email_success(client, monkeypatch, as_user, async_mock):
    as_user("1")
    monkeypatch.setattr("server.verify_user_password", async_mock(True))
    monkeypatch.setattr(
        "server.get_user_credentials",
        async_mock({"username": "jdoe", "password": "pw", "email": "old@example.com", "is_test": False, "grade_emails_enabled": True}),
    )
    monkeypatch.setattr("server.db_update_email", async_mock(None))
    monkeypatch.setattr("server.send_email_changed_old", lambda *a, **k: None)
    monkeypatch.setattr("server.send_email_changed_new", lambda *a, **k: None)

    response = client.patch(
        "/users/me/email",
        headers={"Authorization": "Bearer x"},
        json={"email": "new@example.com", "current_password": "pw"},
    )

    assert response.status_code == 200
    assert response.json() == {"success": True}


REAL_USER = {"username": "jdoe", "password": "pw", "email": "j@example.com", "is_test": False, "grade_emails_enabled": True}
DEMO_USER = {"username": "__test_user__", "password": "pw", "email": "demo@example.com", "is_test": True, "grade_emails_enabled": True}


def test_update_email_wrong_password(client, monkeypatch, as_user, async_mock):
    as_user("1")
    monkeypatch.setattr("server.get_user_credentials", async_mock(REAL_USER))
    monkeypatch.setattr("server.verify_user_password", async_mock(False))

    response = client.patch(
        "/users/me/email",
        headers={"Authorization": "Bearer x"},
        json={"email": "new@example.com", "current_password": "wrong"},
    )

    assert response.status_code == 401


def test_update_password_success(client, monkeypatch, as_user, async_mock):
    as_user("1")
    monkeypatch.setattr(
        "server.get_user_credentials",
        async_mock({"username": "jdoe", "password": "pw", "email": "j@example.com", "is_test": False, "grade_emails_enabled": True}),
    )
    monkeypatch.setattr("server.info", async_mock(FAKE_INFO))
    monkeypatch.setattr("server.db_update_password", async_mock(None))

    response = client.patch(
        "/users/me/password",
        headers={"Authorization": "Bearer x"},
        json={"password": "newpw"},
    )

    assert response.status_code == 200


def test_update_password_rejected_by_carleton(client, monkeypatch, as_user, async_mock):
    as_user("1")
    monkeypatch.setattr(
        "server.get_user_credentials",
        async_mock({"username": "jdoe", "password": "pw", "email": "j@example.com", "is_test": False, "grade_emails_enabled": True}),
    )
    monkeypatch.setattr("server.info", async_mock(None))

    response = client.patch(
        "/users/me/password",
        headers={"Authorization": "Bearer x"},
        json={"password": "wrongpw"},
    )

    assert response.status_code == 401


def test_delete_user_success(client, monkeypatch, as_user, async_mock):
    as_user("1")
    monkeypatch.setattr("server.verify_user_password", async_mock(True))
    monkeypatch.setattr(
        "server.get_user_credentials",
        async_mock({"username": "jdoe", "password": "pw", "email": "j@example.com", "is_test": False, "grade_emails_enabled": True}),
    )
    monkeypatch.setattr("server.db_delete_user", async_mock(None))
    monkeypatch.setattr("server.send_goodbye_email", lambda *a, **k: None)

    response = client.request(
        "DELETE",
        "/users/me",
        headers={"Authorization": "Bearer x"},
        json={"current_password": "pw"},
    )

    assert response.status_code == 200
    assert response.json() == {"success": True}


def test_delete_user_wrong_password(client, monkeypatch, as_user, async_mock):
    as_user("1")
    monkeypatch.setattr("server.get_user_credentials", async_mock(REAL_USER))
    monkeypatch.setattr("server.verify_user_password", async_mock(False))

    response = client.request(
        "DELETE",
        "/users/me",
        headers={"Authorization": "Bearer x"},
        json={"current_password": "wrong"},
    )

    assert response.status_code == 401

def test_update_password_rejects_test_account(client, monkeypatch, as_user, async_mock):
    as_user("1")
    monkeypatch.setattr(
        "server.get_user_credentials",
        async_mock({"username": "jdoe", "password": "pw", "email": "j@example.com", "is_test": True, "grade_emails_enabled": True}),
    )

    response = client.patch(
        "/users/me/password",
        headers={"Authorization": "Bearer x"},
        json={"password": "newpw"},
    )

    assert response.status_code == 403


def test_demo_issues_session_token(client, monkeypatch, async_mock):
    monkeypatch.setattr("server.get_demo_user_id", async_mock(42))

    response = client.post("/demo")

    assert response.status_code == 200
    claims = jwt.get_unverified_claims(response.json()["accessToken"])
    assert claims["sub"] == "42"
    assert claims["demo"] is True


def test_demo_unavailable_without_demo_account(client, monkeypatch, async_mock):
    monkeypatch.setattr("server.get_demo_user_id", async_mock(None))

    response = client.post("/demo")

    assert response.status_code == 404


def test_get_me_flags_demo_account(client, monkeypatch, as_user, async_mock):
    as_user("1")
    monkeypatch.setattr("server.get_user_credentials", async_mock(DEMO_USER))

    response = client.get("/users/me", headers={"Authorization": "Bearer x"})

    assert response.json()["is_demo"] is True


def test_grade_check_rejects_demo_account(client, monkeypatch, as_user, async_mock):
    as_user("1")
    monkeypatch.setattr("server.get_user_credentials", async_mock(DEMO_USER))

    response = client.post("/grades/check", headers={"Authorization": "Bearer x"})

    assert response.status_code == 403


def test_update_email_rejects_demo_before_password_check(client, monkeypatch, as_user, async_mock):
    as_user("1")
    monkeypatch.setattr("server.get_user_credentials", async_mock(DEMO_USER))
    monkeypatch.setattr("server.verify_user_password", async_mock(False))

    response = client.patch(
        "/users/me/email",
        headers={"Authorization": "Bearer x"},
        json={"email": "new@example.com", "current_password": "anything"},
    )

    assert response.status_code == 403


def test_delete_rejects_demo_before_password_check(client, monkeypatch, as_user, async_mock):
    as_user("1")
    monkeypatch.setattr("server.get_user_credentials", async_mock(DEMO_USER))
    monkeypatch.setattr("server.verify_user_password", async_mock(False))

    response = client.request(
        "DELETE",
        "/users/me",
        headers={"Authorization": "Bearer x"},
        json={"current_password": "anything"},
    )

    assert response.status_code == 403
