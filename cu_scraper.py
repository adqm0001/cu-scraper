import asyncio
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import os
load_dotenv()

from playwright.async_api import async_playwright, Playwright, expect

async def run(playwright: Playwright, term: str):
    webkit = playwright.webkit
    browser = await webkit.launch()
    context = await browser.new_context()
    page = await context.new_page()
    username = os.getenv("CU_USERNAME")
    password = os.getenv("CU_PASSWORD")
    await page.goto("https://central.carleton.ca")
    await expect(page.get_by_role("textbox", name="User Account")).to_be_visible()
    await page.get_by_role("textbox", name="User Account").click()
    await page.get_by_role("textbox", name="User Account").fill(username)
    await expect(page.get_by_role("textbox", name="Password")).to_be_visible()
    await page.get_by_role("textbox", name="Password").click()
    await page.get_by_role("textbox", name="Password").fill(password)
    await expect(page.get_by_role("button", name="Sign in")).to_be_visible()
    await page.get_by_role("button", name="Sign in").click()
    await expect(page.get_by_role("link", name="Display grades")).to_be_visible()
    await page.get_by_role("link", name="Display grades").click()
    await expect(page.get_by_label("Select a Term:")).to_be_visible()
    await page.get_by_label("Select a Term:").select_option(term)
    await expect(page.get_by_role("button", name="Submit")).to_be_visible()
    await page.get_by_role("button", name="Submit").click()
    await expect(page.get_by_role("table", name="Undergraduate Course Work")).to_be_visible()

    html_content = await page.content()
    await browser.close()
    soup = BeautifulSoup(html_content, 'html.parser') 
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

async def get_terms(playwright: Playwright):
    webkit = playwright.webkit
    browser = await webkit.launch()
    context = await browser.new_context()
    page = await context.new_page()
    username = os.getenv("CU_USERNAME")
    password = os.getenv("CU_PASSWORD")
    await page.goto("https://central.carleton.ca")
    await expect(page.get_by_role("textbox", name="User Account")).to_be_visible()
    await page.get_by_role("textbox", name="User Account").click()
    await page.get_by_role("textbox", name="User Account").fill(username)
    await expect(page.get_by_role("textbox", name="Password")).to_be_visible()
    await page.get_by_role("textbox", name="Password").click()
    await page.get_by_role("textbox", name="Password").fill(password)
    await expect(page.get_by_role("button", name="Sign in")).to_be_visible()
    await page.get_by_role("button", name="Sign in").click()
    await expect(page.get_by_role("link", name="Display grades")).to_be_visible()
    await page.get_by_role("link", name="Display grades").click()
    await expect(page.get_by_label("Select a Term:")).to_be_visible()
    terms = await page.get_by_label("Select a Term:").evaluate(
    "select => Array.from(select.options).map(o => o.value)"
    )
    await browser.close()
    return [t for t in terms if t]

async def main():
    async with async_playwright() as playwright: 
        terms = await get_terms(playwright)

        all_courses = {} 
        student_name = student_number = student_info_dict = student_program = None

        for i, term in enumerate(terms):
            if i == 0:
                student_name, student_number, student_info_dict, courses, student_program = await run(playwright, term)
            else:
                _, _, _, courses, _ = await run(playwright, term)
            all_courses[term] = courses

    # Small test 
    print(all_courses)
    print("---------------")
    print(student_program)
    print("---------------")
    print(student_info_dict)
    return student_name, student_number, student_info_dict, student_program, all_courses

asyncio.run(main())
