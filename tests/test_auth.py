def test_register_creates_student_and_never_returns_hash(client):
    r = client.post("/auth/register", json={"email": "a@test.com", "password": "Password123"})
    assert r.status_code == 201
    body = r.json()
    assert body["role"] == "STUDENT"
    assert "password" not in body and "hashed_password" not in body


def test_register_cannot_self_assign_admin(client):
    r = client.post(
        "/auth/register",
        json={"email": "x@test.com", "password": "Password123", "role": "ADMIN"},
    )
    assert r.status_code == 201
    assert r.json()["role"] == "STUDENT"


def test_duplicate_email_is_409(client):
    payload = {"email": "dup@test.com", "password": "Password123"}
    assert client.post("/auth/register", json=payload).status_code == 201
    r = client.post("/auth/register", json=payload)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "conflict"


def test_short_password_is_422_with_consistent_shape(client):
    r = client.post("/auth/register", json={"email": "b@test.com", "password": "short"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error"


def test_wrong_password_is_401(client):
    client.post("/auth/register", json={"email": "c@test.com", "password": "Password123"})
    r = client.post("/auth/login", data={"username": "c@test.com", "password": "WrongPass999"})
    assert r.status_code == 401


def test_unknown_email_gives_same_error_as_wrong_password(client):
    r = client.post("/auth/login", data={"username": "nobody@test.com", "password": "Password123"})
    assert r.status_code == 401
    assert r.json()["error"]["message"] == "Incorrect email or password"


def test_me_requires_token(client):
    assert client.get("/users/me").status_code == 401


def test_garbage_token_is_401(client):
    r = client.get("/users/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert r.status_code == 401