import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router';
import { useAuthContext } from '../context/AuthContext.tsx';
import { QUICK_TIMEOUT } from '../utils/errors.ts';
import './NotFound.css';

export function Demo() {
  const { setToken } = useAuthContext();
  const navigate = useNavigate();
  const [failed, setFailed] = useState(false);
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;

    async function startDemo() {
      try {
        const response = await fetch(`${import.meta.env.VITE_API_URL}/demo`, {
          method: 'POST',
          signal: AbortSignal.timeout(QUICK_TIMEOUT),
        });
        if (!response.ok) throw new Error(`demo failed: ${response.status}`);
        const data = await response.json();
        localStorage.setItem('token', data.accessToken);
        setToken(data.accessToken);
        navigate('/app/dashboard', { replace: true });
      } catch {
        setFailed(true);
      }
    }
    startDemo();
  }, []);

  return (
    <div className="notfound-page">
      <p className="notfound-title">{failed ? 'Demo unavailable' : 'Loading demo...'}</p>
      {failed && (
        <>
          <p className="notfound-text">The demo couldn't be started right now. Please try again later.</p>
          <button className="notfound-btn" onClick={() => navigate('/login', { replace: true })}>
            Back to login
          </button>
        </>
      )}
    </div>
  );
}
