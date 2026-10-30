import asyncio
import smtplib

import poller
from poller import retry_delay, deliver_pending_emails


def pending(email_id=1, attempts=0):
    return {"id": email_id, "user_id": 7, "recipient": "j@example.com", "subject": "s", "body": "b", "attempts": attempts}


def record(calls, name):
    async def _fn(*args):
        calls.append((name, *args))
    return _fn


def setup_outbox(monkeypatch, emails, send):
    calls = []

    async def due():
        return emails

    monkeypatch.setattr(poller, "get_due_emails", due)
    monkeypatch.setattr(poller, "send_email", send)
    monkeypatch.setattr(poller, "mark_email_sent", record(calls, "sent"))
    monkeypatch.setattr(poller, "mark_email_retry", record(calls, "retry"))
    monkeypatch.setattr(poller, "mark_email_failed", record(calls, "failed"))
    monkeypatch.setattr(poller, "alert_discord", record(calls, "discord"))
    return calls


def failing_send(*args):
    raise smtplib.SMTPException("boom")


def test_retry_delay_backs_off_then_gives_up():
    assert retry_delay(0) == 60
    assert retry_delay(4) == 10800
    assert retry_delay(5) is None


def test_successful_send_marks_email_sent(monkeypatch):
    calls = setup_outbox(monkeypatch, [pending()], lambda *a: None)

    asyncio.run(deliver_pending_emails())

    assert calls == [("sent", 1)]


def test_failed_send_schedules_retry(monkeypatch):
    calls = setup_outbox(monkeypatch, [pending(attempts=0)], failing_send)

    asyncio.run(deliver_pending_emails())

    assert calls == [("retry", 1, 60, "SMTPException")]


def test_final_failure_gives_up_and_alerts(monkeypatch):
    calls = setup_outbox(monkeypatch, [pending(attempts=5)], failing_send)

    asyncio.run(deliver_pending_emails())

    assert calls[0] == ("failed", 1, "SMTPException")
    assert calls[1][0] == "discord"
    assert "j@example.com" not in calls[1][1]


def test_one_failure_does_not_block_other_emails(monkeypatch):
    def send(to, subject, body):
        if to == "bad@example.com":
            raise smtplib.SMTPException("boom")

    bad = {**pending(1), "recipient": "bad@example.com"}
    calls = setup_outbox(monkeypatch, [bad, pending(2)], send)

    asyncio.run(deliver_pending_emails())

    assert ("retry", 1, 60, "SMTPException") in calls
    assert ("sent", 2) in calls
