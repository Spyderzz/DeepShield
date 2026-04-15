import { createContext, useCallback, useContext, useState } from 'react';

const ToastContext = createContext(null);

const COLORS = {
  info:    { bg: '#E3F2FD', fg: '#0D47A1', border: '#90CAF9' },
  success: { bg: '#E8F5E9', fg: '#1B5E20', border: '#A5D6A7' },
  warning: { bg: '#FFF8E1', fg: '#6D4C00', border: '#FFE082' },
  error:   { bg: '#FFEBEE', fg: '#B71C1C', border: '#FFCDD2' },
};

let nextId = 1;

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const dismiss = useCallback((id) => {
    setToasts((xs) => xs.filter((t) => t.id !== id));
  }, []);

  const push = useCallback((msg, opts = {}) => {
    const id = nextId++;
    const toast = { id, message: msg, type: opts.type || 'info', duration: opts.duration ?? 4000 };
    setToasts((xs) => [...xs, toast]);
    if (toast.duration > 0) {
      setTimeout(() => dismiss(id), toast.duration);
    }
    return id;
  }, [dismiss]);

  const api = {
    push,
    dismiss,
    info:    (m, o) => push(m, { ...o, type: 'info' }),
    success: (m, o) => push(m, { ...o, type: 'success' }),
    warning: (m, o) => push(m, { ...o, type: 'warning' }),
    error:   (m, o) => push(m, { ...o, type: 'error' }),
  };

  return (
    <ToastContext.Provider value={api}>
      {children}
      <div style={{
        position: 'fixed',
        bottom: 'var(--space-4)',
        right: 'var(--space-4)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-2)',
        zIndex: 9999,
        maxWidth: 'calc(100vw - var(--space-8))',
      }}>
        {toasts.map((t) => {
          const c = COLORS[t.type] || COLORS.info;
          return (
            <div key={t.id} role="status" style={{
              background: c.bg,
              color: c.fg,
              border: `1px solid ${c.border}`,
              borderRadius: 'var(--radius-md)',
              padding: 'var(--space-3) var(--space-4)',
              boxShadow: 'var(--shadow-md)',
              minWidth: 240,
              maxWidth: 420,
              display: 'flex',
              gap: 'var(--space-3)',
              alignItems: 'flex-start',
              animation: 'toast-in 200ms ease-out',
            }}>
              <span style={{ flex: 1, fontSize: 'var(--font-size-sm)' }}>{t.message}</span>
              <button
                onClick={() => dismiss(t.id)}
                aria-label="Dismiss"
                style={{
                  background: 'transparent', border: 'none', color: c.fg,
                  cursor: 'pointer', fontSize: 'var(--font-size-lg)', lineHeight: 1, padding: 0,
                }}
              >×</button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within ToastProvider');
  return ctx;
}
