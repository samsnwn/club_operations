import { createRootRouteWithContext, Outlet } from '@tanstack/react-router';

import type { RouterContext } from '../router';
import { NotFoundScreen } from '../screens';

export const Route = createRootRouteWithContext<RouterContext>()({
  component: Outlet,
  notFoundComponent: NotFoundScreen,
});
