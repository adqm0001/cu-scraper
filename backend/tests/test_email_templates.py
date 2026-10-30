import unittest
from email import policy
from email.parser import Parser

from email_templates import build_grade_email_html, create_email_message, format_term


class GradeEmailTests(unittest.TestCase):
    def setUp(self):
        self.changes = {
            "202430": [
                {"subject": "ECOR", "course": "1031", "finalgrade": "A"},
                {"subject": "MATH", "course": "1007", "finalgrade": "A+"},
            ],
            "202510": [{"subject": "COMP", "course": "2401", "finalgrade": "A-"}],
        }
        self.base = "https://grades.example.com"
        self.unsubscribe = self.base + "/unsubscribe?token=sample&source=email"

    def test_multiple_terms_and_all_courses_are_rendered(self):
        html = build_grade_email_html(self.changes, self.base, self.unsubscribe, "jdoe")
        self.assertIn("Fall 2024", html)
        self.assertIn("Winter 2025", html)
        for code in ("ECOR 1031", "MATH 1007", "COMP 2401"):
            self.assertEqual(html.count(code), 1)
        self.assertIn("Hi jdoe,", html)
        self.assertIn(self.base + "/app/dashboard", html)
        self.assertIn(self.base + "/app/profile", html)
        self.assertIn("Unsubscribe from grade updates", html)
        self.assertIn("token=sample&amp;source=email", html)

    def test_unknown_terms_and_blank_grades_are_readable(self):
        html = build_grade_email_html({"custom term": [{"subject": "ECOR", "course": "1031", "finalgrade": ""}]}, self.base)
        self.assertIn("custom term", html)
        self.assertIn("Not yet posted", html)
        self.assertEqual(format_term("202420"), "Summer 2024")

    def test_untrusted_values_are_escaped(self):
        changes = {'<img src=x>': [{"subject": '<script>alert(1)</script>', "course": '"1031"', "finalgrade": '<b>A</b>'}]}
        html = build_grade_email_html(changes, self.base, username='<img src=x onerror=alert(1)>')
        self.assertNotIn("<script>", html)
        self.assertNotIn("<img", html)
        self.assertNotIn("<b>A</b>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("&lt;b&gt;A&lt;/b&gt;", html)

    def test_unsafe_links_are_rejected(self):
        with self.assertRaises(ValueError):
            build_grade_email_html(self.changes, self.base, "javascript:alert(1)")
        with self.assertRaises(ValueError):
            build_grade_email_html(self.changes, "javascript:alert(1)")

    def test_text_and_html_become_a_multipart_message(self):
        text = "The following grades have been updated:\nTerm: 202430\n- ECOR 1031: A\n" + self.unsubscribe
        html = build_grade_email_html(self.changes, self.base, self.unsubscribe)
        message = create_email_message("student@example.com", "sender@example.com", "CU Scraper - Grade Update", text, html)
        decoded = Parser(policy=policy.default).parsestr(message.as_string())
        self.assertEqual(decoded.get_content_type(), "multipart/alternative")
        self.assertEqual([part.get_content_type() for part in decoded.iter_parts()], ["text/plain", "text/html"])
        self.assertEqual(decoded.get_body(preferencelist=("plain",)).get_content().strip(), text.strip())
        self.assertEqual(decoded.get_body(preferencelist=("html",)).get_content().strip(), html.strip())
        self.assertEqual(decoded["To"], "student@example.com")

    def test_text_only_message_has_no_html_part(self):
        message = create_email_message("student@example.com", "sender@example.com", "Old queued email", "An existing plain-text email", None)
        self.assertEqual(message.get_content_type(), "text/plain")
        self.assertEqual(message.get_content().strip(), "An existing plain-text email")

    def test_optional_links_and_greeting(self):
        html = build_grade_email_html({}, self.base)
        self.assertIn("Hi there,", html)
        self.assertNotIn("Unsubscribe from grade updates", html)
        self.assertNotIn("$", html)


if __name__ == "__main__":
    unittest.main()
