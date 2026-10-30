import { Link } from 'react-router';
import { ArrowLeft } from 'lucide-react';
import { useAuthContext } from '../context/AuthContext.tsx';
import { PublicShell } from '../components/PublicShell.tsx';

export function NotFound() {
  const { token } = useAuthContext();
  return (
    <PublicShell>
      <main className="public-state">
        <p className="public-eyebrow">PAGE NOT FOUND</p>
        <div className="public-status-code" aria-hidden="true">404<span>.</span></div>
        <h1>This page isn’t here.</h1>
        <p>The link may be incorrect, or the page may have moved.</p>
        <Link className="public-primary" to={token ? '/app/dashboard' : '/login'} replace><ArrowLeft size={15} />{token ? 'Back to dashboard' : 'Back to sign in'}</Link>
      </main>
    </PublicShell>
  );
}
