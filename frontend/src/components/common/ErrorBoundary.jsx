import { Component } from 'react';

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    // eslint-disable-next-line no-console
    console.error('ErrorBoundary caught:', error, info);
  }

  handleReset = () => {
    this.setState({ error: null });
  };

  render() {
    if (this.state.error) {
      return (
        <div style={{
          maxWidth: 600,
          margin: 'var(--space-16) auto',
          padding: 'var(--space-8)',
          background: 'var(--color-surface)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-lg)',
          boxShadow: 'var(--shadow-md)',
          textAlign: 'center',
        }}>
          <div style={{ fontSize: '3rem', marginBottom: 'var(--space-3)' }}>⚠</div>
          <h2>Something went wrong</h2>
          <p style={{ color: 'var(--color-text-secondary)' }}>
            The app hit an unexpected error. You can try reloading the page or returning home.
          </p>
          <pre style={{
            background: '#FFEBEE',
            color: 'var(--color-danger)',
            padding: 'var(--space-3)',
            borderRadius: 'var(--radius-sm)',
            fontSize: 'var(--font-size-xs)',
            overflowX: 'auto',
            textAlign: 'left',
          }}>{String(this.state.error?.message || this.state.error)}</pre>
          <div style={{ display: 'flex', gap: 'var(--space-2)', justifyContent: 'center', marginTop: 'var(--space-4)' }}>
            <button
              onClick={() => window.location.reload()}
              style={{
                padding: 'var(--space-2) var(--space-4)',
                background: 'var(--color-primary-500)',
                color: 'white',
                border: 'none',
                borderRadius: 'var(--radius-md)',
                cursor: 'pointer',
                fontWeight: 'var(--font-weight-semibold)',
              }}
            >Reload</button>
            <button
              onClick={this.handleReset}
              style={{
                padding: 'var(--space-2) var(--space-4)',
                background: 'var(--color-surface)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-md)',
                cursor: 'pointer',
              }}
            >Dismiss</button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
