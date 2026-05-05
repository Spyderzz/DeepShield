import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { fetchMe, setAuth } from '../services/authApi.js';

export default function OAuthCallbackPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState('Completing sign in…');

  useEffect(() => {
    const token = searchParams.get('token');
    const next = searchParams.get('next') || '/analyze';
    const remember = searchParams.get('remember') !== '0';

    if (!token) {
      navigate('/login', { replace: true });
      return;
    }

    (async () => {
      try {
        setStatus('Saving session…');
        setAuth(token, null, remember);
        const user = await fetchMe();
        setAuth(token, user, remember);
        setStatus('Redirecting…');
        window.location.assign(next.startsWith('/') ? next : '/analyze');
      } catch (_err) {
        setStatus('Sign-in failed. Redirecting…');
        window.location.assign('/login');
      }
    })();
  }, [navigate, searchParams]);

  return (
    <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', color: 'var(--ds-muted)' }}>
      <div>{status}</div>
    </div>
  );
}