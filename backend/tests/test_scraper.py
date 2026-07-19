from pathlib import Path

from cu_scraper import parse_grades_page

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_grades_page_extracts_student_identity():
    html = (FIXTURES / "grades_page.html").read_text()
    student_name, student_number, info, _, _ = parse_grades_page(html)

    assert student_name == "John Doe"
    assert student_number == "100000000"
    assert info == {"studentnumber": "100000000", "studentname": "John Doe"}


def test_parse_grades_page_extracts_all_courses():
    html = (FIXTURES / "grades_page.html").read_text()
    _, _, _, courses, _ = parse_grades_page(html)

    assert len(courses) == 14


def test_parse_grades_page_extracts_course_fields():
    html = (FIXTURES / "grades_page.html").read_text()
    _, _, _, courses, _ = parse_grades_page(html)

    first = courses[0]
    assert first["crn"] == "30001"
    assert first["subject"] == "CHEM"
    assert first["course"] == "1101"
    assert first["section"] == "A"
    assert first["coursetitle"] == "Chemistry for Engineering Students"
    assert first["campus"] == "Main Campus"
    assert first["finalgrade"] == "A+"
    assert first["attempted"] == "0.500"
    assert first["earned"] == "0.500"
    assert first["gpahours"] == "0.500"
    assert first["qualitypoints"] == "6.00"


def test_parse_grades_page_handles_full_grade_scale():
    html = (FIXTURES / "grades_page.html").read_text()
    _, _, _, courses, _ = parse_grades_page(html)

    grades = [c["finalgrade"] for c in courses]
    assert grades == [
        "A+", "A", "A-", "B+", "B", "B-",
        "C+", "C", "C-", "D+", "D", "D-",
        "F", "SAT",
    ]


def test_parse_grades_page_extracts_failed_course():
    html = (FIXTURES / "grades_page.html").read_text()
    _, _, _, courses, _ = parse_grades_page(html)

    failed = next(c for c in courses if c["finalgrade"] == "F")
    assert failed["subject"] == "PHIL"
    assert failed["earned"] == "0.000"
    assert failed["attempted"] == "0.500"


def test_parse_grades_page_extracts_program():
    html = (FIXTURES / "grades_page.html").read_text()
    _, _, _, _, program = parse_grades_page(html)

    assert program["currentprogram"] == "Bachelor of Engineering"
    assert program["level"] == "Undergraduate"
    assert program["program"] == "Software Engineering"
    assert program["major"] == "Software Engineering"
    assert program["concentration"] == "Co-operative Option"
    assert program["academicstanding"] == "No Assessment"
