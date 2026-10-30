# CU Scraper

A web app that watches your Carleton University grades for you and emails you when one of them changes. I got tired of refreshing Carleton Central every day during exam season, so I built something to do it for me.

It logs into Carleton Central on your behalf, reads your grades, and keeps checking in the background. When a grade shows up or changes, you get an email about it.

This is a personal project and it is not affiliated with Carleton University in any way. Your Carleton login is encrypted in the database and is only ever used to fetch your own grades.

## Try it out 

You can explore the app without a Carleton login at [cu-scraper.vercel.app/demo](https://cu-scraper.vercel.app/demo), or with the "Try the demo" button on the login page.

The demo uses sample data and is read only. Password and email changes, account deletion, and live grade checks are disabled for it.

## What it does

* Create an account and log in
* See your grades grouped by term, with your cumulative GPA, total credits, course count and term count
* Search your courses by code (like ECOR 1031 or ECOR1031) or by name
* Refresh your grades from the dashboard, or leave automatic checks running in the background
* Get a formatted email when grades change, grouped by term if more than one semester has updates
* Change which email gets notifications from Account. The old address gets a notice and the new one gets a confirmation
* Update your saved Carleton password if you change it at Carleton, without creating a new account
* Pause grade emails and automatic checks from Account, or use the unsubscribe link in a grade email. You can turn them back on later and still refresh manually while they're paused
* Delete your account and its stored data. Email changes and account deletion both ask for your password again

The pages share a dark theme with Carleton's red, black and white, and work on mobile too. There's also an About page explaining how checks work, what gets stored and how notifications are handled.

## How it works

Logging in is the hard part. Carleton Central uses single sign on, so to put it simply, the login goes through a few systems before it actually lets you in. First Microsoft, which is where you type your username and password since Carleton accounts run on Microsoft accounts. Then CAS (Central Authentication Service), which is what lets that one login carry across all of Carleton's different sites without signing in again. And then Banner, the student system that actually holds your grades.

Doing this with plain HTTP requests would be extremely hard, and if the website updates it would break, so it wasn't worth the effort. I ended up opting to use a headless browser to go through the real login with the Python Playwright library, and grab the session cookies once it's through. Using those cookies, I hit the grade pages directly with normal HTTP requests, then pull the grades out of the HTML with the BeautifulSoup Python library.

The checking runs on its own in the background. About every 30 minutes, a poller goes through users who have grade emails enabled, scrapes their grades again, and compares them to what's already saved. If something's different, it queues an email with the updated courses grouped by term. The email also has links to the dashboard, notification settings and an unsubscribe confirmation page. A plain text version is included for email apps that need it.

Grade emails stay in a database queue until they're sent or stop being eligible for delivery. Failed sends are retried, so a temporary email issue doesn't lose the notification as soon as the saved grades are updated. Turning off grade emails also cancels pending grade notifications.

The scraper also sanity checks the shape of what it pulled out of the page, so if Carleton changes their HTML the poller notices instead of saving incorrect data. If the same user keeps failing, a Discord webhook pings me so I can go look.

If you change your password at Carleton, you can still sign into CU Scraper with the password it last had saved. In Account, enter your new Carleton password. The app checks it through Carleton before updating the saved credentials and the password you use to sign into CU Scraper. This doesn't change your password at Carleton itself.

## Tech

The backend is FastAPI. Scraping is Playwright for the login plus httpx and BeautifulSoup for everything after, and the data sits in PostgreSQL. Login passwords are hashed with bcrypt, Carleton credentials get encrypted with Fernet (AES-128), and auth uses JWTs.

The frontend is React and TypeScript on Vite, with React Router handling the pages.

## Running it locally

You'll need Python 3.11 or newer, Node 22.12 or newer, and a PostgreSQL database with the app's tables set up.

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
# on Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

Make a `.env` file in `backend/` with these values:

```
DATABASE_URL=your postgres connection string
JWT_SECRET=some long random string
JWT_EXPIRE_MINUTES=60
FERNET_KEY=your fernet key
GOOGLE_EMAIL=the gmail address that sends notifications
GOOGLE_PASSWORD=a gmail app password for that account
FRONTEND_URL=http://localhost:5173
DISCORD_WEBHOOK_URL=optional, a discord webhook to ping when a user's scrape keeps failing
TRUSTED_HOSTS=comma separated hostnames the backend accepts (e.g. localhost,192.0.2.1)
CORS_ORIGINS=comma separated frontend origins allowed to call the backend (e.g. https://example.com), leave empty in dev
```

Set `FRONTEND_URL` to your frontend address so links in emails point to the right site. For local development, that's normally `http://localhost:5173`. In production, use your public frontend URL.

Then start the API and the poller (they run as two separate processes):

```bash
uvicorn server:app --reload
python poller.py
```

### Frontend

```bash
cd frontend
npm install
```

Make a `.env` file in `frontend/` pointing at your backend:

```
VITE_API_URL=http://localhost:8000
```

Then:

```bash
npm run dev      # local dev server
npm run build    # production build
```

## Tests

The backend has a pytest suite covering the scraping, the grade diffing, the email formatting and the API endpoints. To run it:

```bash
cd backend
pytest
```

GitHub Actions runs the same suite on every push and pull request.

## Security and privacy

Your Carleton password and email never get stored in plain text. They're encrypted with Fernet, and the password for the app itself is hashed with bcrypt. Changing your notification email or deleting your account both require typing your password again, so a stolen token on its own can't quietly hijack where the alerts go or wipe your data. The production frontend build also ships a Content Security Policy so that scripts can only run from places I trust and the page can't quietly send data somewhere it shouldn't. Anything sensitive like the `.env` files and keys stays out of the repo.

If you delete your account, its stored credentials, notification email, course records and grade history are removed from the database. This doesn't delete your real Carleton account or remove emails already delivered to your inbox. Existing server logs aren't erased by account deletion.

Turning off grade emails keeps your account and saved grades. It pauses automatic checks and grade notifications, but account messages like email-change and deletion confirmations can still be sent.

## A word of caution

This app needs your real Carleton login to work, and you're trusting it to hold those credentials. They're encrypted, but you should still only run this on a setup you control and trust, and treat your encryption keys and database the same way you'd treat the credentials themselves. Deleting your account through the app does not touch your actual Carleton account, it only removes your data from this app.
