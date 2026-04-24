import React, { useContext, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { SessionContext } from '../context/SessionContext';
import UploadCard from '../components/UploadCard';
import PolicyTable from '../components/PolicyTable';
import '../styles/admin.css';

const AdminPage = () => {
  const { currentUser, setAuthToken } = useContext(SessionContext);
  const navigate = useNavigate();

  /**
   * refreshTrigger is incremented each time a new policy is uploaded.
   * PolicyTable watches it via useEffect to re-fetch the list automatically.
   */
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleUploadSuccess = () => {
    setRefreshTrigger((n) => n + 1);
  };

  const handleLogout = () => {
    setAuthToken(null, null);   // clears token + all localStorage session data
    navigate('/login', { replace: true });
  };

  return (
    <div className="admin-page">
      {/* ── Sticky header ── */}
      <header className="admin-header">
        <div className="admin-header-brand">
          <p className="admin-header-title">AarogyaAid Admin</p>
          <p className="admin-header-sub">Policy Knowledge Base</p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {currentUser?.email && (
            <span style={{ fontSize: '13px', color: '#8A8A8A' }}>
              {currentUser.full_name || currentUser.email}
            </span>
          )}
          <button
            className="admin-logout-btn"
            onClick={handleLogout}
            aria-label="Log out of admin panel"
          >
            Log out
          </button>
        </div>
      </header>

      {/* ── Body ── */}
      <div className="admin-body">
        {/* Left: Upload */}
        <aside aria-label="Upload new policy">
          <UploadCard onUploadSuccess={handleUploadSuccess} />
        </aside>

        {/* Right: Policy table */}
        <main aria-label="Policy documents list">
          <PolicyTable refreshTrigger={refreshTrigger} />
        </main>
      </div>
    </div>
  );
};

export default AdminPage;
