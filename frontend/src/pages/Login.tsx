import { useState } from 'react'
import { useNavigate } from 'react-router';
import {useAuthContext} from '../context/AuthContext.tsx'

export function Login(){
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [errorMessage, setErrorMessage] = useState('')
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  
  const {setToken} = useAuthContext();
  const navigate = useNavigate();

  async function handleSignIn(){
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
      setErrorMessage(data.detail);
      setTimeout(() => {
        setErrorMessage(''); 
      }, 3000);
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
        <input type={showPassword ? "text" : "password"} value={password} onChange={v => setPassword(v.target.value)}/>
        <button className="view-password" onMouseDown={handleMouseDown} onMouseUp={handleMouseUp}></button>
      </div>
      <p className="error-msg">{errorMessage}</p>
      <button className="signinbutton" disabled={loading} onClick={handleSignIn}>Sign in</button>
      <button className="registerpage" onClick={redirectRegisterPage}>Create an account</button>
    </div>
  )
}
