import smtplib
from dotenv import load_dotenv
import os
from email.mime.text import MIMEText 
from db import get_users, check_changes, update_grades, update_last_checked
from cu_scraper import info
import asyncio
load_dotenv()

def send_welcome_email(email, username):
    subject = "CU Scraper - Welcome Message"
    body = f"""Dear {username},

Thank you for subscribing to automatic grade updates on the CU Scraper Website.
You will now be notified whenever one of your grades update on the Carleton Central Website."""

    sender = os.getenv("GOOGLE_EMAIL")
    password = os.getenv("GOOGLE_PASSWORD")
    assert sender and password, "email credentials not found in .env"

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
        smtp_server.login(sender, password)
        smtp_server.sendmail(sender, email, msg.as_string())
    print("Welcome message sent!")

def send_grade_change_email(email, changes):
    subject = "CU Scraper - Grade Update"
    header = "The following grades have been updated:\n"


    lines = []
    for term in changes:
        lines.append(f"Term: {term}")
        for course in changes[term]:
            lines.append(f"- {course['subject']} {course['course']}: {course['finalgrade']}")
    body = header + "\n".join(lines)

    sender = os.getenv("GOOGLE_EMAIL")
    password = os.getenv("GOOGLE_PASSWORD")
    assert sender and password, "email credentials not found in .env"

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = email

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
        smtp_server.login(sender, password)
        smtp_server.sendmail(sender, email, msg.as_string())
    print("Grades update email sent!")

def send_email_changed_old(old_email, username):
    subject = "CU Scraper - Notification Email Changed"
    body = f"""Dear {username},

Your grade notification email has been updated. You will no longer receive grade updates at this address.

If you did not make this change, please contact us immediately."""

    sender = os.getenv("GOOGLE_EMAIL")
    password = os.getenv("GOOGLE_PASSWORD")
    assert sender and password, "email credentials not found in .env"

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = old_email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
        smtp_server.login(sender, password)
        smtp_server.sendmail(sender, old_email, msg.as_string())
    print("Email changed notification sent to old email!")

def send_email_changed_new(new_email, username):
    subject = "CU Scraper - You're now subscribed"
    body = f"""Dear {username},

This email has been set as the new destination for your CU Scraper grade notifications.

You will now receive an email at this address whenever one of your grades updates on the Carleton Central Website."""

    sender = os.getenv("GOOGLE_EMAIL")
    password = os.getenv("GOOGLE_PASSWORD")
    assert sender and password, "email credentials not found in .env"

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = new_email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
        smtp_server.login(sender, password)
        smtp_server.sendmail(sender, new_email, msg.as_string())
    print("Subscription email sent to new email!")

def send_goodbye_email(email, username):
    subject = "CU Scraper - Account Deleted"
    body = f"""Dear {username},

Your CU Scraper account has been successfully deleted. You will no longer receive grade update notifications."""

    sender = os.getenv("GOOGLE_EMAIL")
    password = os.getenv("GOOGLE_PASSWORD")
    assert sender and password, "email credentials not found in .env"

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = email

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
        smtp_server.login(sender, password)
        smtp_server.sendmail(sender, email, msg.as_string())
    print("Goodbye email sent!")

async def scrape_user(user, sem):
    user_id = user["user_id"]
    username = user["username"]
    password = user["password"]
    email = user["email"]
    async with sem: 
        result = await info(username, password)
        if result is None:
            return "user not found" 
        _,_,_,_, fresh_courses,_ = result
    changes = await check_changes(user_id, fresh_courses)
    if changes:
        send_grade_change_email(email, changes)
        await update_grades(user_id, changes)
    await update_last_checked(user_id)

sem = asyncio.Semaphore(3)
async def poll():
    while True:
        failed = []
        users = await get_users()
        results = await asyncio.gather(*[scrape_user(user, sem) for user in users], return_exceptions=True)
        for user, result in zip(users, results):
            if isinstance(result, Exception):
                failed.append(user)
        if failed:
            results = await asyncio.gather(*[scrape_user(user, sem) for user in failed], return_exceptions=True)
            for r in results:
                if isinstance(r, Exception):
                    print(f"scrape failed: {r}")

        
        await asyncio.sleep(1800)

if __name__ == "__main__":
    asyncio.run(poll())


