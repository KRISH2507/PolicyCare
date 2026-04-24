import React, { useState, useContext, useEffect } from 'react';
import { useNavigate, Link, Navigate } from 'react-router-dom';
import { SessionContext } from '../context/SessionContext';
import { apiPost } from '../api/client';
import styles from '../styles/LoginPage.module.css';

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';

const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [error, setError] = useState(null);

  const { setAuthToken, authToken, currentUser } = useContext(SessionContext);
  const navigate = useNavigate();

  if (authToken) {
    return <Navigate to={currentUser?.role === 'admin' ? '/admin' : '/profile'} replace />;
  }

  /* ── Load Google Identity Services script ── */
  useEffect(() => {
    if (!GOOGLE_CLIENT_ID) return;
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    document.head.appendChild(script);
    return () => document.head.removeChild(script);
  }, []);

  /* ── Email / password login ── */
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await apiPost('/api/auth/login', { email, password });
      setAuthToken(response.access_token, {
        email: response.email,
        full_name: response.full_name,
        role: response.role,
      });
      navigate(response.role === 'admin' ? '/admin' : '/profile');
    } catch (err) {
      setError(err.message || 'Incorrect email or password');
    } finally {
      setLoading(false);
    }
  };

  /* ── Google Sign-In callback ── */
  const handleGoogleSignIn = () => {
    if (!GOOGLE_CLIENT_ID || !window.google) {
      setError('Google Sign-In is not configured. Please use email login.');
      return;
    }
    setGoogleLoading(true);
    setError(null);

    window.google.accounts.id.initialize({
      client_id: GOOGLE_CLIENT_ID,
      callback: async (credentialResponse) => {
        try {
          const response = await apiPost('/api/auth/google', {
            id_token: credentialResponse.credential,
          });
          setAuthToken(response.access_token, {
            email: response.email,
            full_name: response.full_name,
            role: response.role,
          });
          navigate('/profile');
        } catch (err) {
          setError(err.message || 'Google Sign-In failed. Please try again.');
        } finally {
          setGoogleLoading(false);
        }
      },
    });

    window.google.accounts.id.prompt((notification) => {
      if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
        setGoogleLoading(false);
        // Fallback: render the button popup
        window.google.accounts.id.renderButton(
          document.getElementById('google-btn-container'),
          { theme: 'outline', size: 'large', width: 328 }
        );
      }
    });
  };

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <div className={styles.header}>
          <h2>AarogyaAid</h2>
          <p>Sign in to continue</p>
        </div>

        {/* Google Sign-In */}
        {GOOGLE_CLIENT_ID && (
          <>
            <div id="google-btn-container" />
            <button
              type="button"
              className={styles.googleButton}
              onClick={handleGoogleSignIn}
              disabled={googleLoading || loading}
            >
              <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
                <path fill="#4285F4" d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.875 2.684-6.615z"/>
                <path fill="#34A853" d="M9 18c2.43 0 4.467-.806 5.956-2.184l-2.908-2.258c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z"/>
                <path fill="#FBBC05" d="M3.964 10.707A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.707V4.961H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.039l3.007-2.332z"/>
                <path fill="#EA4335" d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.961L3.964 7.293C4.672 5.163 6.656 3.58 9 3.58z"/>
              </svg>
              {googleLoading ? 'Signing in…' : 'Continue with Google'}
            </button>

            <div className={styles.divider}>
              <span>or</span>
            </div>
          </>
        )}

        {/* Email / password form */}
        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.field}>
            <label htmlFor="login-email">Email</label>
            <input
              id="login-email"
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="you@example.com"
              disabled={loading}
              required
              autoComplete="email"
            />
          </div>
          <div className={styles.field}>
            <label htmlFor="login-password">Password</label>
            <input
              id="login-password"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="Your password"
              disabled={loading}
              required
              autoComplete="current-password"
            />
          </div>
          <button type="submit" disabled={loading || googleLoading} className={styles.button}>
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
          {error && <div className={styles.error}>{error}</div>}
        </form>

        <p className={styles.switchLink}>
          Don't have an account? <Link to="/signup">Sign up</Link>
        </p>
      </div>
    </div>
  );
};

export default LoginPage;
