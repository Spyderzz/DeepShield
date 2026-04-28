import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useEffect } from 'react';
import HomePage from './pages/HomePage.jsx';
import AnalyzePage from './pages/AnalyzePage.jsx';
import ResultsPage from './pages/ResultsPage.jsx';
import HistoryPage from './pages/HistoryPage.jsx';
import LoginPage from './pages/LoginPage.jsx';
import RegisterPage from './pages/RegisterPage.jsx';
import AboutPage from './pages/AboutPage.jsx';
import ContactPage from './pages/ContactPage.jsx';
import ModelsPage from './pages/ModelsPage.jsx';
import NotFoundPage from './pages/NotFoundPage.jsx';
import { useAuth } from './contexts/AuthContext.jsx';
import { warmupBackend } from './services/api.js';

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
}

/** Redirects unauthenticated users to /login, preserving the intended path. */
function ProtectedRoute({ children }) {
  const { isAuthed } = useAuth();
  const location = useLocation();
  if (!isAuthed) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }
  return children;
}

export default function App() {
  const { authReady } = useAuth();

  useEffect(() => {
    // Fire-and-forget warm-up to reduce first-request latency after HF sleep.
    void warmupBackend();
  }, []);

  if (!authReady) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh' }}>
        <div style={{ color: 'var(--ds-muted, #7A8299)', fontSize: 14 }}>Loading…</div>
      </div>
    );
  }

  return (
    <>
      <ScrollToTop />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/analyze"     element={<ProtectedRoute><AnalyzePage /></ProtectedRoute>} />
        <Route path="/results/:id" element={<ResultsPage />} />
        <Route path="/history"     element={<ProtectedRoute><HistoryPage /></ProtectedRoute>} />
        <Route path="/login"    element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/about"    element={<AboutPage />} />
        <Route path="/contact"  element={<ContactPage />} />
        <Route path="/models"   element={<ModelsPage />} />
        <Route path="*"         element={<NotFoundPage />} />
      </Routes>
    </>
  );
}
