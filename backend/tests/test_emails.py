from poller import (
    build_welcome_email,
    build_grade_change_email,
    build_email_changed_old_email,
    build_email_changed_new_email,
    build_goodbye_email,
)


def test_build_welcome_email():
    subject, body = build_welcome_email("jdoe")

    assert subject == "CU Scraper - Welcome Message"
    assert "Dear jdoe," in body
    assert "automatic grade updates" in body


def test_build_goodbye_email():
    subject, body = build_goodbye_email("jdoe")

    assert subject == "CU Scraper - Account Deleted"
    assert "Dear jdoe," in body
    assert "successfully deleted" in body


def test_build_email_changed_old_email():
    subject, body = build_email_changed_old_email("jdoe")

    assert subject == "CU Scraper - Notification Email Changed"
    assert "Dear jdoe," in body
    assert "no longer receive" in body


def test_build_email_changed_new_email():
    subject, body = build_email_changed_new_email("jdoe")

    assert subject == "CU Scraper - You're now subscribed"
    assert "Dear jdoe," in body
    assert "new destination" in body


def test_build_grade_change_email_single_course():
    changes = {
        "202530": [
            {"subject": "ECOR", "course": "1031", "finalgrade": "A+"},
        ],
    }
    subject, body = build_grade_change_email(changes)

    assert subject == "CU Scraper - Grade Update"
    assert "Term: 202530" in body
    assert "- ECOR 1031: A+" in body


def test_build_grade_change_email_multiple_terms():
    changes = {
        "202530": [
            {"subject": "ECOR", "course": "1031", "finalgrade": "A+"},
            {"subject": "MATH", "course": "1004", "finalgrade": "B"},
        ],
        "202610": [
            {"subject": "PHYS", "course": "1003", "finalgrade": "A"},
        ],
    }
    _, body = build_grade_change_email(changes)

    assert "Term: 202530" in body
    assert "- ECOR 1031: A+" in body
    assert "- MATH 1004: B" in body
    assert "Term: 202610" in body
    assert "- PHYS 1003: A" in body


def test_build_grade_change_email_empty_changes():
    subject, body = build_grade_change_email({})

    assert subject == "CU Scraper - Grade Update"
    assert body == "The following grades have been updated:\n"


def test_grade_notification_uses_html_and_plain_text():
    from poller import build_grade_change_notification
    from email_templates import create_email_message

    changes = {"202530": [{"subject": "ECOR", "course": "1031", "finalgrade": "A+"}]}
    subject, text, html_body = build_grade_change_notification(changes, "https://example.com/unsubscribe?token=abc", "jdoe")
    assert "<" not in text
    message = create_email_message("j@example.com", "sender@example.com", subject, text, html_body)
    assert message.get_content_type() == "multipart/alternative"
    assert "- ECOR 1031: A+" in message.get_body(preferencelist=("plain",)).get_content()
    html = message.get_body(preferencelist=("html",)).get_content()
    assert "Fall 2025" in html
    assert "Hi jdoe," in html
    assert "https://example.com/unsubscribe?token=abc" in html


def test_send_email_passes_both_versions_to_smtp(monkeypatch):
    import poller
    from email import policy
    from email.parser import Parser

    sent = []

    class FakeSMTP:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def login(self, *args):
            pass

        def sendmail(self, sender, recipient, message):
            sent.append(message)

    monkeypatch.setenv("GOOGLE_EMAIL", "sender@example.com")
    monkeypatch.setenv("GOOGLE_PASSWORD", "test-only")
    monkeypatch.setattr(poller.smtplib, "SMTP_SSL", FakeSMTP)
    poller.send_email("j@example.com", "Grade Update", "Plain grades", "<p>HTML grades</p>")
    parsed = Parser(policy=policy.default).parsestr(sent[0])
    assert parsed.get_body(preferencelist=("plain",)).get_content().strip() == "Plain grades"
    assert parsed.get_body(preferencelist=("html",)).get_content().strip() == "<p>HTML grades</p>"
