from cu_scraper import info
import psycopg
from dotenv import load_dotenv
import os
from cryptography.fernet import Fernet
import bcrypt
load_dotenv()

key = os.getenv("FERNET_KEY")
db = os.getenv("DATABASE_URL")
assert db, "Database not found in .env"
assert key, "Key not found in .env"
fernet = Fernet(key)

async def register(username: str, password: str, email: str):
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
                    SELECT username, password, email
                    FROM users
                    WHERE user_id = %s
                    """,
                    (user_id,))

                row = await cur.fetchone()
                if row is None:
                    return "user_id not found"
    return {"username": row[0], "password": fernet.decrypt(row[1].encode()).decode(), "email": fernet.decrypt(row[2].encode()).decode()}


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
            last_updated = row[0].isoformat()

            return grades, last_updated

async def check_changes(user_id: str, fresh_courses: dict):
    db_grades, _ = await get_grades(user_id)
    changes = {} 
    for term in db_grades:
        if db_grades[term] == fresh_courses[term]:
            continue
        else:
            for fresh_course in fresh_courses[term]:
                found = False
                for course in db_grades[term]:
                    if course["crn"] == fresh_course["crn"]:
                        found = True
                        if course["finalgrade"] != fresh_course["finalgrade"]:
                            if term not in changes:
                                changes[term] = []
                            changes[term].append(fresh_course)
                if not found:
                    if term not in changes:
                        changes[term] = []
                    changes[term].append(fresh_course)

            for course in db_grades[term]:
                found = False
                for fresh_course in fresh_courses[term]:
                    if course["crn"] == fresh_course["crn"]:
                        found = True
                if not found:
                    await delete_course(user_id, term, course["crn"]) 
    return changes

async def update_grades(user_id: str, courses: dict):
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

async def get_users(): 
    async with await psycopg.AsyncConnection.connect(db) as conn: 
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT user_id, username, password, email from users 
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







            
            

        
        


