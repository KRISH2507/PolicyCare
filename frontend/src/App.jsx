import React, { useContext } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { SessionContext } from './context/SessionContext';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import ProfilePage from './pages/ProfilePage';
import ResultsPage from './pages/ResultsPage';
import AdminPage from './pages/AdminPage';

const ProtectedRoute = ({ children, requireAdmin, requireResult }) => {
  const { authToken, currentUser, recommendationResult } = useContext(SessionContext);
  const location = useLocation();

  if (!authToken) return <Navigate to="/login" state={{ from: location }} replace />;
  if (requireAdmin && currentUser?.role !== 'admin') return <Navigate to="/profile" replace />;
  if (requireResult && !recommendationResult) return <Navigate to="/profile" replace />;

  return children;
};

const App = () => {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/profile" element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />
      <Route path="/results" element={<ProtectedRoute requireResult><ResultsPage /></ProtectedRoute>} />
      <Route path="/admin" element={<ProtectedRoute requireAdmin><AdminPage /></ProtectedRoute>} />
    </Routes>
  );
};

export default App;