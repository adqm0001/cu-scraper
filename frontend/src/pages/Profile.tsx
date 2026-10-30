import { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router';
import { useAuthContext } from '../context/AuthContext.tsx';
import { isTimeout, QUICK_TIMEOUT, SCRAPE_TIMEOUT, DEMO_RESTRICTED_MSG } from '../utils/errors.ts';
import { ArrowLeft, LogOut, ShieldCheck } from 'lucide-react';
import './Dashboard.css';
import './Profile.css';

export function Profile() {
  const { token, setToken } = useAuthContext();
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [newEmail, setNewEmail] = useState('');
  const [emailCurrentPassword, setEmailCurrentPassword] = useState('');
  const [editingEmail, setEditingEmail] = useState(false);
  const [savingEmail, setSavingEmail] = useState(false);
  const [newPassword, setNewPassword] = useState('');
  const [editingPassword, setEditingPassword] = useState(false);
  const [savingPassword, setSavingPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [deleteCurrentPassword, setDeleteCurrentPassword] = useState('');
  const [deleting, setDeleting] = useState(false);
  const [notification, setNotification] = useState('');
  const [isDemo, setIsDemo] = useState(false);
  const [gradeEmails, setGradeEmails] = useState<boolean | null>(null);
  const [savingGradeEmails, setSavingGradeEmails] = useState(false);
  const notificationTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  function showNotification(msg: string) {
    if (notificationTimeout.current) clearTimeout(notificationTimeout.current);
    setNotification(msg);
    notificationTimeout.current = setTimeout(() => setNotification(''), 3000);
  }

  function guardDemo(action: () => void) {
    if (isDemo) {
      showNotification(DEMO_RESTRICTED_MSG);
      return;
    }
    action();
  }

  function logOut() {
    localStorage.removeItem('token');
    setToken('');
    navigate('/login');
  }

  useEffect(() => {
    async function fetchMe() {
      try {
        const response = await fetch(`${import.meta.env.VITE_API_URL}/users/me`, {
          method: 'GET',
          headers: { Authorization: `Bearer ${token}` },
          signal: AbortSignal.timeout(QUICK_TIMEOUT),
        });
        if (response.status === 401) { logOut(); return; }
        const data = await response.json();
        setUsername(data.username);
        setEmail(data.email);
        setIsDemo(data.is_demo === true);
        setGradeEmails(data.grade_emails_enabled !== false);
      } catch (err) {
        showNotification(isTimeout(err) ? 'Loading your profile timed out. Please refresh.' : 'Failed to load your profile. Please refresh.');
      }
    }
    fetchMe();
    return () => { if (notificationTimeout.current) clearTimeout(notificationTimeout.current); };
  }, []);

  async function toggleGradeEmails() {
    if (savingGradeEmails || gradeEmails === null) return;
    const next = !gradeEmails;
    setSavingGradeEmails(true);
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/users/me/notifications`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ grade_emails_enabled: next }),
        signal: AbortSignal.timeout(QUICK_TIMEOUT),
      });
      if (response.ok) {
        setGradeEmails(next);
        showNotification(next ? 'Grade emails turned on' : 'Grade emails paused');
      } else if (response.status === 401) {
        logOut();
      } else if (response.status === 403) {
        showNotification(DEMO_RESTRICTED_MSG);
      } else {
        showNotification('Failed to update your notification settings. Please try again.');
      }
    } catch (err) {
      showNotification(isTimeout(err) ? 'The request timed out. Please try again.' : 'Network error. Please try again.');
    } finally {
      setSavingGradeEmails(false);
    }
  }

  async function handleSaveEmail() {
    if (savingEmail || !newEmail || !emailCurrentPassword) return;
    setSavingEmail(true);
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/users/me/email`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ email: newEmail, current_password: emailCurrentPassword }),
        signal: AbortSignal.timeout(QUICK_TIMEOUT),
      });
      if (response.ok) {
        setEmail(newEmail);
        setNewEmail('');
        setEmailCurrentPassword('');
        setEditingEmail(false);
        showNotification('Email updated');
      } else if (response.status === 403) {
        handleCancelEmail();
        showNotification(DEMO_RESTRICTED_MSG);
      } else if (response.status === 401) {
        showNotification('Incorrect password.');
      } else {
        showNotification('Failed to update email. Please try again.');
      }
    } catch (err) {
      showNotification(isTimeout(err) ? 'The request timed out. Please try again.' : 'Network error. Please try again.');
    } finally {
      setSavingEmail(false);
    }
  }

  function handleCancelEmail() {
    setNewEmail('');
    setEmailCurrentPassword('');
    setEditingEmail(false);
  }

  async function handleSavePassword() {
    if (savingPassword || !newPassword) return;
    setSavingPassword(true);
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/users/me/password`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ password: newPassword }),
        signal: AbortSignal.timeout(SCRAPE_TIMEOUT),
      });
      if (response.ok) {
        setNewPassword('');
        setEditingPassword(false);
        showNotification('Carleton password updated');
      } else if (response.status === 403) {
        handleCancelPassword();
        showNotification(DEMO_RESTRICTED_MSG);
      } else if (response.status === 401) {
        showNotification('Could not verify that password with Carleton. Double-check it.');
      } else {
        showNotification('Failed to update password. Please try again.');
      }
    } catch (err) {
      showNotification(isTimeout(err) ? 'Verifying with Carleton timed out. Please try again.' : 'Network error. Please try again.');
    } finally {
      setSavingPassword(false);
    }
  }

  function handleCancelPassword() {
    setNewPassword('');
    setEditingPassword(false);
  }

  async function handleDeleteAccount() {
    if (deleting || !deleteCurrentPassword) return;
    setDeleting(true);
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/users/me`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ current_password: deleteCurrentPassword }),
        signal: AbortSignal.timeout(QUICK_TIMEOUT),
      });
      if (response.ok) {
        logOut();
      } else if (response.status === 403) {
        setShowConfirm(false);
        setDeleteCurrentPassword('');
        showNotification(DEMO_RESTRICTED_MSG);
      } else if (response.status === 401) {
        showNotification('Incorrect password.');
      } else {
        setShowConfirm(false);
        showNotification('Failed to delete account. Please try again.');
      }
    } catch (err) {
      setShowConfirm(false);
      showNotification(isTimeout(err) ? 'The request timed out. Please try again.' : 'Network error. Please try again.');
    } finally {
      setDeleting(false);
    }
  }

  function handleCancelDelete() {
    setDeleteCurrentPassword('');
    setShowConfirm(false);
  }

  return (
    <div className="profile-page dashboard-page">
      <header className="dashboard-nav">
        <a className="dashboard-brand" href="/app/dashboard" aria-label="CU Scraper dashboard">
          <span className="dashboard-monogram">cu<span>.</span></span>
          <span>CU Scraper<span className="dashboard-brand-caption">CARLETON GRADE TRACKER</span></span>
        </a>
        <nav className="dashboard-links" aria-label="Main navigation">
          <button onClick={() => navigate('/app/dashboard')}><ArrowLeft size={16} aria-hidden="true" />Overview</button>
          <span className="dashboard-current" aria-current="page">Account</span>
          <button className="dashboard-logout" onClick={logOut}><LogOut size={15} /><span>Log out</span></button>
        </nav>
      </header>

      <main className="profile-content">
        {isDemo && <div className="dashboard-demo"><span>DEMO</span> You’re viewing a sample account. Account changes are disabled.</div>}
        <div className="profile-intro">
          <p className="dashboard-eyebrow">ACCOUNT SETTINGS</p>
          <h1>Your account.</h1>
          <p>Manage your details and where your grade updates go.</p>
        </div>

        <div className="profile-card">
          <div className="profile-card-header">
            <h2 className="profile-card-title">Account details</h2><p>Your Carleton username and saved login details.</p>
          </div>
          <div className="profile-card-body">
            <div className="profile-field">
              <span className="profile-field-label">Username</span>
              <span className="profile-field-value">{username || '—'}</span>
            </div>

            <div className="profile-field">
              <span className="profile-field-label">Carleton password</span><span className="profile-field-hint">Changed your password at Carleton? Update it here to keep grade checks working.</span>
              {editingPassword ? (
                <div className="email-edit-row">
                  <input
                    className="profile-field-input"
                    type="password"
                    value={newPassword}
                    aria-label="New Carleton password"
                    autoComplete="new-password"
                    placeholder="New Carleton password"
                    onChange={e => setNewPassword(e.target.value)}
                    onKeyDown={e => { if (e.key === 'Enter') handleSavePassword(); if (e.key === 'Escape') handleCancelPassword(); }}
                    autoFocus
                  />
                  <button className="btn-save" disabled={savingPassword || !newPassword} onClick={handleSavePassword}>
                    {savingPassword ? 'Verifying...' : 'Save'}
                  </button>
                  <button className="btn-cancel-inline" disabled={savingPassword} onClick={handleCancelPassword}>
                    Cancel
                  </button>
                </div>
              ) : (
                <div className="email-display-row">
                  <span className="profile-field-value">••••••••</span>
                  <button className="btn-edit" onClick={() => guardDemo(() => setEditingPassword(true))}>Change</button>
                </div>
              )}
              {editingPassword && (
                <span className="profile-field-hint">
                  Update this whenever you change your Carleton password, otherwise grade checking will stop working.
                </span>
              )}
            </div>
          </div>
        </div>

        <section className="profile-card" aria-labelledby="notification-settings-title">
          <div className="profile-card-header">
            <h2 className="profile-card-title" id="notification-settings-title">Notifications</h2>
            <p>Choose where grade updates go, or pause them for a while.</p>
          </div>
          <div className="profile-card-body">
            <div className="profile-field">
              <span className="profile-field-label">Notification email</span><span className="profile-field-hint">Grade updates are sent to this address.</span>
              {editingEmail ? (
                <div className="email-edit-stack">
                  <input
                    className="profile-field-input"
                    type="email"
                    aria-label="New notification email"
                    value={newEmail}
                    placeholder={email}
                    onChange={e => setNewEmail(e.target.value)}
                    onKeyDown={e => { if (e.key === 'Escape') handleCancelEmail(); }}
                    autoFocus
                  />
                  <input
                    className="profile-field-input"
                    type="password"
                    value={emailCurrentPassword}
                    aria-label="Current password"
                    autoComplete="current-password"
                    placeholder="Current password"
                    onChange={e => setEmailCurrentPassword(e.target.value)}
                    onKeyDown={e => { if (e.key === 'Enter') handleSaveEmail(); if (e.key === 'Escape') handleCancelEmail(); }}
                  />
                  <div className="email-edit-actions">
                    <button className="btn-save" disabled={savingEmail || !newEmail || !emailCurrentPassword} onClick={handleSaveEmail}>
                      {savingEmail ? 'Saving...' : 'Save'}
                    </button>
                    <button className="btn-cancel-inline" disabled={savingEmail} onClick={handleCancelEmail}>
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <div className="email-display-row">
                  <span className="profile-field-value">{email || '—'}</span>
                  <button className="btn-edit" onClick={() => guardDemo(() => setEditingEmail(true))}>Change</button>
                </div>
              )}
            </div>

            <div className="notification-preference" aria-busy={savingGradeEmails}>
              <div className="notification-preference-heading">
                <div>
                  <span className="profile-field-label" id="grade-emails-label">Grade update emails</span>
                  <p className="profile-field-hint" id="grade-emails-description">Email me when a grade changes on Carleton Central.</p>
                </div>
                <button
                  type="button"
                  role="switch"
                  aria-checked={gradeEmails === true}
                  aria-labelledby="grade-emails-label"
                  aria-describedby="grade-emails-description"
                  className={`profile-switch${gradeEmails ? ' is-on' : ''}`}
                  disabled={gradeEmails === null || savingGradeEmails}
                  onClick={() => guardDemo(toggleGradeEmails)}
                >
                  <span className="profile-switch-thumb" />
                </button>
              </div>
              <div className="notification-preference-status" role="status">
                <span className="notification-status-label">{savingGradeEmails ? 'Saving…' : gradeEmails === null ? 'Loading…' : gradeEmails ? 'Enabled' : 'Paused'}</span>
                <span>{gradeEmails === false ? 'Automatic checks are paused. You can still refresh grades from your dashboard.' : 'Automatic checks run in the background while grade emails are enabled.'}</span>
              </div>
            </div>
            <p className="profile-field-hint notification-account-note">Account confirmations are still sent when grade emails are paused.</p>
          </div>
        </section>

        <div className="profile-card">
          <div className="profile-card-header">
            <h2 className="profile-card-title">Security & privacy</h2><p>How your account information is handled.</p>
          </div>
          <div className="profile-card-body">
            <div className="profile-field">
              <span className="profile-field-label profile-security-title"><ShieldCheck size={16} /> Encrypted credentials</span>
              <span className="profile-field-value">
                Your Carleton credentials are encrypted using AES-128 and used to fetch your grades. Your saved password is never displayed here.
              </span>
            </div>
          </div>
        </div>

        <div className="profile-card danger-card">
          <div className="profile-card-header">
            <h2 className="profile-card-title">Delete account</h2><p>Permanently remove your data from CU Scraper.</p>
          </div>
          <div className="profile-card-body">
            <p className="danger-description">
              Permanently delete your CU Scraper account and all associated data, including your stored credentials and grade history. This does not affect your real Carleton University account and cannot be undone.
            </p>
            <button className="btn-danger" onClick={() => guardDemo(() => setShowConfirm(true))}>
              Delete account
            </button>
          </div>
        </div>
        <footer className="dashboard-footer"><div className="public-footer-links"><span>CU Scraper</span><Link to="/about">About & privacy</Link></div><span>Independent project. Not affiliated with Carleton University.</span></footer>
      </main>

      {showConfirm && (
        <div className="confirm-overlay" onClick={() => !deleting && handleCancelDelete()}>
          <div className="confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="delete-account-title" onClick={e => e.stopPropagation()}>
            <h2 id="delete-account-title">Delete your account?</h2>
            <p>
              This will permanently delete your CU Scraper account, stored Carleton credentials, and all grade data.
              You will be logged out immediately. This does not affect your real Carleton University account.
            </p>
            <input
              className="profile-field-input"
              type="password"
              value={deleteCurrentPassword}
              aria-label="Password to confirm account deletion"
              autoComplete="current-password"
              placeholder="Enter your password to confirm"
              onChange={e => setDeleteCurrentPassword(e.target.value)}
              onKeyDown={e => { if (e.key === 'Escape' && !deleting) handleCancelDelete(); }}
              autoFocus
            />
            <div className="confirm-actions">
              <button className="btn-cancel" disabled={deleting} onClick={handleCancelDelete}>
                Cancel
              </button>
              <button className="btn-confirm-delete" disabled={deleting || !deleteCurrentPassword} onClick={handleDeleteAccount}>
                {deleting ? 'Deleting...' : 'Yes, delete my account'}
              </button>
            </div>
          </div>
        </div>
      )}

      {notification && <div className="notification-toast" role="status">{notification}</div>}
    </div>
  );
}
