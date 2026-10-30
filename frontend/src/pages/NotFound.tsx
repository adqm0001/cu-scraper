import { useNavigate } from 'react-router';
import { useAuthContext } from '../context/AuthContext.tsx';
import './NotFound.css';

export function NotFound() {
  const { token } = useAuthContext();
  const navigate = useNavigate();

  return (
    <div className="notfound-page">
      <h1 className="notfound-code">404</h1>
      <p className="notfound-title">Page not found</p>
      <p className="notfound-text">The page you're looking for doesn't exist or was moved.</p>
      <button
        className="notfound-btn"
        onClick={() => navigate(token ? '/app/dashboard' : '/login', { replace: true })}
      >
        {token ? 'Back to dashboard' : 'Back to login'}
      </button>
    </div>
  );
}
