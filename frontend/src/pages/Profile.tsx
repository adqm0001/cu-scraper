import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router';
import { useAuthContext } from '../context/AuthContext.tsx';
import './Profile.css';

export function Profile() {
  const { token, setToken } = useAuthContext();
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [newEmail, setNewEmail] = useState('');
  const [editingEmail, setEditingEmail] = useState(false);
  const [savingEmail, setSavingEmail] = useState(false);
  const [newPassword, setNewPassword] = useState('');
  const [editingPassword, setEditingPassword] = useState(false);
  const [savingPassword, setSavingPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [notification, setNotification] = useState('');
  const notificationTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  function showNotification(msg: string) {
    if (notificationTimeout.current) clearTimeout(notificationTimeout.current);
    setNotification(msg);
    notificationTimeout.current = setTimeout(() => setNotification(''), 3000);
  }

  function logOut() {
    localStorage.removeItem('token');
    setToken('');
    navigate('/login');
  }

  useEffect(() => {
    async function fetchMe() {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/users/me`, {
        method: 'GET',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.status === 401) { logOut(); return; }
      const data = await response.json();
      setUsername(data.username);
      setEmail(data.email);
    }
    fetchMe();
    return () => { if (notificationTimeout.current) clearTimeout(notificationTimeout.current); };
  }, []);

  async function handleSaveEmail() {
    if (!newEmail) return;
    setSavingEmail(true);
    const response = await fetch(`${import.meta.env.VITE_API_URL}/users/me/email`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ email: newEmail }),
    });
    setSavingEmail(false);
    if (response.ok) {
      setEmail(newEmail);
      setNewEmail('');
      setEditingEmail(false);
      showNotification('Email updated');
    } else {
      showNotification('Failed to update email. Please try again.');
    }
  }

  function handleCancelEmail() {
    setNewEmail('');
    setEditingEmail(false);
  }

  async function handleSavePassword() {
    if (!newPassword) return;
    setSavingPassword(true);
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/users/me/password`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ password: newPassword }),
      });
      if (response.ok) {
        setNewPassword('');
        setEditingPassword(false);
        showNotification('Carleton password updated');
      } else if (response.status === 401) {
        showNotification('Could not verify that password with Carleton. Double-check it.');
      } else {
        showNotification('Failed to update password. Please try again.');
      }
    } catch {
      showNotification('Network error. Please try again.');
    } finally {
      setSavingPassword(false);
    }
  }

  function handleCancelPassword() {
    setNewPassword('');
    setEditingPassword(false);
  }

  async function handleDeleteAccount() {
    setDeleting(true);
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/users/me`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        logOut();
      } else {
        setShowConfirm(false);
        showNotification('Failed to delete account. Please try again.');
      }
    } catch {
      setShowConfirm(false);
      showNotification('Network error. Please try again.');
    } finally {
      setDeleting(false);
    }
  }

  return (
    <div className="profile-page">
      <nav className="profile-nav">
        <span className="nav-logo" onClick={() => navigate('/app/dashboard')}>CU SCRAPER</span>
        <div className="nav-actions">
          <button className="btn-outline" onClick={() => navigate('/app/dashboard')}>Dashboard</button>
          <button className="btn-outline" onClick={logOut}>Log out</button>
        </div>
      </nav>

      <main className="profile-content">
        <h1 className="profile-heading">Profile</h1>

        <div className="profile-card">
          <div className="profile-card-header">
            <span className="profile-card-title">Account</span>
          </div>
          <div className="profile-card-body">
            <div className="profile-field">
              <span className="profile-field-label">Username</span>
              <span className="profile-field-value">{username || '—'}</span>
            </div>

            <div className="profile-field">
              <span className="profile-field-label">Notification Email</span>
              {editingEmail ? (
                <div className="email-edit-row">
                  <input
                    className="profile-field-input"
                    type="email"
                    value={newEmail}
                    placeholder={email}
                    onChange={e => setNewEmail(e.target.value)}
                    onKeyDown={e => { if (e.key === 'Enter') handleSaveEmail(); if (e.key === 'Escape') handleCancelEmail(); }}
                    autoFocus
                  />
                  <button className="btn-save" disabled={savingEmail || !newEmail} onClick={handleSaveEmail}>
                    {savingEmail ? 'Saving...' : 'Save'}
                  </button>
                  <button className="btn-cancel-inline" disabled={savingEmail} onClick={handleCancelEmail}>
                    Cancel
                  </button>
                </div>
              ) : (
                <div className="email-display-row">
                  <span className="profile-field-value">{email || '—'}</span>
                  <button className="btn-edit" onClick={() => setEditingEmail(true)}>Change</button>
                </div>
              )}
            </div>

            <div className="profile-field">
              <span className="profile-field-label">Carleton Password</span>
              {editingPassword ? (
                <div className="email-edit-row">
                  <input
                    className="profile-field-input"
                    type="password"
                    value={newPassword}
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
                  <button className="btn-edit" onClick={() => setEditingPassword(true)}>Change</button>
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

        <div className="profile-card">
          <div className="profile-card-header">
            <span className="profile-card-title">Security</span>
          </div>
          <div className="profile-card-body">
            <div className="profile-field">
              <span className="profile-field-label">Credential Storage</span>
              <span className="profile-field-value">
                Your Carleton credentials are stored using AES-128 encryption and are never shared or used outside of grade fetching.
              </span>
            </div>
          </div>
        </div>

        <div className="profile-card danger-card">
          <div className="profile-card-header">
            <span className="profile-card-title">Danger Zone</span>
          </div>
          <div className="profile-card-body">
            <p className="danger-description">
              Permanently delete your CU Scraper account and all associated data, including your stored credentials and grade history. This does not affect your real Carleton University account and cannot be undone.
            </p>
            <button className="btn-danger" onClick={() => setShowConfirm(true)}>
              Delete Account
            </button>
          </div>
        </div>
      </main>

      {showConfirm && (
        <div className="confirm-overlay" onClick={() => !deleting && setShowConfirm(false)}>
          <div className="confirm-dialog" onClick={e => e.stopPropagation()}>
            <h2>Delete Account</h2>
            <p>
              This will permanently delete your CU Scraper account, stored Carleton credentials, and all grade data.
              You will be logged out immediately. This does not affect your real Carleton University account.
            </p>
            <div className="confirm-actions">
              <button className="btn-cancel" disabled={deleting} onClick={() => setShowConfirm(false)}>
                Cancel
              </button>
              <button className="btn-confirm-delete" disabled={deleting} onClick={handleDeleteAccount}>
                {deleting ? 'Deleting...' : 'Yes, delete my account'}
              </button>
            </div>
          </div>
        </div>
      )}

      {notification && <div className="notification-toast">{notification}</div>}
    </div>
  );
}
