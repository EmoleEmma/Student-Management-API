from decimal import Decimal


def _register(client, headers, course_id):
    return client.post(f"/courses/{course_id}/register", headers=headers)


def _grade(client, headers, course_id, student_id, score):
    return client.put(
        f"/courses/{course_id}/students/{student_id}/grade", json={"score": score}, headers=headers
    )


def test_registration_grading_and_gpa(client, world, login):
    s1 = login("s1@test.com")
    assert _register(client, s1, world.c1).status_code == 201
    assert _register(client, s1, world.c2).status_code == 201

    r = _grade(client, login("lec1@test.com"), world.c1, world.s1, 80)
    assert r.status_code == 200 and r.json()["grade"] == "A"
    _grade(client, login("lec2@test.com"), world.c2, world.s1, 55)

    t = client.get("/students/me/transcript", headers=s1).json()
    assert t["graded_units"] == 5
    assert Decimal(t["gpa"]) == Decimal("4.20")  # (3*5 + 2*3) / 5
    assert [row["course_code"] for row in t["courses"]] == ["CSC101", "CSC102"]


def test_ungraded_courses_are_listed_but_not_in_gpa(client, world, login):
    s1 = login("s1@test.com")
    _register(client, s1, world.c1)
    _register(client, s1, world.c2)
    _grade(client, login("lec1@test.com"), world.c1, world.s1, 65)
    t = client.get("/students/me/transcript", headers=s1).json()
    assert t["graded_units"] == 3 and Decimal(t["gpa"]) == Decimal("4.00")
    assert t["courses"][1]["grade"] is None


def test_no_graded_courses_gives_null_gpa(client, world, login):
    t = client.get("/students/me/transcript", headers=login("s1@test.com")).json()
    assert t["gpa"] is None and t["courses"] == []


def test_regrading_overwrites_instead_of_duplicating(client, world, login):
    s1, lec1 = login("s1@test.com"), login("lec1@test.com")
    _register(client, s1, world.c1)
    _grade(client, lec1, world.c1, world.s1, 50)
    _grade(client, lec1, world.c1, world.s1, 90)
    t = client.get("/students/me/transcript", headers=s1).json()
    assert len(t["courses"]) == 1 and Decimal(t["courses"][0]["score"]) == Decimal("90")


def test_duplicate_registration_is_409(client, world, login):
    s1 = login("s1@test.com")
    assert _register(client, s1, world.c1).status_code == 201
    assert _register(client, s1, world.c1).status_code == 409


def test_can_drop_ungraded_but_not_graded_course(client, world, login):
    s1 = login("s1@test.com")
    _register(client, s1, world.c1)
    _register(client, s1, world.c2)
    _grade(client, login("lec1@test.com"), world.c1, world.s1, 60)
    assert client.delete(f"/courses/{world.c2}/register", headers=s1).status_code == 204
    assert client.delete(f"/courses/{world.c1}/register", headers=s1).status_code == 409


def test_cannot_grade_unregistered_student(client, world, login):
    r = _grade(client, login("lec1@test.com"), world.c1, world.s2, 70)
    assert r.status_code == 404


def test_score_out_of_range_is_422(client, world, login):
    s1 = login("s1@test.com")
    _register(client, s1, world.c1)
    r = _grade(client, login("lec1@test.com"), world.c1, world.s1, 101)
    assert r.status_code == 422


def test_admin_links_student_profile_once(client, world, login):
    uid = client.post(
        "/auth/register", json={"email": "new@test.com", "password": "Password123"}
    ).json()["id"]
    admin = login("admin@test.com")
    body = {"user_id": uid, "matric_number": "MAT900", "first_name": "New", "last_name": "Student"}
    assert client.post("/students", json=body, headers=admin).status_code == 201
    assert client.post("/students", json=body, headers=admin).status_code == 409


def test_search_students(client, world, login):
    admin = login("admin@test.com")
    found = client.get("/students", params={"q": "MAT001"}, headers=admin).json()
    assert [s["id"] for s in found] == [world.s1]


def test_course_crud(client, world, login):
    admin = login("admin@test.com")
    r = client.post("/courses", json={"code": "mth101", "title": "Maths", "credit_units": 2}, headers=admin)
    assert r.status_code == 201 and r.json()["code"] == "MTH101"
    cid = r.json()["id"]
    dup = client.post("/courses", json={"code": "MTH101", "title": "Again", "credit_units": 2}, headers=admin)
    assert dup.status_code == 409
    assert client.patch(f"/courses/{cid}", json={"title": "Maths I"}, headers=admin).json()["title"] == "Maths I"
    assert client.delete(f"/courses/{cid}", headers=admin).status_code == 204


def test_cannot_delete_course_with_registrations(client, world, login):
    _register(client, login("s1@test.com"), world.c1)
    r = client.delete(f"/courses/{world.c1}", headers=login("admin@test.com"))
    assert r.status_code == 409


def test_missing_resource_uses_consistent_error_shape(client, world, login):
    r = client.get("/courses/9999", headers=login("s1@test.com"))
    assert r.status_code == 404
    assert r.json() == {"error": {"code": "not_found", "message": "Course not found"}}