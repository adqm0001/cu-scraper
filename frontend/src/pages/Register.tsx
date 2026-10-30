import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router';
import {useAuthContext} from '../context/AuthContext.tsx'
import { getAuthErrorMessage, isTimeout, SCRAPE_TIMEOUT } from '../utils/errors.ts'
import { Eye, EyeOff } from 'lucide-react';
import { PublicShell, AuthIntroduction } from '../components/PublicShell.tsx';

export function Register(){
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [email, setEmail] = useState('')
  const [errorMessage, setErrorMessage] = useState('')
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const errorTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mounted = useRef(true);

  const {setToken} = useAuthContext();
  const navigate = useNavigate();

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      if (errorTimeout.current) clearTimeout(errorTimeout.current);
    };
  }, []);

  function displayErrorMsg(msg: string){
   if (errorTimeout.current) clearTimeout(errorTimeout.current);
   setErrorMessage(msg);
   errorTimeout.current = setTimeout(() => setErrorMessage(''), 3000);
  }

  async function handleSignUp(){
    if (loading) return;
    if (!username){
      displayErrorMsg('Please enter your Carleton username.')
      return;
    }
    if (!password){
      displayErrorMsg('Please enter your password.');
      return;
    }
    if (!email){
      displayErrorMsg('Please enter your notification email.');
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)){
      displayErrorMsg('Please enter a valid email address.');
      return;
    }
    setLoading(true);
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({username, password, email}),
        signal: AbortSignal.timeout(SCRAPE_TIMEOUT),
      });
      const data = await response.json().catch(() => ({}));
      if (!mounted.current) return;
      if (!response.ok){
        displayErrorMsg(getAuthErrorMessage(response.status, data.detail, 'register'));
      } else {
        localStorage.setItem('token', data.accessToken);
        setToken(data.accessToken);
        navigate("/app/dashboard");
      }
    } catch (err) {
      if (mounted.current) displayErrorMsg(isTimeout(err) ? 'Registration is taking too long. Please try again.' : 'Network error. Please check your connection and try again.');
    } finally {
      if (mounted.current) setLoading(false);
    }
  }

  function toggleShowPassword(){
    setShowPassword(prev => !prev);
  }

  function redirectLoginPage(){
    navigate("/login");
  }

  return (
    <PublicShell>
      <main className="auth-layout">
        <AuthIntroduction />
        <section className="auth-form-section" aria-labelledby="register-title">
          <p className="public-eyebrow">GET STARTED</p>
          <h1 id="register-title">Create your account.</h1>
          <p className="auth-form-description">Connect your Carleton login to start tracking your grades.</p>
          <form onSubmit={e => { e.preventDefault(); handleSignUp(); }} aria-busy={loading}>
            <div className="auth-field">
              <label htmlFor="register-username">Carleton username</label>
              <input id="register-username" autoComplete="username" autoCapitalize="none" spellCheck={false} value={username} onChange={e => setUsername(e.target.value)} placeholder="Your Carleton username" />
            </div>
            <div className="auth-field">
              <label htmlFor="register-password">Carleton password</label>
              <div className="auth-password">
                <input id="register-password" type={showPassword ? 'text' : 'password'} autoComplete="current-password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Your current Carleton password" />
                <button type="button" onClick={toggleShowPassword} aria-label={showPassword ? 'Hide password' : 'Show password'} aria-pressed={showPassword}>{showPassword ? <EyeOff size={17} /> : <Eye size={17} />}</button>
              </div>
            </div>
            <div className="auth-field">
              <label htmlFor="register-email">Notification email</label>
              <input id="register-email" type="email" autoComplete="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" />
              <span className="auth-field-note">We’ll send grade updates to this address.</span>
            </div>
            {errorMessage && <p className="public-alert" role="alert">{errorMessage}</p>}
            <button className="public-primary auth-submit" disabled={loading} type="submit">{loading ? 'Registering...' : 'Create account'}</button>
            <p className="auth-field-note auth-verification-note">We verify your login with Carleton before creating your account. This can take a moment.</p>
          </form>
          <p className="auth-switch">Already have an account? <button type="button" onClick={redirectLoginPage}>Sign in</button></p>
        </section>
      </main>
    </PublicShell>
  );
}
