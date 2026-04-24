import React, { useState, useContext } from 'react';
import { useNavigate, Link, Navigate } from 'react-router-dom';
import { SessionContext } from '../context/SessionContext';
import { apiPost } from '../api/client';
import styles from '../styles/LoginPage.module.css';

const LoginPage = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
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
    setLoading(true);
    setError(null);
    try {
      const response = await apiPost('/api/auth/login', { username, password });
      setAuthToken(response.access_token, { username: response.username, role: response.role });
      
      if (response.role === 'admin') navigate('/admin');
      else navigate('/profile');
    } catch (err) {
      setError("Incorrect username or password");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <div className={styles.header}>
          <h2>AarogyaAid</h2>
          <p>Sign in to continue</p>
        </div>
        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.field}>
            <label>Username</label>
            <input 
              type="text" 
              value={username} onChange={e => setUsername(e.target.value)} 
              disabled={loading} required 
            />
          </div>
          <div className={styles.field}>
            <label>Password</label>
            <input 
              type="password" 
              value={password} onChange={e => setPassword(e.target.value)} 
              disabled={loading} required 
            />
          </div>
          <button type="submit" disabled={loading} className={styles.button}>
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