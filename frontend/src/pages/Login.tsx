import { useState, useEffect, useRef } from 'react'
import { Link, Navigate, useNavigate } from 'react-router';
import {useAuthContext} from '../context/AuthContext.tsx'
import { getAuthErrorMessage, isTimeout, QUICK_TIMEOUT } from '../utils/errors.ts'
import { ArrowLeft, ArrowUpRight, Eye, EyeOff } from 'lucide-react';
import { PublicShell, AuthIntroduction } from '../components/PublicShell.tsx';
import { readTokenClaims, isTokenUsable } from '../utils/session.ts';

export function Login(){
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [errorMessage, setErrorMessage] = useState('')
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const errorTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mounted = useRef(true);

  const {token, setToken} = useAuthContext();
  const navigate = useNavigate();
  const claims = token ? readTokenClaims(token) : null;
  const sessionUsable = isTokenUsable(claims);
  const sessionIsDemo = sessionUsable && claims?.demo === true;

  function displayErrorMsg(msg: string){
   if (errorTimeout.current) clearTimeout(errorTimeout.current);
   setErrorMessage(msg);
   errorTimeout.current = setTimeout(() => setErrorMessage(''), 3000);
  }

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      if (errorTimeout.current) clearTimeout(errorTimeout.current);
    };
  }, []);

  useEffect(() => {
    if (token && !sessionUsable) {
      localStorage.removeItem('token');
      setToken('');
    }
  }, [token, sessionUsable, setToken]);

  async function handleSignIn(){
    if (loading) return;
    if (!username){
      displayErrorMsg('Please enter your Carleton username.')
      return;
    }
    if (!password){
      displayErrorMsg('Please enter your password.');
      return;
    }
    setLoading(true);
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({username, password}),
        signal: AbortSignal.timeout(QUICK_TIMEOUT),
      });
      const data = await response.json().catch(() => ({}));
      if (!mounted.current) return;
      if (!response.ok){
        displayErrorMsg(getAuthErrorMessage(response.status, data.detail, 'login'));
      } else {
        localStorage.setItem('token', data.accessToken);
        setToken(data.accessToken);
        navigate("/app/dashboard");
      }
    } catch (err) {
      if (mounted.current) displayErrorMsg(isTimeout(err) ? 'The request timed out. Please try again.' : 'Network error. Please check your connection and try again.');
    } finally {
      if (mounted.current) setLoading(false);
    }
  }

  function toggleShowPassword(){
    setShowPassword(prev => !prev);
  }

  function redirectRegisterPage(){
    navigate("/register");
  }

  if (sessionUsable && !sessionIsDemo) {
    return <Navigate to="/app/dashboard" replace />;
  }

  return (
    <PublicShell>
      <main className="auth-layout">
        <AuthIntroduction />
        <section className="auth-form-section" aria-labelledby="login-title">
          {token && <Link className="auth-session-link" to="/app/dashboard"><ArrowLeft size={14} />{sessionIsDemo ? 'Back to demo' : 'Back to dashboard'}</Link>}
          <p className="public-eyebrow">WELCOME BACK</p>
          <h1 id="login-title">Sign in.</h1>
          <p className="auth-form-description">Use your CU Scraper account to view your grades.</p>
          <form onSubmit={e => { e.preventDefault(); handleSignIn(); }} aria-busy={loading}>
            <div className="auth-field">
              <label htmlFor="login-username">Carleton username</label>
              <input id="login-username" autoComplete="username" autoCapitalize="none" spellCheck={false} value={username} onChange={e => setUsername(e.target.value)} placeholder="Your Carleton username" />
            </div>
            <div className="auth-field">
              <label htmlFor="login-password">Password</label>
              <div className="auth-password">
                <input id="login-password" type={showPassword ? 'text' : 'password'} autoComplete="current-password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Your password" />
                <button type="button" onClick={toggleShowPassword} aria-label={showPassword ? 'Hide password' : 'Show password'} aria-pressed={showPassword}>{showPassword ? <EyeOff size={17} /> : <Eye size={17} />}</button>
              </div>
            </div>
            {errorMessage && <p className="public-alert" role="alert">{errorMessage}</p>}
            <button className="public-primary auth-submit" disabled={loading} type="submit">{loading ? 'Signing in...' : 'Sign in'}</button>
          </form>
          <p className="auth-switch">New to CU Scraper? <button type="button" onClick={redirectRegisterPage}>Create an account</button></p>
          <div className="auth-demo"><span>Want to have a look first?</span><button onClick={() => navigate('/demo')}>Explore the demo <ArrowUpRight size={15} aria-hidden="true" /></button></div>
        </section>
      </main>
    </PublicShell>
  );
}
