import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router';
import { type Course } from '../utils/Course.ts';
import { TermCard } from '../components/TermCard.tsx';
import { useAuthContext } from '../context/AuthContext.tsx'
import { isTimeout, QUICK_TIMEOUT, SCRAPE_TIMEOUT, DEMO_RESTRICTED_MSG } from '../utils/errors.ts'
import './Dashboard.css'

interface GradesData {
  [termCode: string]: Course[];
}

export function Dashboard(){
  const [searching, setSearching] = useState('');
  const [searchMode, setSearchMode] = useState<'code' | 'name'>('code');
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
          const q = searching.toLowerCase();
          if (!q) return true;
          if (searchMode === 'code') return `${c.subject}${c.course}`.toLowerCase().includes(q.replace(/\s+/g, ''));
          return c.coursetitle.toLowerCase().includes(q);
        }),
      })).filter(({ courses }) => courses.length > 0 || !searching)
    : [];

  return (
    <div className="dashboard-page">
      <nav className="dashboard-nav">
        <span className="nav-logo">CU SCRAPER</span>
        <div className="nav-actions">
          <button className="btn-refresh" disabled={loading} onClick={handleRefresh}>
            {loading ? 'Refreshing...' : 'Refresh Grades'}
          </button>
          <button className="btn-outline" onClick={() => navigate('/app/profile')}>Profile</button>
          <button className="btn-outline btn-logout" onClick={logOut}>Log out</button>
        </div>
      </nav>

      <main className="dashboard-content">
        {isDemo && (
          <div className="demo-banner">
            <span className="demo-banner-tag">Demo Mode</span>
            Sample data. Account changes and grade refresh are disabled.
          </div>
        )}
        <div className="stats-row">
          <div className="stat-card">
            <span className="stat-label">Cumulative GPA</span>
            <span className="stat-value gpa">
              {cumulativeGpa !== null ? cumulativeGpa.toFixed(2) : '—'}
            </span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Total Credits</span>
            <span className="stat-value">{totalCredits || '—'}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Terms</span>
            <span className="stat-value">{termsCount || '—'}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Last Updated</span>
            <span className="stat-value" style={{ fontSize: '1rem', paddingTop: '4px' }}>
              {formatLastUpdated()}
            </span>
          </div>
        </div>

        <div className="search-row">
          <input
            className="search-input"
            placeholder={searchMode === 'code' ? 'e.g. ECOR 1031' : 'e.g. Programming and Data Management'}
            value={searching}
            onChange={e => setSearching(e.target.value)}
          />
          <div className="search-toggle">
            <button
              className={`toggle-btn ${searchMode === 'code' ? 'active' : ''}`}
              onClick={() => setSearchMode('code')}
            >Code</button>
            <button
              className={`toggle-btn ${searchMode === 'name' ? 'active' : ''}`}
              onClick={() => setSearchMode('name')}
            >Name</button>
          </div>
        </div>

        <div className="terms-list">
          {grades === null ? (
            <p className="empty-state">Loading grades...</p>
          ) : filteredEntries.length === 0 ? (
            <p className="empty-state">No courses found.</p>
          ) : (
            filteredEntries.map(({ termCode, courses, allCourses }) => (
              <TermCard key={termCode} termCode={termCode} courses={courses} allCourses={allCourses} />
            ))
          )}
        </div>
      </main>

      {notification && <div className="notification-toast">{notification}</div>}
    </div>
  );
}
