from email.message import EmailMessage
from html import escape
from pathlib import Path
from string import Template
from urllib.parse import urlsplit

TEMPLATE = Template((Path(__file__).parent / "templates" / "grade_update.html").read_text(encoding="utf-8"))


def format_term(term) -> str:
    code = str(term)
    seasons = {"10": "Winter", "20": "Summer", "30": "Fall"}
    if len(code) == 6 and code.isdigit() and code[4:] in seasons:
        return f"{seasons[code[4:]]} {code[:4]}"
    return code


def safe_link(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme not in ("https", "http") or not parsed.netloc:
        raise ValueError("Email links must use an absolute HTTP or HTTPS URL")
    return escape(url, quote=True)


def build_grade_email_html(changes: dict, frontend_url: str, unsubscribe_link: str | None = None, username: str | None = None) -> str:
    rows = []
    for term, courses in changes.items():
        if not courses:
            continue
        rows.append(f'<tr><th scope="colgroup" colspan="2" style="text-align:left;font-size:14px;color:#555b65;padding:20px 0 11px;border-bottom:1px solid #d9dce1;">{escape(format_term(term))}</th></tr>')
        for course in courses:
            code = escape(f"{course['subject']} {course['course']}")
            grade = escape(str(course.get("finalgrade") or "Not yet posted"))
            rows.append(f'<tr><td style="padding:15px 0;font-size:16px;border-bottom:1px solid #efeff1;">{code}</td><td style="padding:15px 0;text-align:right;font-size:17px;font-weight:700;border-bottom:1px solid #efeff1;">{grade}</td></tr>')
    unsubscribe_footer = ""
    if unsubscribe_link:
        unsubscribe_footer = f'<br><a href="{safe_link(unsubscribe_link)}" style="color:#555b65;text-decoration:underline;">Unsubscribe from grade updates</a>'
    base = frontend_url.rstrip("/")
    return TEMPLATE.substitute(
        greeting=f"Hi {escape(str(username))}," if username else "Hi there,",
        term_rows="\n".join(rows),
        dashboard_url=safe_link(f"{base}/app/dashboard"),
        account_url=safe_link(f"{base}/app/profile"),
        unsubscribe_footer=unsubscribe_footer,
    )


def create_email_message(recipient: str, sender: str, subject: str, text: str, html: str | None = None) -> EmailMessage:
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = recipient
    message.set_content(text)
    if html:
        message.add_alternative(html, subtype="html")
    return message
