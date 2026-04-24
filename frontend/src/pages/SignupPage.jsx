import React, { useState, useContext, useEffect } from 'react';
import { useNavigate, Link, Navigate } from 'react-router-dom';
import { SessionContext } from '../context/SessionContext';
import { apiPost } from '../api/client';
import styles from '../styles/LoginPage.module.css';

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';

const SignupPage = () => {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [error, setError] = useState(null);

  const { setAuthToken, authToken, currentUser } = useContext(SessionContext);
  const navigate = useNavigate();

  if (authToken) {
    return <Navigate to={currentUser?.role === 'admin' ? '/admin' : '/profile'} replace />;
  }

  useEffect(() => {
    if (!GOOGLE_CLIENT_ID) return;
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    document.head.appendChild(script);
    return () => document.head.removeChild(script);
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (password !== confirm) {
      setError("Passwords don't match");
      return;
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await apiPost('/api/auth/signup', {
        email,
        password,
        full_name: fullName,
      });
      setAuthToken(response.access_token, {
        email: response.email,
        full_name: response.full_name,
        role: response.role,
      });
      navigate('/profile');
    } catch (err) {
      setError(err.message || 'Could not create account. Try a different email.');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignIn = () => {
    if (!GOOGLE_CLIENT_ID || !window.google) {
      setError('Google Sign-In is not configured. Please use email signup.');
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
      }
    });
  };

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <div className={styles.header}>
          <h2>AarogyaAid</h2>
          <p>Create your account</p>
        </div>

        {GOOGLE_CLIENT_ID && (
          <>
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
              {googleLoading ? 'Signing up…' : 'Continue with Google'}
            </button>
            <div className={styles.divider}><span>or</span></div>
          </>
        )}

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.field}>
            <label htmlFor="signup-name">Full name</label>
            <input
              id="signup-name"
              type="text"
              value={fullName}
              onChange={e => setFullName(e.target.value)}
              placeholder="Priya Sharma"
              disabled={loading}
              required
              autoComplete="name"
            />
          </div>
          <div className={styles.field}>
            <label htmlFor="signup-email">Email</label>
            <input
              id="signup-email"
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
            <label htmlFor="signup-password">Password</label>
            <input
              id="signup-password"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="At least 8 characters"
              disabled={loading}
              required
              autoComplete="new-password"
            />
          </div>
          <div className={styles.field}>
            <label htmlFor="signup-confirm">Confirm password</label>
            <input
              id="signup-confirm"
              type="password"
              value={confirm}
              onChange={e => setConfirm(e.target.value)}
              placeholder="Repeat your password"
              disabled={loading}
              required
              autoComplete="new-password"
            />
          </div>
          <button type="submit" disabled={loading || googleLoading} className={styles.button}>
            {loading ? 'Creating account…' : 'Create account'}
          </button>
          {error && <div className={styles.error}>{error}</div>}
        </form>

        <p className={styles.switchLink}>
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  );
};

export default SignupPage;
