import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router';
import {useAuthContext} from '../context/AuthContext.tsx'
import { getAuthErrorMessage, isTimeout, SCRAPE_TIMEOUT } from '../utils/errors.ts'
import { Eye, EyeOff } from 'lucide-react';
import './Register.css'

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
      displayErrorMsg('Username cannot be empty!')
      return;
    }
    if (!password){
      displayErrorMsg('Password cannot be empty!');
      return;
    }
    if (!email){
      displayErrorMsg('Email cannot be empty!');
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

  return(
    <div className="register-page">
      <div className="register-left">
        <h2>Cu Scraper</h2>
        <p>Your grades, monitored automatically. We store your Carleton credentials securely using AES-128 encryption and are not affiliated with Carleton University.</p>
      </div>
      <div className="register-right">
        <div className="register-component">
          <div className="register-title">
            <h1>Register</h1>
          </div>
          <div className="username-section">
            <label>Username</label>
            <input value={username} onChange={v => setUsername(v.target.value)} onKeyDown={e => e.key === 'Enter' && handleSignUp()}/>
          </div>
          <div className="password-section">
            <label>Password</label>
            <div className="input-wrapper">
              <input type={showPassword ? "text" : "password"} value={password} onChange={v => setPassword(v.target.value)} onKeyDown={e => e.key === 'Enter' && handleSignUp()}/>
              <button type="button" className="view-password" onClick={toggleShowPassword}>{showPassword ? <EyeOff size={16} /> : <Eye size={16} />}</button>
            </div>
          </div>
          <div className="email-section">
            <label>Email</label>
            <input value={email} onChange={v => setEmail(v.target.value)} onKeyDown={e => e.key === 'Enter' && handleSignUp()}/>
          </div>
          {errorMessage && <p className="error-msg">{errorMessage}</p>}
          <button className="signupbutton" disabled={loading} onClick={handleSignUp}>{loading ? "Registering..." : "Sign up"}</button>
          <button className="loginpage" onClick={redirectLoginPage}>Already have an account</button>
        </div>
      </div>
    </div>
  )
}
