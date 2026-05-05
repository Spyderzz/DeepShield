import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useEffect } from 'react';
import { Suspense, lazy } from 'react';
import { useAuth } from './contexts/AuthContext.jsx';
import { warmupBackend } from './services/api.js';

const HomePage = lazy(() => import('./pages/HomePage.jsx'));
const AnalyzePage = lazy(() => import('./pages/AnalyzePage.jsx'));
const ResultsPage = lazy(() => import('./pages/ResultsPage.jsx'));
const HistoryPage = lazy(() => import('./pages/HistoryPage.jsx'));
const LoginPage = lazy(() => import('./pages/LoginPage.jsx'));
const RegisterPage = lazy(() => import('./pages/RegisterPage.jsx'));
const OAuthCallbackPage = lazy(() => import('./pages/OAuthCallbackPage.jsx'));
const AboutPage = lazy(() => import('./pages/AboutPage.jsx'));
const ContactPage = lazy(() => import('./pages/ContactPage.jsx'));
const ModelsPage = lazy(() => import('./pages/ModelsPage.jsx'));
const NotFoundPage = lazy(() => import('./pages/NotFoundPage.jsx'));
const PrivacyPage  = lazy(() => import('./pages/PrivacyPage.jsx'));

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
      <a href="#main-content" className="skip-nav">Skip to main content</a>
      <ScrollToTop />
      <Suspense fallback={<div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><div style={{ color: 'var(--ds-muted)', fontSize: 14 }}>Loading...</div></div>}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/analyze"     element={<ProtectedRoute><AnalyzePage /></ProtectedRoute>} />
          <Route path="/results/:id" element={<ResultsPage />} />
          <Route path="/history"     element={<ProtectedRoute><HistoryPage /></ProtectedRoute>} />
          <Route path="/login"    element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/auth/callback" element={<OAuthCallbackPage />} />
          <Route path="/about"    element={<AboutPage />} />
          <Route path="/contact"  element={<ContactPage />} />
          <Route path="/models"   element={<ModelsPage />} />
          <Route path="/privacy"  element={<PrivacyPage />} />
          <Route path="*"         element={<NotFoundPage />} />
        </Routes>
      </Suspense>
    </>
  );
}
