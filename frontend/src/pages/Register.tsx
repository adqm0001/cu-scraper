import { useState, useRef } from 'react'
import { useNavigate } from 'react-router';
import {useAuthContext} from '../context/AuthContext.tsx'

export function Register(){
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [email, setEmail] = useState('')
  const [errorMessage, setErrorMessage] = useState('')
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const errorTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);
  
  const {setToken} = useAuthContext();
  const navigate = useNavigate();

  function displayErrorMsg(msg: string){
   if (errorTimeout.current) clearTimeout(errorTimeout.current);
   setErrorMessage(msg);
   errorTimeout.current = setTimeout(() => setErrorMessage(''), 3000);
  }

  async function handleSignUp(){
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
    const response = await fetch(`${import.meta.env.VITE_API_URL}/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({username, password, email}),
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

  function redirectLoginPage(){
    navigate("/login");
  }

  return(
    <div className="register-component">
      <div className="register-title">
        <h1>Register</h1>
      </div>
      <div className="username-section">
        <label>Username</label>
        <input value={username} onChange={v => setUsername(v.target.value)}/>
      </div>
      <div className="password-section">
        <label>Password</label>
        <input type={showPassword ? "text" : "password"} value={password} onChange={v => setPassword(v.target.value)}/>
        <button className="view-password" onMouseDown={handleMouseDown} onMouseUp={handleMouseUp}></button>
      </div>
      <div className="email-section">
        <label>Email</label>
        <input value={email} onChange={v => setEmail(v.target.value)} onKeyDown={e => e.key === 'Enter' && handleSignUp()}/>
      </div>
      <p className="error-msg">{errorMessage}</p>
      <button className="signupbutton" disabled={loading} onClick={handleSignUp}>{loading ? "Registering..." : "Sign up"}</button>
      <button className="loginpage" onClick={redirectLoginPage}>Already have an account</button>
    </div>
  )
}

