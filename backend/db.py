from cu_scraper import info
import psycopg
from dotenv import load_dotenv
import os
from cryptography.fernet import Fernet
import bcrypt
from datetime import datetime, timezone
load_dotenv()

key = os.getenv("FERNET_KEY")
db = os.getenv("DATABASE_URL")
assert db, "Database not found in .env"
assert key, "Key not found in .env"
fernet = Fernet(key)

async def register(username: str, password: str, email: str):
    async with await psycopg.AsyncConnection.connect(db) as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT 1 FROM users WHERE username = %s", (username,))
            if await cur.fetchone() is not None:
                return "username already exists"

    result_info = await info(username, password)
    if not result_info:
        return "invalid credentials"

    enc_password = fernet.encrypt(password.encode()).decode()
    enc_email = fernet.encrypt(email.encode()).decode()
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    async with await psycopg.AsyncConnection.connect(db) as conn:
        async with conn.cursor() as cur:

            await cur.execute("""
                INSERT INTO users (
                username, password, email, hashed_password)
                VALUES (
                %s , %s, %s, %s)
                ON CONFLICT (username) DO NOTHING
                RETURNING user_id
                """,
                (username, enc_password, enc_email, hashed_password.decode()))

            row = await cur.fetchone()
            if row is None:
                return "username already exists"
            user_id = row[0]

        await conn.commit()

    return user_id, result_info

async def fetch_and_store_grades(user_id: str, result_info):
    if result_info is None:
        return "invalid credentials"
    _,_,_,_, all_courses,_ = result_info
    
    async with await psycopg.AsyncConnection.connect(db) as conn:
        async with conn.cursor() as cur:
            for term_code, courses in all_courses.items():
                await cur.execute("""
                    INSERT INTO terms (
                    user_id, term_code) VALUES (
                    %s, %s) 
                    ON CONFLICT (user_id, term_code) DO UPDATE SET term_code = EXCLUDED.term_code 
                    RETURNING term_id
                    """,
                    (user_id, term_code))
                row = await cur.fetchone()
                if row is None:
                    return "Error while fetching."
                term_id = row[0]
            
                for course in courses:
                    enc_grade = fernet.encrypt(course["finalgrade"].encode()).decode()
                    enc_attempted = fernet.encrypt(course["attempted"].encode()).decode()
                    enc_earned = fernet.encrypt(course["earned"].encode()).decode()
                    enc_gpahours = fernet.encrypt(course["gpahours"].encode()).decode()
                    enc_qualitypoints = fernet.encrypt(course["qualitypoints"].encode()).decode()
                    await cur.execute("""
                        INSERT INTO courses (
                        term_id, crn, subject, course, section, coursetitle, finalgrade, attempted, earned, gpahours, qualitypoints) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s , %s, %s, %s)
                        ON CONFLICT (term_id, crn) DO NOTHING
                        """,
                        (term_id, course["crn"], course["subject"], course["course"], course["section"], course["coursetitle"], enc_grade, enc_attempted, enc_earned, enc_gpahours, enc_qualitypoints))

            await cur.execute("UPDATE users SET last_updated = NOW() WHERE user_id = %s", (user_id,))

        await conn.commit()

async def get_user_credentials(user_id: str):
    async with await psycopg.AsyncConnection.connect(db) as conn:
        async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT username, password, email, is_test, grade_emails_enabled
                    FROM users
                    WHERE user_id = %s
                    """,
                    (user_id,))

                row = await cur.fetchone()
                if row is None:
                    return "user_id not found"
    return {"username": row[0], "password": fernet.decrypt(row[1].encode()).decode(), "email": fernet.decrypt(row[2].encode()).decode(), "is_test": row[3], "grade_emails_enabled": row[4]}


async def get_grades(user_id: str, term_code=None):
    async with await psycopg.AsyncConnection.connect(db) as conn:
        async with conn.cursor() as cur:

            base = """
                SELECT terms.term_code, crn, subject, course, section, coursetitle, finalgrade, attempted, earned, gpahours, qualitypoints
                FROM courses
                JOIN terms ON courses.term_id = terms.term_id
                WHERE terms.user_id = %s
            """

            if term_code:
                query = base + "AND terms.term_code = %s"
                params = (user_id, term_code)
            else:
                query = base
                params = (user_id,)

                
            await cur.execute(query, params)
            rows = await cur.fetchall()
            
            grades = {}
            for row in rows:
                if row[0] not in grades:
                    grades[row[0]] = []
                grades[row[0]].append({
                    "crn": row[1],
                    "subject": row[2],
                    "course": row[3],
                    "section": row[4],
                    "coursetitle": row[5],
                    "finalgrade": fernet.decrypt(row[6].encode()).decode(),
                    "attempted": fernet.decrypt(row[7].encode()).decode(),
                    "earned": fernet.decrypt(row[8].encode()).decode(),
                    "gpahours": fernet.decrypt(row[9].encode()).decode(),
                    "qualitypoints": fernet.decrypt(row[10].encode()).decode(),
                })

            await cur.execute("SELECT last_updated FROM users WHERE user_id = %s", (user_id,))
            row = await cur.fetchone()
            if row is None:
                raise Exception("Last updated update failed!")
            last_updated = to_utc_iso(row[0])

            return grades, last_updated

def to_utc_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()

def diff_grades(db_grades: dict, fresh_courses: dict) -> tuple[dict, list]:
    changes: dict = {}
    deletions: list = []

    for term in db_grades:
        if term not in fresh_courses:
            continue
        if db_grades[term] == fresh_courses[term]:
            continue

        for fresh_course in fresh_courses[term]:
            match = next(
                (c for c in db_grades[term] if c["crn"] == fresh_course["crn"]),
                None,
            )
            if match is None:
                changes.setdefault(term, []).append(fresh_course)
            elif match["finalgrade"] != fresh_course["finalgrade"]:
                changes.setdefault(term, []).append(fresh_course)

        for db_course in db_grades[term]:
            in_fresh = any(fc["crn"] == db_course["crn"] for fc in fresh_courses[term])
            if not in_fresh:
                deletions.append((term, db_course["crn"]))

    for term in fresh_courses:
        if term not in db_grades:
            changes[term] = fresh_courses[term]

    return changes, deletions


async def check_changes(user_id: str, fresh_courses: dict):
    db_grades, _ = await get_grades(user_id)
    changes, deletions = diff_grades(db_grades, fresh_courses)
    for term, crn in deletions:
        await delete_course(user_id, term, crn)
    return changes

def _encrypt(value: str | None) -> str | None:
    return fernet.encrypt(value.encode()).decode() if value is not None else None

def _decrypt(value: str | None) -> str | None:
    return fernet.decrypt(value.encode()).decode() if value is not None else None

async def update_grades(user_id: str, courses: dict, notification: tuple[str, str, str, str | None] | None = None):
    async with await psycopg.AsyncConnection.connect(db) as conn:
        async with conn.cursor() as cur:

            for term in courses: 
                await cur.execute("""
                    INSERT INTO terms (user_id, term_code)
                    VALUES (%s, %s)
                    ON CONFLICT (user_id, term_code) DO UPDATE SET term_code = EXCLUDED.term_code
                    RETURNING term_id
                    """, (user_id, term))
                row = await cur.fetchone()
                term_id = row[0]

                for course in courses[term]:
                    enc_grade = fernet.encrypt(course["finalgrade"].encode()).decode()
                    enc_attempted = fernet.encrypt(course["attempted"].encode()).decode()
                    enc_earned = fernet.encrypt(course["earned"].encode()).decode()
                    enc_gpahours = fernet.encrypt(course["gpahours"].encode()).decode()
                    enc_qualitypoints = fernet.encrypt(course["qualitypoints"].encode()).decode()
                    await cur.execute("""
                        INSERT INTO courses (
                        term_id, crn, subject, course, section, coursetitle, finalgrade, attempted, earned, gpahours, qualitypoints)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (term_id, crn) DO UPDATE SET
                        finalgrade = EXCLUDED.finalgrade,
                        attempted = EXCLUDED.attempted,
                        earned = EXCLUDED.earned,
                        gpahours = EXCLUDED.gpahours,
                        qualitypoints = EXCLUDED.qualitypoints
                    """, (term_id, course["crn"], course["subject"], course["course"], course["section"], course["coursetitle"], enc_grade, enc_attempted, enc_earned, enc_gpahours, enc_qualitypoints))

            if notification:
                recipient, subject, body, html_body = notification
                await cur.execute("""
                    INSERT INTO email_outbox (user_id, kind, recipient, subject, body, html_body)
                    SELECT %s, 'grade_change', %s, %s, %s, %s
                    WHERE EXISTS (SELECT 1 FROM users WHERE user_id = %s AND grade_emails_enabled)
                    """,
                    (user_id, _encrypt(recipient), _encrypt(subject), _encrypt(body), _encrypt(html_body), user_id),
                )

        await conn.commit()

async def get_due_emails(limit: int = 20):
    async with await psycopg.AsyncConnection.connect(db) as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT o.id, o.user_id, o.recipient, o.subject, o.body, o.html_body, o.attempts
                FROM email_outbox o
                JOIN users u ON u.user_id = o.user_id
                WHERE o.sent_at IS NULL AND o.failed_at IS NULL AND o.cancelled_at IS NULL
                  AND o.next_attempt_at <= NOW()
                  AND (o.kind <> 'grade_change' OR u.grade_emails_enabled)
                ORDER BY o.id
                LIMIT %s
                """, (limit,))
            rows = await cur.fetchall()
    return [
        {
            "id": row[0],
            "user_id": row[1],
            "recipient": _decrypt(row[2]),
            "subject": _decrypt(row[3]),
            "body": _decrypt(row[4]),
            "html": _decrypt(row[5]),
            "attempts": row[6],
        }
        for row in rows
    ]

async def set_grade_emails(user_id: str, enabled: bool) -> bool:
    async with await psycopg.AsyncConnection.connect(db) as conn:
        async with conn.cursor() as cur:
            await cur.execute("UPDATE users SET grade_emails_enabled = %s WHERE user_id = %s", (enabled, user_id))
            if cur.rowcount == 0:
                return False
            await cur.execute("""
                UPDATE email_outbox SET cancelled_at = NOW()
                WHERE user_id = %s AND kind = 'grade_change'
                  AND sent_at IS NULL AND failed_at IS NULL AND cancelled_at IS NULL
                """, (user_id,))
        await conn.commit()
    return True

async def mark_email_sent(email_id: int):
    async with await psycopg.AsyncConnection.connect(db) as conn:
        async with conn.cursor() as cur:
            await cur.execute("UPDATE email_outbox SET sent_at = NOW(), attempts = attempts + 1 WHERE id = %s", (email_id,))
            await conn.commit()

async def mark_email_retry(email_id: int, delay_seconds: int, error: str):
    async with await psycopg.AsyncConnection.connect(db) as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                UPDATE email_outbox
                SET attempts = attempts + 1, last_error = %s, next_attempt_at = NOW() + make_interval(secs => %s)
                WHERE id = %s
                """, (error, delay_seconds, email_id))
            await conn.commit()

async def mark_email_failed(email_id: int, error: str):
    async with await psycopg.AsyncConnection.connect(db) as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE email_outbox SET attempts = attempts + 1, last_error = %s, failed_at = NOW() WHERE id = %s",
                (error, email_id),
            )
            await conn.commit()

async def update_email(user_id: str, new_email: str):
    enc_email = fernet.encrypt(new_email.encode()).decode()
    async with await psycopg.AsyncConnection.connect(db) as conn:
        async with conn.cursor() as cur:
            await cur.execute("UPDATE users SET email = %s WHERE user_id = %s", (enc_email, user_id))
            await conn.commit()

async def update_password(user_id: str, new_password: str):
    enc_password = fernet.encrypt(new_password.encode()).decode()
    hashed_password = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    async with await psycopg.AsyncConnection.connect(db) as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE users SET password = %s, hashed_password = %s WHERE user_id = %s",
                (enc_password, hashed_password, user_id),
            )
            await conn.commit()

async def update_last_checked(user_id: str):
    async with await psycopg.AsyncConnection.connect(db) as conn:
        async with conn.cursor() as cur:
            await cur.execute("UPDATE users SET last_updated = NOW() WHERE user_id = %s", (user_id,))
            await conn.commit()

async def get_user(username: str):
    async with await psycopg.AsyncConnection.connect(db) as conn:
        async with conn.cursor() as cur:

            await cur.execute("""
                SELECT user_id, hashed_password
                FROM users
                WHERE username = %s
                """, (username,))

            row = await cur.fetchone()
            if row is None:
                return "username not found"
            return {"user_id": row[0], "hashed_password": row[1]}

async def get_demo_user_id(username: str):
    async with await psycopg.AsyncConnection.connect(db) as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT user_id FROM users WHERE username = %s AND is_test = true", (username,))
            row = await cur.fetchone()
            return row[0] if row else None

async def verify_user_password(user_id: str, plaintext: str) -> bool:
    async with await psycopg.AsyncConnection.connect(db) as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT hashed_password FROM users WHERE user_id = %s", (user_id,))
            row = await cur.fetchone()
            if row is None:
                return False
            return bcrypt.checkpw(plaintext.encode(), row[0].encode())

async def get_users():
    async with await psycopg.AsyncConnection.connect(db) as conn: 
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT user_id, username, password, email from users
                WHERE is_test = false AND grade_emails_enabled = true
                """)

            rows = await cur.fetchall()

            return [{"user_id": row[0], "username": row[1], "password": fernet.decrypt(row[2].encode()).decode(), "email": fernet.decrypt(row[3].encode()).decode()} for row in rows]

async def delete_course(user_id: str, term: str, crn: str):
    async with await psycopg.AsyncConnection.connect(db) as conn:
        async with conn.cursor() as cur:

            await cur.execute("""
                DELETE FROM courses
                WHERE term_id = (SELECT term_id FROM terms WHERE user_id = %s AND term_code = %s)
                AND crn = %s
                """, (user_id, term, crn))

            await conn.commit()

async def delete_user(user_id: str):
    async with await psycopg.AsyncConnection.connect(db) as conn:
        async with conn.cursor() as cur:

            await cur.execute("""
                DELETE FROM users WHERE user_id = %s 
                """, (user_id,))

            await conn.commit()







            
            

        
        


