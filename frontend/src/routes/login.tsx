import { createFileRoute, redirect } from '@tanstack/react-router';

import { safeRedirect } from '../redirect';
import { LoginScreen } from '../screens';

export const Route = createFileRoute('/login')({
  validateSearch: (search: Record<string, unknown>): { redirect?: string } =>
    typeof search.redirect === 'string' ? { redirect: search.redirect } : {},
  beforeLoad: ({ context, search }) => {
    // Signed in (including right after sign-in): continue to the requested
    // page, but only when it is a same-origin path.
    if (context.user) {
      throw redirect({ href: safeRedirect(search.redirect), replace: true });
    }
  },
  component: LoginScreen,
});
