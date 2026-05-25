from cu_scraper import info
import psycopg
from dotenv import load_dotenv
import os
from cryptography.fernet import Fernet
import bcrypt
load_dotenv()

key = os.getenv("FERNET_KEY")
assert key, "Key not found in .env"
fernet = Fernet(key)

async def register(username: str, password: str, email: str):
    result_info = await info(username, password)
    if not result_info:
        return "invalid credentials"
    
    enc_password = fernet.encrypt(password.encode()).decode()
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    async with await psycopg.AsyncConnection.connect("dbname=cu_scraper user=postgres") as conn:
        async with conn.cursor() as cur:

            await cur.execute("""
                INSERT INTO users (
                username, password, email, hashed_password)
                VALUES (
                %s , %s, %s, %s)
                ON CONFLICT (username) DO NOTHING
                RETURNING user_id
                """,
                (username, enc_password, email, hashed_password.decode()))
            
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
    
    async with await psycopg.AsyncConnection.connect("dbname=cu_scraper user=postgres") as conn:
        async with conn.cursor() as cur:
            for term_code, courses in all_courses.items():
                await cur.execute("""
                    INSERT INTO terms (
                    user_id, term_code) VALUES (
                    %s, %s) 
                    ON CONFLICT (user_id, term_code) DO NOTHING
                    RETURNING term_id
                    """,
                    (user_id, term_code))
                row = await cur.fetchone()
                if row is None:
                    return "wait how could this even happen"
                term_id = row[0]
            
                for course in courses:
                    await cur.execute("""
                        INSERT INTO courses (
                        term_id, crn, subject, course, section, coursetitle, finalgrade, attempted, earned, gpahours, qualitypoints) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s , %s, %s, %s)
                        ON CONFLICT (term_id, crn) DO NOTHING
                        """,
                        (term_id, course["crn"], course["subject"], course["course"], course["section"], course["coursetitle"], course["finalgrade"], course["attempted"], course["earned"], course["gpahours"], course["qualitypoints"]))
            await conn.commit()

async def get_user_credentials(user_id: str):
    async with await psycopg.AsyncConnection.connect("dbname=cu_scraper user=postgres") as conn:
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
                print(row[1])
    return {"username": row[0], "password": fernet.decrypt(row[1].encode()).decode(), "email": row[2]}


async def get_grades(user_id: str, term_code=None):
    async with await psycopg.AsyncConnection.connect("dbname=cu_scraper user=postgres") as conn:
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
                    "finalgrade": row[6],
                    "attempted": row[7],
                    "earned": row[8],
                    "gpahours": row[9],
                    "qualitypoints": row[10] 
                })

            return grades 

async def check_changes(user_id: str, fresh_courses: dict):
    db_grades = await get_grades(user_id)
    changes = {} 
    for term in db_grades:
        if db_grades[term] == fresh_courses[term]:
            continue
        else:
            for course in db_grades[term]:
                found = False
                for fresh_course in fresh_courses[term]:
                    if course["crn"] == fresh_course["crn"]:
                        found = True
                        if course["finalgrade"] != fresh_course["finalgrade"]:
                            if term not in changes:
                                changes[term] = []
                            changes[term].append(course)
                if not found:
                    if term not in changes:
                        changes[term] = []
                    changes[term].append(course)
    return changes

async def update_grades(user_id: str, courses: dict):
    async with await psycopg.AsyncConnection.connect("dbname=cu_scraper user=postgres") as conn:
        async with conn.cursor() as cur:

            for term in courses: 
                for course in courses[term]:
                    await cur.execute("""
                        UPDATE courses
                        SET crn = %s, subject = %s, course = %s, section = %s, coursetitle = %s, finalgrade = %s, attempted = %s, earned = %s, gpahours = %s, qualitypoints = %s
                        WHERE term_id = (SELECT term_id FROM terms WHERE user_id = %s AND term_code = %s)
                        AND crn = %s
                    """, (course["crn"], course["subject"], course["course"], course["section"], course["coursetitle"], course["finalgrade"], course["attempted"], course["earned"], course["gpahours"], course["qualitypoints"], user_id, term, course["crn"]))
        
        await conn.commit()

async def get_user(username: str):
    async with await psycopg.AsyncConnection.connect("dbname=cu_scraper user=postgres") as conn:
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
    async with await psycopg.AsyncConnection.connect("dbname=cu_scraper user=postgres") as conn:
        async with conn.cursor() as cur:

            await cur.execute("""
                SELECT user_id, username, password, email from users 
                """)

            rows = await cur.fetchall()

            return [{"user_id": row[0], "username": row[1], "password": fernet.decrypt(row[2].encode()).decode(), "email": row[3]} for row in rows]

async def delete_user(user_id: str):
    async with await psycopg.AsyncConnection.connect("dbname=cu_scraper user=postgres") as conn:
        async with conn.cursor() as cur:

            await cur.execute("""
                DELETE FROM users WHERE user_id = %s 
                """, (user_id,))

            await conn.commit()









            
            

        
        


