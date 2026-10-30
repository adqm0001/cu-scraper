import { Link, NavLink } from 'react-router';
import { ArrowUpRight } from 'lucide-react';
import { type ReactNode } from 'react';
import '../pages/Dashboard.css';
import '../pages/Public.css';

export function PublicShell({ children }: { children: ReactNode }) {
  return (
    <div className="public-page">
      <header className="dashboard-nav">
        <Link className="dashboard-brand" to="/login" aria-label="CU Scraper home">
          <span className="dashboard-monogram">cu<span>.</span></span>
          <span>CU Scraper<span className="dashboard-brand-caption">CARLETON GRADE TRACKER</span></span>
        </Link>
        <nav className="public-nav" aria-label="Main navigation">
          <NavLink to="/about">About</NavLink>
          <Link to="/demo">Try the demo <ArrowUpRight size={14} /></Link>
        </nav>
      </header>
      {children}
      <footer className="public-footer"><div className="public-footer-links"><span>CU Scraper</span><Link to="/about">About & privacy</Link></div><span>Independent project. Not affiliated with Carleton University.</span></footer>
    </div>
  );
}

export function AuthIntroduction() {
  return (
    <aside className="auth-introduction">
      <p className="public-eyebrow">FOR CARLETON STUDENTS</p>
      <h2>Keep up with<br />your grades.</h2>
      <p>View your courses in one place and get an email when a grade changes on Carleton Central.</p>
      <div className="auth-course-preview" aria-label="Example grade notification">
        <div className="auth-preview-heading"><span>Grade update</span><span>EXAMPLE</span></div>
        <div className="auth-preview-course"><div><strong>ECOR 1031</strong><span>Programming and Data Management</span></div><strong>A</strong></div>
        <p>One less reason to keep checking Carleton Central.</p>
      </div>
      <p className="auth-privacy-note">Your Carleton credentials are encrypted using AES-128 and used to check your grades.</p>
    </aside>
  );
}
