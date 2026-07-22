import asyncio
import re
import httpx
from bs4 import BeautifulSoup

# This lists every valid Carleton grade code so we can tell if the page layout changed.
GRADE_RE = re.compile(r"^([A-D][+-]?|F|AEG|AUD|CEX|CH|CLP|CR|CTN|CUO|CUR|DEF|GNA|IP|NR|SAT|UCH|UNS|WDN)?$")

from playwright.async_api import async_playwright, Playwright, expect

async def login(playwright: Playwright, username: str, password: str):
    webkit = playwright.chromium
    browser = await webkit.launch(headless=True)
    context = await browser.new_context()
    page = await context.new_page()
    await page.goto("https://central.carleton.ca")
    await expect(page.get_by_role("textbox", name="User Account")).to_be_visible()
    await page.get_by_role("textbox", name="User Account").click()
    await page.get_by_role("textbox", name="User Account").fill(username)
    await expect(page.get_by_role("textbox", name="Password")).to_be_visible()
    await page.get_by_role("textbox", name="Password").click()
    await page.get_by_role("textbox", name="Password").fill(password)
    await expect(page.get_by_role("button", name="Sign in")).to_be_visible()
    await page.get_by_role("button", name="Sign in").click()
    
    try:
        continue_btn = page.get_by_role("button", name="Continue")
        await expect(continue_btn).to_be_visible(timeout=3000)
        await continue_btn.click()
        await page.wait_for_load_state("networkidle")
    except Exception:
        pass
    try:
        await expect(page.get_by_role("link", name="Display grades")).to_be_visible()
        cookies = await context.cookies()
    except Exception as e:
        print(f"Login failed: {e}")
        await browser.close()
        return None
    await browser.close()
    return cookies 

def build_cookies(cookies):
    cookies_dict = {}
    for cookie in cookies:
        name = cookie["name"]
        cookies_dict[name] = cookie["value"]
    return cookies_dict

async def get_terms(cookies):
    cookies_dict = build_cookies(cookies)
    async with httpx.AsyncClient(cookies=cookies_dict) as client:
        response = await client.get("https://central.carleton.ca/prod/bwskogrd.P_ViewTermGrde")

        soup = BeautifulSoup(response.text, 'html.parser')
        selectObj = soup.find('select', {"name": 'term_in'})
        optionObj = selectObj.find_all('option')
        terms = []
        for tag in optionObj:
            terms.append(tag["value"])

        return terms

def parse_grades_page(html):
    soup = BeautifulSoup(html, 'html.parser') 
    all_tables = soup.find_all('td', class_="dddefault")
    courses = []
    student_program = {}
    header = True
    for i in range(0, len(all_tables), 11):
        chunk = all_tables[i:i+11]
        if header:
            student_program = {    
                "currentprogram": chunk[0].get_text(strip=True),
                "level": chunk[1].get_text(strip=True),
                "program": chunk[2].get_text(strip=True),
                "admitterm": chunk[3].get_text(strip=True),
                "admittype": chunk[4].get_text(strip=True),
                #"catalogterm": chunk[5].get_text(strip=True),
                "college": chunk[6].get_text(strip=True),
                "campus": chunk[7].get_text(strip=True),
                "major": chunk[8].get_text(strip=True),
                "concentration": chunk[9].get_text(strip=True),
                "academicstanding": chunk[10].get_text(strip=True)  
            }
            header = False
        else:
            course = {
                "crn": chunk[0].get_text(strip=True),
                "subject": chunk[1].get_text(strip=True),
                "course": chunk[2].get_text(strip=True),
                "section": chunk[3].get_text(strip=True),
                "coursetitle": chunk[4].get_text(strip=True),
                "campus": chunk[5].get_text(strip=True),
                "finalgrade": chunk[6].get_text(strip=True),
                "attempted": chunk[7].get_text(strip=True),
                "earned": chunk[8].get_text(strip=True),
                "gpahours": chunk[9].get_text(strip=True),
                "qualitypoints": chunk[10].get_text(strip=True)
            }
            if not GRADE_RE.match(course["finalgrade"]):
                raise ValueError(f"unexpected finalgrade: {course['finalgrade']!r}")
            if course["crn"] and not course["crn"].isdigit():
                raise ValueError(f"unexpected crn: {course['crn']!r}")
            courses.append(course)
    student_info = soup.find('div', class_='staticheaders')
    lines = student_info.get_text(separator="\n", strip=True).split("\n")
    student_number = lines[0].split(" ", 1)[0]
    student_name = lines[0].split(" ", 1)[1]
    student_info_dict = {
            "studentnumber": student_number,
            "studentname": student_name
    }

    return student_name, student_number, student_info_dict, courses, student_program


async def get_grades(cookies, term):
    cookies_dict = build_cookies(cookies)

    async with httpx.AsyncClient(cookies=cookies_dict) as client:
        response = await client.post("https://central.carleton.ca/prod/bwskogrd.P_ViewGrde", data={"term_in": term})
        student_name, student_number, student_info_dict, courses, student_program = parse_grades_page(response.text)
        return student_name, student_number, student_info_dict, courses, student_program

async def info(username, password):
    async with async_playwright() as playwright: 
        cookies = await login(playwright, username, password)
        if cookies is None:
            return None
        terms = await get_terms(cookies)

        all_courses = {}
        student_name = student_number = student_info_dict = student_program = None

        for i, term in enumerate(terms):
            if i == 0:
                student_name, student_number, student_info_dict, courses, student_program = await get_grades(cookies, term)
            else:
                _, _, _, courses, _ = await get_grades(cookies, term) 
            all_courses[term] = courses 
        return student_name, student_number, student_info_dict, student_program, all_courses, cookies 


