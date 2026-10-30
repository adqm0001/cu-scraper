import { Link } from 'react-router';
import { ArrowUpRight, Mail } from 'lucide-react';
import { PublicShell } from '../components/PublicShell.tsx';
import './About.css';

export function About() {
  return (
    <PublicShell>
      <main className="about-content">
        <header className="about-intro">
          <p className="public-eyebrow">ABOUT CU SCRAPER</p>
          <h1>Your grades.<br />Here’s how it works.</h1>
          <p>CU Scraper checks Carleton Central for grade changes and emails you when it finds an update. Here’s what happens when you connect your account, and what information the app keeps.</p>
        </header>
        <div className="about-layout">
          <nav className="about-contents" aria-label="On this page">
            <span>ON THIS PAGE</span>
            <a href="#grade-checks">How grade checks work</a>
            <a href="#your-data">Your data</a>
            <a href="#notifications">Email notifications</a>
            <a href="#your-choices">Your choices</a>
          </nav>
          <div className="about-sections">
            <section id="grade-checks" className="about-section">
              <span className="about-section-number">01 / GRADE CHECKS</span>
              <h2>Checking for you, in the background.</h2>
              <p>When you register, the app signs in to Carleton Central with the username and password you provide. It reads your course and grade information and saves a copy so it can compare future checks against it.</p>
              <p>When grade emails are enabled, background checks run roughly every 30 minutes while the service is running. If a check finds changed grades or new courses, the app sends an update to your notification email. You don’t need to keep the website open.</p>
              <p>You can also use Refresh grades on the dashboard. Checks aren’t instant: Carleton availability, login issues, and email delivery can cause delays. Carleton Central remains the source for your official grades.</p>
            </section>
            <section id="your-data" className="about-section">
              <span className="about-section-number">02 / YOUR DATA</span>
              <h2>What gets stored, and why.</h2>
              <dl className="about-data-list">
                <div><dt>Carleton username</dt><dd>Identifies your account and is used to sign in to Carleton Central for grade checks.</dd></div>
                <div><dt>Carleton password</dt><dd>Stored encrypted using AES-128 through Fernet. The server decrypts it when signing in to Carleton on your behalf. Encryption protects the stored value, but the service still needs access to your real password to check grades.</dd></div>
                <div><dt>App sign-in password</dt><dd>A separate bcrypt hash is used to check your CU Scraper login. Updating your Carleton password in Account updates both stored versions.</dd></div>
                <div><dt>Notification email</dt><dd>Stored encrypted and used for grade updates and account messages. It can be a personal address; it doesn’t have to be your Carleton email.</dd></div>
                <div><dt>Courses and grades</dt><dd>Term information, course codes, titles, grades, credits, and grade-point values are saved to show your dashboard and detect changes. Grades and credit values are encrypted in the database; course codes and titles are stored as readable text.</dd></div>
              </dl>
              <p className="about-detail">Your browser saves a sign-in token so you can stay logged in. Logging out removes that saved token.</p>
              <h3>Other services involved</h3>
              <p>Your credentials are submitted to Carleton’s login systems to fetch grades. Notification emails are sent through Gmail, so the email provider handles the recipient address and message contents, including the grades shown in an update.</p>
              <p>For troubleshooting, server logs and configured Discord alerts can contain a username, an error type, or an unrecognised grade code. Passwords are not included in the Discord alert messages.</p>
            </section>
            <section id="notifications" className="about-section">
              <span className="about-section-number">03 / EMAIL NOTIFICATIONS</span>
              <h2>Sent to the address you choose.</h2>
              <p>Enter your preferred notification email when you register. To change it later, open Account, select Change beside Notification email, and confirm with your current CU Scraper password.</p>
              <p>Grade updates use a simple email layout, with a plain-text version for email apps that need it. Each update lists the term, course code, and detected grade. If multiple courses change in the same check, they appear in the same message.</p>
              <figure className="about-email">
                <figcaption><Mail size={16} /><span>Example grade update</span><span className="about-example-tag">SAMPLE</span></figcaption>
                <div className="about-email-meta"><span>To</span><span>you@example.com</span><span>Subject</span><strong>CU Scraper - Grade Update</strong></div>
                <pre>{`Hi there,

There are new grades on Carleton Central.
Here’s what changed:

Fall 2024
ECOR 1031    A
MATH 1007    A+`}</pre>
              </figure>
              <p>The app also sends a welcome message when you register. Changing your notification email sends a notice to your old address and a subscription confirmation to your new one. Deleting your account sends a final confirmation email.</p>
            </section>
            <section id="your-choices" className="about-section">
              <span className="about-section-number">04 / YOUR CHOICES</span>
              <h2>You control the account.</h2>
              <h3>Pause or resume grade emails</h3>
              <p>In Account, use the Grade update emails switch under Notifications. Turning it off pauses both grade emails and automatic checks, without deleting your account or saved grades. Manual dashboard refresh still works.</p>
              <p>You can also use the unsubscribe link in a grade email. Opening the link shows a confirmation page; nothing changes until you confirm. Essential account emails, such as email-change and deletion confirmations, are still sent. To resume grade emails and automatic checks, turn the switch back on in Account.</p>
              <h3>Keep your Carleton password up to date</h3>
              <p>If you change your password at Carleton, update it in Account too. Otherwise the saved credentials won’t work and grade checks will fail. Until you update it here, CU Scraper still uses your previous app password for sign-in.</p>
              <h3>Delete your CU Scraper account</h3>
              <p>Deleting your account in Account removes your stored credentials, notification email, and associated course and grade records from the active database, and stops future checks for that account. You confirm the deletion with your current CU Scraper password.</p>
              <p>This does not delete or change your real Carleton University account. It also doesn’t erase emails already delivered to your inbox or existing operational logs.</p>
              <div className="about-independent"><h3>An independent student project</h3><p>CU Scraper is not affiliated with or endorsed by Carleton University. Only connect your account if you’re comfortable letting this service store your credentials and sign in on your behalf. No service can guarantee complete security.</p></div>
              <Link className="public-secondary" to="/demo">Explore with sample data <ArrowUpRight size={14} /></Link>
            </section>
          </div>
        </div>
      </main>
    </PublicShell>
  );
}
