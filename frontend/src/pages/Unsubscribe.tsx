import { useState } from 'react';
import { Link, useSearchParams } from 'react-router';
import { ArrowLeft, BellOff, Check, CheckCircle2, Link2Off, RefreshCw } from 'lucide-react';
import { PublicShell } from '../components/PublicShell.tsx';
import { isTimeout, QUICK_TIMEOUT } from '../utils/errors.ts';
import './Unsubscribe.css';

type Status = 'confirm' | 'submitting' | 'done' | 'invalid' | 'error';

export function Unsubscribe() {
  const [params] = useSearchParams();
  const token = params.get('token') ?? '';
  return <UnsubscribeFlow key={token} token={token} />;
}

function UnsubscribeFlow({ token }: { token: string }) {
  const [status, setStatus] = useState<Status>(token ? 'confirm' : 'invalid');
  const [errorMessage, setErrorMessage] = useState('');
  const submitting = status === 'submitting';
  const done = status === 'done';
  const invalid = status === 'invalid';

  async function confirmUnsubscribe() {
    if (submitting || done || invalid) return;
    setStatus('submitting');
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/unsubscribe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token }),
        signal: AbortSignal.timeout(QUICK_TIMEOUT),
      });
      if (response.ok) {
        setStatus('done');
      } else if (response.status === 400 || response.status === 422) {
        setStatus('invalid');
      } else {
        setErrorMessage(response.status === 429 ? 'Too many attempts. Please wait a moment and try again.' : 'We couldn’t save this change. Please try again.');
        setStatus('error');
      }
    } catch (err) {
      setErrorMessage(isTimeout(err) ? 'The request timed out. Please try again.' : 'We couldn’t connect right now. Please try again.');
      setStatus('error');
    }
  }

  return (
    <PublicShell>
      <main className="unsubscribe-content" aria-labelledby="unsubscribe-title">
        <div className="unsubscribe-panel">
          <p className="public-eyebrow">NOTIFICATION PREFERENCES</p>
          <div className="unsubscribe-heading-icon" aria-hidden="true">
            {done ? <CheckCircle2 size={25} strokeWidth={1.5} /> : invalid ? <Link2Off size={25} strokeWidth={1.5} /> : <BellOff size={25} strokeWidth={1.5} />}
          </div>
          <div aria-live="polite" aria-atomic="true">
            <h1 id="unsubscribe-title">{done ? 'Grade emails are paused.' : invalid ? 'This link isn’t valid.' : 'Unsubscribe from grade emails?'}</h1>
            <p className="unsubscribe-description">
              {done ? 'You’re unsubscribed from grade updates. Your CU Scraper account is still here whenever you need it.' : invalid ? 'The link may be incomplete or no longer valid. You can manage grade emails directly in your account settings.' : 'You can stop grade emails without deleting your account. You can turn them back on in Account anytime.'}
            </p>
          </div>
          {!invalid && (
            <section className="unsubscribe-summary" aria-label={done ? 'Your updated preferences' : 'What will change'}>
              <h2>{done ? 'Your updated preferences' : 'What will change'}</h2>
              <dl>
                <div><dt>Grade update emails</dt><dd>{done ? 'Paused' : 'Will pause'}</dd></div>
                <div><dt>Automatic grade checks</dt><dd>{done ? 'Paused' : 'Will pause'}</dd></div>
                <div><dt>Your account & saved grades</dt><dd><Check size={14} aria-hidden="true" />Kept</dd></div>
              </dl>
              <p>You can still refresh your grades manually from the dashboard.</p>
            </section>
          )}
          {status === 'error' && <div className="public-alert unsubscribe-error" role="alert">{errorMessage}</div>}
          <div className="unsubscribe-actions" aria-busy={submitting}>
            {done || invalid ? (
              <>
                <Link className="public-primary" to="/app/profile">Open account settings</Link>
                <Link className="unsubscribe-back" to="/login"><ArrowLeft size={15} />Back to sign in</Link>
              </>
            ) : (
              <>
                <button className="public-primary" onClick={confirmUnsubscribe} disabled={submitting}>
                  {submitting && <RefreshCw className="unsubscribe-spinner" size={16} aria-hidden="true" />}
                  {submitting ? 'Unsubscribing…' : status === 'error' ? 'Try again' : 'Yes, unsubscribe'}
                </button>
                <Link className="public-secondary" to="/login">Keep getting updates</Link>
              </>
            )}
          </div>
          <p className="unsubscribe-footnote">{invalid ? 'You don’t need an unsubscribe link to change this in Account.' : 'Essential account emails, such as email-change and deletion confirmations, will still be sent.'}</p>
        </div>
      </main>
    </PublicShell>
  );
}
