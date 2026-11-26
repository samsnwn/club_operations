// The router. Routes live one per file under src/routes/; the TanStack Router
// Vite plugin generates src/routeTree.gen.ts from them (committed, never
// edited by hand). Guards read the signed-in user from router context, which
// App fills once the session check is done.

import { createRouter } from '@tanstack/react-router';

import type { CurrentUser } from './auth';
import { routeTree } from './routeTree.gen';

export type RouterContext = { user: CurrentUser | null };

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
