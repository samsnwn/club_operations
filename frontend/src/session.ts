// Session state shared from App with the routed screens. The guards in
// router.tsx read the user from router context; screens read it from here.

import { createContext, useContext } from 'react';

import type { CurrentUser } from './auth';

export type Session = {
  user: CurrentUser | null;
  /** Session-check problem shown on the login page. */
  notice: string;
  setUser: (user: CurrentUser | null) => void;
  /** Re-reads the session; clears the user when it is gone. */
  onAuthProblem: () => void;
  signOut: () => void;
};

export const SessionContext = createContext<Session | null>(null);

export function useSession(): Session {
  const session = useContext(SessionContext);
  if (!session) throw new Error('useSession must be used inside App');
  return session;
}
