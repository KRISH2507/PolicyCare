import React, { useState, useContext } from 'react';
import { useNavigate, Link, Navigate } from 'react-router-dom';
import { SessionContext } from '../context/SessionContext';
import { apiPost } from '../api/client';
import styles from '../styles/LoginPage.module.css';

const SignupPage = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const { setAuthToken, authToken, currentUser } = useContext(SessionContext);
  const navigate = useNavigate();

  // Already logged in — redirect away
  if (authToken) {
    return <Navigate to={currentUser?.role === 'admin' ? '/admin' : '/profile'} replace />;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (password !== confirm) {
      setError("Passwords don't match");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      // Backend auto-registers on first login
      const response = await apiPost('/api/auth/login', { username, password });
      setAuthToken(response.access_token, { username: response.username, role: response.role });
      navigate('/profile');
    } catch (err) {
      setError(err.message || 'Could not create account. Try a different username.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <div className={styles.header}>
          <h2>AarogyaAid</h2>
          <p>Create your account</p>
        </div>
        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.field}>
            <label>Username</label>
            <input
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              disabled={loading}
              required
              autoComplete="username"
            />
          </div>
          <div className={styles.field}>
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              disabled={loading}
              required
              autoComplete="new-password"
            />
          </div>
          <div className={styles.field}>
            <label>Confirm password</label>
            <input
              type="password"
              value={confirm}
              onChange={e => setConfirm(e.target.value)}
              disabled={loading}
              required
              autoComplete="new-password"
            />
          </div>
          <button type="submit" disabled={loading} className={styles.button}>
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
