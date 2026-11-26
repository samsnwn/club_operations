import { Crest, Sign, Wordmark } from './Brand';

/** Persistent notice for the signed-in shell while the server is unreachable. */
export function OfflineBar() {
  return (
    <p className="alert alert-warning offline-bar" role="status">
      Offline – changes can't be saved until the connection is back.
    </p>
  );
}

/** Start screen when the session check can't reach the server. */
export function OfflineScreen({ onRetry }: { onRetry: () => void }) {
  return (
    <section className="auth-stack" aria-label="Offline">
      <Sign className="auth-sign">
        <Crest />
        <Wordmark className="auth-wordmark" />
        <span className="auth-tagline">Club operations</span>
      </Sign>
      <div className="card auth-card">
        <h1>You're offline</h1>
        <p className="auth-hint">
          Blue Velvet needs a connection to the club server. Check your
          connection and try again.
        </p>
        <button type="button" className="btn btn-primary" onClick={onRetry}>
          Retry
        </button>
      </div>
    </section>
  );
}
