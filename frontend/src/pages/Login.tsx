import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router';
import {useAuthContext} from '../context/AuthContext.tsx'
import { Eye, EyeOff } from 'lucide-react';
import './Login.css'

export function Login(){
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [errorMessage, setErrorMessage] = useState('')
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const errorTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);
  
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
  }, []);

  async function handleSignIn(){
    if (!username){
      displayErrorMsg('Username cannot be empty!')
      return;
    }
    if (!password){
      displayErrorMsg('Password cannot be empty!');
      return;
    }
    setLoading(true);
    const response = await fetch(`${import.meta.env.VITE_API_URL}/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({username, password}),
    });
    const data = await response.json();
    if (!response.ok){
      displayErrorMsg(data.detail);
    } else {
      localStorage.setItem('token', data.accessToken);
      setToken(data.accessToken);
      navigate("/app/dashboard");
    }
    setLoading(false);
  }

  function handleMouseDown(){
    setShowPassword(true); 
  }

  function handleMouseUp(){
    setShowPassword(false);
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
            <input value={username} onChange={v => setUsername(v.target.value)}/>
          </div>
          <div className="password-section">
            <label>Password</label>
            <div className="input-wrapper">
              <input type={showPassword ? "text" : "password"} value={password} onChange={v => setPassword(v.target.value)}/>
              <button className="view-password" onMouseDown={handleMouseDown} onMouseUp={handleMouseUp}>{showPassword ? <EyeOff size={16} /> : <Eye size={16} />}</button>
            </div>
          </div>
            <button className="signinbutton" disabled={loading} onClick={handleSignIn}>Sign in</button>
            <button className="registerpage" onClick={redirectRegisterPage}>Create an account</button>
        </div>
      </div>
    </div>
  )
}
