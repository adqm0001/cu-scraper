import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router';
import {useAuthContext} from '../context/AuthContext.tsx'
import { getAuthErrorMessage } from '../utils/errors.ts'
import { Eye, EyeOff } from 'lucide-react';
import './Login.css'

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

  function displayErrorMsg(msg: string){
   if (errorTimeout.current) clearTimeout(errorTimeout.current);
   setErrorMessage(msg);
   errorTimeout.current = setTimeout(() => setErrorMessage(''), 3000);
  }

  useEffect(() => {
    if (token){
      navigate('/app/dashboard', { replace: true});
    }
    return () => {
      mounted.current = false;
      if (errorTimeout.current) clearTimeout(errorTimeout.current);
    };
  }, []);

  async function handleSignIn(){
    if (loading) return;
    if (!username){
      displayErrorMsg('Username cannot be empty!')
      return;
    }
    if (!password){
      displayErrorMsg('Password cannot be empty!');
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
    } catch {
      if (mounted.current) displayErrorMsg('Network error. Please check your connection and try again.');
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

  return(
    <div className="login-page">
      <div className="login-left">
        <h2>Cu Scraper</h2>
        <p>Your grades, monitored automatically. We store your Carleton credentials securely using AES-128 encryption and are not affiliated with Carleton University.</p>
      </div>
      <div className="login-right">
        <div className="login-component">
          <div className="login-title">
            <h1>Login</h1>
          </div>
          <div className="username-section">
            <label>Username</label>
            <input value={username} onChange={v => setUsername(v.target.value)} onKeyDown={e => e.key === 'Enter' && handleSignIn()}/>
          </div>
          <div className="password-section">
            <label>Password</label>
            <div className="input-wrapper">
              <input type={showPassword ? "text" : "password"} value={password} onChange={v => setPassword(v.target.value)} onKeyDown={e => e.key === 'Enter' && handleSignIn()}/>
              <button type="button" className="view-password" onClick={toggleShowPassword}>{showPassword ? <EyeOff size={16} /> : <Eye size={16} />}</button>
            </div>
          </div>
          {errorMessage && <p className="error-msg">{errorMessage}</p>}
            <button className="signinbutton" disabled={loading} onClick={handleSignIn}>{loading ? 'Signing in...' : 'Sign in'}</button>
            <button className="registerpage" onClick={redirectRegisterPage}>Create an account</button>
        </div>
      </div>
    </div>
  )
}
