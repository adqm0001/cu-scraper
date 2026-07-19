from db import diff_grades


def course(crn, subject="ECOR", num="1031", grade="A"):
    return {
        "crn": crn,
        "subject": subject,
        "course": num,
        "section": "A",
        "coursetitle": "Test",
        "finalgrade": grade,
        "attempted": "0.500",
        "earned": "0.500",
        "gpahours": "0.500",
        "qualitypoints": "6.00",
    }


def test_diff_no_changes_returns_empty():
    grades = {"202530": [course("30001", grade="A+")]}

    changes, deletions = diff_grades(grades, grades)

    assert changes == {}
    assert deletions == []


def test_diff_detects_grade_change():
    old = {"202530": [course("30001", grade="B")]}
    new = {"202530": [course("30001", grade="A+")]}

    changes, deletions = diff_grades(old, new)

    assert changes == {"202530": [course("30001", grade="A+")]}
    assert deletions == []


def test_diff_detects_new_course_in_existing_term():
    old = {"202530": [course("30001", grade="A")]}
    new = {
        "202530": [
            course("30001", grade="A"),
            course("30002", subject="MATH", grade="B+"),
        ],
    }

    changes, deletions = diff_grades(old, new)

    assert changes == {"202530": [course("30002", subject="MATH", grade="B+")]}
    assert deletions == []


def test_diff_detects_removed_course():
    old = {
        "202530": [
            course("30001", grade="A"),
            course("30002", subject="MATH", grade="B"),
        ],
    }
    new = {"202530": [course("30001", grade="A")]}

    changes, deletions = diff_grades(old, new)

    assert changes == {}
    assert deletions == [("202530", "30002")]


def test_diff_detects_entirely_new_term():
    old = {"202530": [course("30001", grade="A")]}
    new = {
        "202530": [course("30001", grade="A")],
        "202610": [course("40001", subject="PHYS", grade="B+")],
    }

    changes, deletions = diff_grades(old, new)

    assert changes == {
        "202610": [course("40001", subject="PHYS", grade="B+")],
    }
    assert deletions == []


def test_diff_term_in_db_but_not_fresh_is_ignored():
    old = {
        "202430": [course("20001", grade="A")],
        "202530": [course("30001", grade="A")],
    }
    new = {"202530": [course("30001", grade="A")]}

    changes, deletions = diff_grades(old, new)

    assert changes == {}
    assert deletions == []


def test_diff_multiple_changes_at_once():
    old = {
        "202530": [
            course("30001", grade="B"),
            course("30002", subject="MATH", grade="A"),
            course("30003", subject="PHYS", grade="C"),
        ],
    }
    new = {
        "202530": [
            course("30001", grade="A+"),
            course("30002", subject="MATH", grade="A"),
            course("30004", subject="CHEM", grade="B+"),
        ],
    }

    changes, deletions = diff_grades(old, new)

    assert changes == {
        "202530": [
            course("30001", grade="A+"),
            course("30004", subject="CHEM", grade="B+"),
        ],
    }
    assert deletions == [("202530", "30003")]


def test_diff_ignores_non_grade_field_changes():
    old = {"202530": [course("30001", grade="A")]}
    new_course = course("30001", grade="A")
    new_course["qualitypoints"] = "99.99"
    new = {"202530": [new_course]}

    changes, deletions = diff_grades(old, new)

    assert changes == {}
    assert deletions == []
