import React, { useContext } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { SessionContext } from '../context/SessionContext';
import styles from '../styles/LandingPage.module.css';

const features = [
  {
    title: 'Find the right plan',
    desc: 'Answer a few questions about your health and budget. We match you with schemes that actually fit.',
  },
  {
    title: 'Government & private schemes',
    desc: 'Coverage across Ayushman Bharat, state schemes, and private insurers — all in one place.',
  },
  {
    title: 'Ask questions, get answers',
    desc: 'Not sure what a policy covers? Chat with our assistant to clear up the fine print.',
  },
];

const LandingPage = () => {
  const { authToken, currentUser } = useContext(SessionContext);

  // Redirect already-authenticated users to their home screen
  if (authToken) {
    return <Navigate to={currentUser?.role === 'admin' ? '/admin' : '/profile'} replace />;
  }
  return (
    <div className={styles.page}>
      <header className={styles.nav}>
        <span className={styles.logo}>AarogyaAid</span>
        <div className={styles.navLinks}>
          <Link to="/login" className={styles.navLink}>Sign in</Link>
          <Link to="/signup" className={styles.navCta}>Get started</Link>
        </div>
      </header>

      <main>
        <section className={styles.hero}>
          <h1 className={styles.heroTitle}>Health insurance,<br />made simple.</h1>
          <p className={styles.heroSub}>
            AarogyaAid helps you find and understand health insurance schemes
            that match your needs — without the jargon.
          </p>
          <div className={styles.heroActions}>
            <Link to="/signup" className={styles.primaryBtn}>Get started — it's free</Link>
            <Link to="/login" className={styles.ghostBtn}>Sign in</Link>
          </div>
        </section>

        <section className={styles.features}>
          {features.map((f) => (
            <div key={f.title} className={styles.featureCard}>
              <h3 className={styles.featureTitle}>{f.title}</h3>
              <p className={styles.featureDesc}>{f.desc}</p>
            </div>
          ))}
        </section>
      </main>

      <footer className={styles.footer}>
        <p>© {new Date().getFullYear()} AarogyaAid</p>
      </footer>
    </div>
  );
};

export default LandingPage;
