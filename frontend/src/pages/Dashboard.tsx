import { useState, useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router';
import { type Course } from '../utils/Course.ts';
import { TermCard } from '../components/TermCard.tsx';
import { useAuthContext } from '../context/AuthContext.tsx'
import { isTimeout, QUICK_TIMEOUT, SCRAPE_TIMEOUT, DEMO_RESTRICTED_MSG } from '../utils/errors.ts'
import { ArrowUpRight, LogOut, RefreshCw, Search, X } from 'lucide-react';
import './Dashboard.css'

interface GradesData {
  [termCode: string]: Course[];
}

export function Dashboard(){
  const [searching, setSearching] = useState('');
  const [grades, setGrades] = useState<GradesData | null>(null);
  const { token, setToken } = useAuthContext();
  const [cumulativeGpa, setCumulativeGpa] = useState<number | null>(null);
  const [totalCredits, setTotalCredits] = useState(0);
  const [termsCount, setTermsCount] = useState(0);
  const [lastUpdated, setLastUpdated] = useState('');
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState('');
  const [isDemo, setIsDemo] = useState(false);
  const notificationTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  const navigate = useNavigate();

  function showNotification(msg: string) {
    if (notificationTimeout.current) clearTimeout(notificationTimeout.current);
    setNotification(msg);
    notificationTimeout.current = setTimeout(() => setNotification(''), 3000);
  }

  function computeInfo(gradesData: GradesData) {
    let totalQP = 0;
    let totalGH = 0;
    let totalEarned = 0;

    Object.values(gradesData).forEach(courses =>
      courses.forEach(course => {
        totalQP += Number(course.qualitypoints);
        totalGH += Number(course.gpahours);
        totalEarned += Number(course.earned);
      })
    );

    setCumulativeGpa(totalGH > 0 ? totalQP / totalGH : null);
    setTotalCredits(totalEarned);
    setTermsCount(Object.keys(gradesData).length);
  }

  function logOut() {
    localStorage.removeItem('token');
    setToken('');
    navigate('/login');
  }

  async function handleRefresh() {
    setLoading(true);
    try {
      const check = await fetch(`${import.meta.env.VITE_API_URL}/grades/check`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        signal: AbortSignal.timeout(SCRAPE_TIMEOUT),
      });
      if (check.status === 401) { logOut(); return; }
      if (check.status === 403) { showNotification(DEMO_RESTRICTED_MSG); return; }
      if (!check.ok) { showNotification('Failed to refresh grades. Please try again.'); return; }
      const response = await fetch(`${import.meta.env.VITE_API_URL}/grades`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        signal: AbortSignal.timeout(QUICK_TIMEOUT),
      });
      if (response.status === 401) { logOut(); return; }
      const data = await response.json();
      setGrades(data.grades);
      setLastUpdated(data.last_updated);
      computeInfo(data.grades);
      showNotification('Grades refreshed');
    } catch (err) {
      showNotification(isTimeout(err) ? 'Refresh is taking too long. Please try again.' : 'Failed to refresh grades. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    async function fetchGrades() {
      try {
        const response = await fetch(`${import.meta.env.VITE_API_URL}/grades`, {
          method: 'GET',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
          signal: AbortSignal.timeout(QUICK_TIMEOUT),
        });
        if (response.status === 401) { logOut(); return; }
        const data = await response.json();
        setGrades(data.grades);
        setLastUpdated(data.last_updated);
        computeInfo(data.grades);
      } catch (err) {
        showNotification(isTimeout(err) ? 'Loading grades timed out. Please refresh.' : 'Failed to load grades. Please refresh.');
      }
    }
    async function fetchDemoFlag() {
      try {
        const response = await fetch(`${import.meta.env.VITE_API_URL}/users/me`, {
          headers: { Authorization: `Bearer ${token}` },
          signal: AbortSignal.timeout(QUICK_TIMEOUT),
        });
        if (response.ok) setIsDemo((await response.json()).is_demo === true);
      } catch {
        setIsDemo(false);
      }
    }
    fetchGrades();
    fetchDemoFlag();
    return () => { if (notificationTimeout.current) clearTimeout(notificationTimeout.current); };
  }, []);

  const formatLastUpdated = () => {
    if (!lastUpdated) return '—';
    return new Date(lastUpdated).toLocaleString(undefined, {
      month: 'short', day: 'numeric', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  };

  const filteredEntries = grades
    ? Object.entries(grades).map(([termCode, courses]) => ({
        termCode,
        allCourses: courses,
        courses: courses.filter(c => {
          const q = searching.trim().toLowerCase();
          if (!q) return true;
          return `${c.subject}${c.course}`.toLowerCase().includes(q.replace(/\s+/g, '')) || c.coursetitle.toLowerCase().includes(q);
        }),
      })).filter(({ courses }) => courses.length > 0 || !searching)
    : [];

  const courseCount = grades ? Object.values(grades).reduce((total, courses) => total + courses.length, 0) : 0;
  const shownCount = filteredEntries.reduce((total, entry) => total + entry.courses.length, 0);

  return (
    <div className="dashboard-page">
      <header className="dashboard-nav">
        <a className="dashboard-brand" href="/app/dashboard" aria-label="CU Scraper dashboard">
          <span className="dashboard-monogram">cu<span>.</span></span>
          <span>CU Scraper<span className="dashboard-brand-caption">CARLETON GRADE TRACKER</span></span>
        </a>
        <nav className="dashboard-links" aria-label="Main navigation">
          <span className="dashboard-current" aria-current="page">Overview</span>
          <button onClick={() => navigate('/app/profile')}>Account <ArrowUpRight size={14} /></button>
          <button className="dashboard-logout" onClick={logOut}><LogOut size={15} /><span>Log out</span></button>
        </nav>
      </header>

      <main className="dashboard-content">
        {isDemo && <div className="dashboard-demo"><span>DEMO</span> You’re viewing sample grades. Account changes and refresh are disabled.</div>}
        <section className="dashboard-intro" aria-labelledby="dashboard-title">
          <div>
            <p className="dashboard-eyebrow">ACADEMIC OVERVIEW</p>
            <h1 id="dashboard-title">Your grades.</h1>
            <p className="dashboard-subtitle">Your academic record, organised by term.</p>
          </div>
          <div className="dashboard-refresh-area">
            <button className="dashboard-refresh" disabled={loading || isDemo} onClick={handleRefresh}>
              <RefreshCw size={15} className={loading ? 'dashboard-spinning' : ''} />
              {loading ? 'Checking grades…' : 'Refresh grades'}
            </button>
            <span className="dashboard-updated">Last checked {formatLastUpdated()}</span>
          </div>
        </section>

        <section className="dashboard-summary" aria-label="Academic summary">
          <div className="dashboard-metric dashboard-metric-gpa">
            <span className="dashboard-metric-label">Cumulative GPA</span>
            <div className="dashboard-metric-number">{cumulativeGpa !== null ? cumulativeGpa.toFixed(2) : '—'}<span>/ 12.00</span></div>
            <span className="dashboard-metric-note">Across all graded courses</span>
          </div>
          <div className="dashboard-metric">
            <span className="dashboard-metric-label">Credits earned</span>
            <div className="dashboard-metric-number">{grades ? totalCredits.toFixed(1) : '—'}</div>
            <span className="dashboard-metric-note">Successfully completed</span>
          </div>
          <div className="dashboard-metric">
            <span className="dashboard-metric-label">Courses</span>
            <div className="dashboard-metric-number">{grades ? courseCount : '—'}</div>
            <span className="dashboard-metric-note">In {termsCount} academic {termsCount === 1 ? 'term' : 'terms'}</span>
          </div>
          <div className="dashboard-metric"><span className="dashboard-metric-label">Academic terms</span><div className="dashboard-metric-number">{grades ? termsCount : '—'}</div><span className="dashboard-metric-note">On your record</span></div>
        </section>

        <section className="dashboard-records" aria-labelledby="records-title">
          <div className="dashboard-records-toolbar">
            <div className="dashboard-records-title"><h2 id="records-title">Course history</h2><span>{shownCount} {shownCount === 1 ? 'course' : 'courses'}</span></div>
            <div className="dashboard-search">
              <Search size={17} aria-hidden="true" />
              <input aria-label="Search courses by code or name" placeholder="Search by code or course name" value={searching} onChange={e => setSearching(e.target.value)} />
              {searching && <button onClick={() => setSearching('')} aria-label="Clear search"><X size={15} /></button>}
            </div>
          </div>
          <div className="terms-list">
            {grades === null ? <p className="dashboard-empty">Loading your academic record…</p> : filteredEntries.length === 0 ? <p className="dashboard-empty">No courses match “{searching}”. Try a course code or name.</p> : filteredEntries.map(({ termCode, courses, allCourses }) => <TermCard key={termCode} termCode={termCode} courses={courses} allCourses={allCourses} />)}
          </div>
        </section>
        <footer className="dashboard-footer"><div className="public-footer-links"><span>CU Scraper</span><Link to="/about">About & privacy</Link></div><span>Independent project. Not affiliated with Carleton University.</span></footer>
      </main>
      {notification && <div className="notification-toast" role="status">{notification}</div>}
    </div>
  );
}
