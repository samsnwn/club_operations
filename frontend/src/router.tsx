// The route tree. Every route and every access guard is defined here, in code
// (no file-based routing, no generated tree). Guards read the signed-in user
// from router context, which App fills once the session check is done.

import {
  createRootRouteWithContext,
  createRoute,
  createRouter,
  Outlet,
  redirect,
} from '@tanstack/react-router';

import { AppShell } from './AppShell';
import type { CurrentUser } from './auth';
import { safeRedirect } from './redirect';
import {
  AccountScreen,
  InvoicesScreen,
  LoginScreen,
  NotFoundScreen,
  PasswordScreen,
  StaffScreen,
} from './screens';

export type RouterContext = { user: CurrentUser | null };

const rootRoute = createRootRouteWithContext<RouterContext>()({
  component: Outlet,
  notFoundComponent: NotFoundScreen,
});

const loginRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: 'login',
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

// Pathless layout for every signed-in screen.
const authenticatedRoute = createRoute({
  getParentRoute: () => rootRoute,
  id: 'authenticated',
  beforeLoad: ({ context, location }) => {
    if (!context.user) {
      throw redirect({
        to: '/login',
        search: { redirect: location.pathname + location.searchStr },
        replace: true,
      });
    }
    return { user: context.user };
  },
  component: AppShell,
});

const indexRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: '/',
  beforeLoad: ({ context }) => {
    throw redirect({
      to: context.user.role === 'staff' ? '/account' : '/invoices',
      replace: true,
    });
  },
});

// Owner/admin only: staff never render these screens, even by typed URL.
const managerRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  id: 'manager',
  beforeLoad: ({ context }) => {
    if (context.user.role !== 'owner' && context.user.role !== 'admin') {
      throw redirect({ to: '/account', replace: true });
    }
  },
});

const invoicesRoute = createRoute({
  getParentRoute: () => managerRoute,
  path: 'invoices',
  staticData: {
    title: 'Invoice review',
    description:
      'Import captured invoices, check the suggestions, and confirm what is ready for export.',
  },
  component: InvoicesScreen,
});

const staffRoute = createRoute({
  getParentRoute: () => managerRoute,
  path: 'staff',
  staticData: {
    title: 'Internal accounts',
    description: 'Create staff accounts and manage access.',
  },
  component: StaffScreen,
});

const accountRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: 'account',
  staticData: {
    title: 'Your account',
    description:
      'Your account is active. Invoice review is limited to owners and administrators; you can change your password or sign out.',
  },
  component: AccountScreen,
});

const passwordRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: 'account/password',
  staticData: {
    title: 'Change password',
    description: 'Update the password for your own account.',
  },
  component: PasswordScreen,
});

const routeTree = rootRoute.addChildren([
  loginRoute,
  authenticatedRoute.addChildren([
    indexRoute,
    managerRoute.addChildren([invoicesRoute, staffRoute]),
    accountRoute,
    passwordRoute,
  ]),
]);

export const router = createRouter({
  routeTree,
  context: { user: null },
  // Unknown paths show the not-found page outside the shell, for anyone.
  notFoundMode: 'root',
});

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
  interface StaticDataRouteOption {
    title?: string;
    description?: string;
  }
}
