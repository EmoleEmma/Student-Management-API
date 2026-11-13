import pytest

NEW_COURSE = {"code": "CSC999", "title": "X", "credit_units": 3}

PROTECTED = [
    ("GET", "/students"), ("POST", "/students"), ("GET", "/students/me"),
    ("GET", "/courses"), ("POST", "/courses"), ("GET", "/courses/mine"),
    ("GET", "/lecturers"), ("GET", "/admin/ping"),
]

ADMIN_ONLY = [
    ("POST", "/courses", NEW_COURSE),
    ("GET", "/lecturers", None),
    ("GET", "/admin/ping", None),
]


@pytest.mark.parametrize("method,path", PROTECTED)
def test_no_token_is_401(client, method, path):
    assert client.request(method, path).status_code == 401


@pytest.mark.parametrize("method,path,body", ADMIN_ONLY)
@pytest.mark.parametrize("email", ["s1@test.com", "lec1@test.com"])
def test_non_admins_get_403_on_admin_endpoints(client, world, login, email, method, path, body):
    r = client.request(method, path, json=body, headers=login(email))
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "forbidden"


def test_student_cannot_list_students(client, world, login):
    assert client.get("/students", headers=login("s1@test.com")).status_code == 403


def test_student_cannot_view_another_student(client, world, login):
    h = login("s1@test.com")
    assert client.get(f"/students/{world.s1}", headers=h).status_code == 200
    assert client.get(f"/students/{world.s2}", headers=h).status_code == 403


def test_student_cannot_view_another_transcript(client, world, login):
    h = login("s1@test.com")
    assert client.get(f"/students/{world.s1}/transcript", headers=h).status_code == 200
    assert client.get(f"/students/{world.s2}/transcript", headers=h).status_code == 403


def test_lecturer_cannot_view_a_transcript(client, world, login):
    client.post(f"/courses/{world.c1}/register", headers=login("s1@test.com"))
    r = client.get(f"/students/{world.s1}/transcript", headers=login("lec1@test.com"))
    assert r.status_code == 403


def test_lecturer_sees_only_students_in_own_courses(client, world, login):
    client.post(f"/courses/{world.c1}/register", headers=login("s1@test.com"))
    h1, h2 = login("lec1@test.com"), login("lec2@test.com")
    assert client.get(f"/students/{world.s1}", headers=h1).status_code == 200
    assert client.get(f"/students/{world.s1}", headers=h2).status_code == 403
    assert [s["id"] for s in client.get("/students", headers=h1).json()] == [world.s1]
    assert client.get("/students", headers=h2).json() == []


def test_lecturer_cannot_see_roster_of_other_course(client, world, login):
    h = login("lec1@test.com")
    assert client.get(f"/courses/{world.c1}/students", headers=h).status_code == 200
    assert client.get(f"/courses/{world.c2}/students", headers=h).status_code == 403


def test_lecturer_can_only_grade_own_course(client, world, login):
    s1 = login("s1@test.com")
    client.post(f"/courses/{world.c1}/register", headers=s1)
    client.post(f"/courses/{world.c2}/register", headers=s1)
    lec1 = login("lec1@test.com")
    own = client.put(f"/courses/{world.c1}/students/{world.s1}/grade", json={"score": 70}, headers=lec1)
    other = client.put(f"/courses/{world.c2}/students/{world.s1}/grade", json={"score": 70}, headers=lec1)
    assert own.status_code == 200
    assert other.status_code == 403


def test_student_cannot_grade_themselves(client, world, login):
    h = login("s1@test.com")
    client.post(f"/courses/{world.c1}/register", headers=h)
    r = client.put(f"/courses/{world.c1}/students/{world.s1}/grade", json={"score": 100}, headers=h)
    assert r.status_code == 403


def test_lecturer_cannot_register_for_courses(client, world, login):
    r = client.post(f"/courses/{world.c1}/register", headers=login("lec1@test.com"))
    assert r.status_code == 403


def test_admin_can_do_everything_staff_can(client, world, login):
    h = login("admin@test.com")
    assert client.get("/admin/ping", headers=h).status_code == 200
    assert client.get("/students", headers=h).status_code == 200
    assert client.get(f"/courses/{world.c1}/students", headers=h).status_code == 200


def test_deactivated_user_token_stops_working(client, world, login, deactivate):
    h = login("s1@test.com")
    assert client.get("/users/me", headers=h).status_code == 200
    deactivate("s1@test.com")
    assert client.get("/users/me", headers=h).status_code == 401