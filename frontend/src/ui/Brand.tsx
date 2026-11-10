import type { ReactNode } from 'react';

/** Round emblem from the left of the sign. Decorative; pair with a wordmark. */
export function Crest({ className = '' }: { className?: string }) {
  return (
    <span className={`bv-crest ${className}`} aria-hidden="true">
      BV
    </span>
  );
}

/** "Blue Velvet" in the sign's script face. The only place Lobster is used. */
export function Wordmark({ className = '' }: { className?: string }) {
  return <span className={`bv-wordmark ${className}`}>Blue Velvet</span>;
}

/**
 * The sign: velvet panel, cream frame, gold stripe. Use for brand moments
 * (app header, sign-in). Children render inside the panel.
 */
export function Sign({
  children,
  className = '',
}: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={`bv-sign ${className}`}>{children}</div>;
}
