import smtplib
from dotenv import load_dotenv
import os
from email.mime.text import MIMEText 
from db import get_users, get_grades, check_changes, update_grades
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
    print("Message sent!")

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
    print("Message sent!")

async def poll():
    while True:
        users = await get_users()
        for user in users:
            # scrape, check, email, update
            user_id = user["user_id"]
            username = user["username"]
            password = user["password"]
            email = user["email"]
            result = await info(username, password)
            if result is None:
                continue
            _,_,_,_, fresh_courses = result
            changes = await check_changes(user_id, fresh_courses)
            if changes:
                send_grade_change_email(email, changes)
                await update_grades(user_id, changes)


        await asyncio.sleep(1800)

if __name__ == "__main__":
    asyncio.run(poll())


