import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router';
import { ArrowLeft, RefreshCw } from 'lucide-react';
import { useAuthContext } from '../context/AuthContext.tsx';
import { QUICK_TIMEOUT } from '../utils/errors.ts';
import { PublicShell } from '../components/PublicShell.tsx';

export function Demo() {
  const { setToken } = useAuthContext();
  const navigate = useNavigate();
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const pending = useRef<Promise<string> | null>(null);

  useEffect(() => {
    let active = true;
    if (!pending.current) {
      pending.current = (async () => {
        const response = await fetch(`${import.meta.env.VITE_API_URL}/demo`, {
          method: 'POST',
          signal: AbortSignal.timeout(QUICK_TIMEOUT),
        });
        if (!response.ok) throw new Error('Demo unavailable');
        const data = await response.json();
        if (typeof data.accessToken !== 'string' || !data.accessToken) throw new Error('Invalid demo response');
        return data.accessToken as string;
      })();
    }
    pending.current.then(token => {
      if (!active) return;
      localStorage.setItem('token', token);
      setToken(token);
      navigate('/app/dashboard', { replace: true });
    }).catch(() => { if (active) setFailed(true); });
    return () => { active = false; };
  }, [attempt, navigate, setToken]);

  function retry() {
    pending.current = null;
    setFailed(false);
    setAttempt(value => value + 1);
  }

  return (
    <PublicShell>
      <main className="public-state" aria-busy={!failed}>
        <p className="public-eyebrow">EXPLORE CU SCRAPER</p>
        <div className={`public-state-icon ${failed ? '' : 'public-loading'}`} aria-hidden="true"><RefreshCw size={28} strokeWidth={1.5} /></div>
        <h1>{failed ? 'The demo couldn’t load.' : 'Opening the demo.'}</h1>
        <p>{failed ? 'We couldn’t connect right now. Try again, or head back to sign in.' : 'Getting a sample account ready so you can explore without using your Carleton login.'}</p>
        <div className="public-state-actions">
          {failed && <button className="public-primary" onClick={retry}>Try again <RefreshCw size={15} /></button>}
          <Link className="public-secondary" to="/login" replace><ArrowLeft size={15} />Back to sign in</Link>
        </div>
        <span className="public-state-note" role="status">{failed ? 'No account details are needed to try the demo.' : 'Sample grades. No account changes or real grade checks.'}</span>
      </main>
    </PublicShell>
  );
}
