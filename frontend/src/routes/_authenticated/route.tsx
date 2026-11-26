import { createFileRoute, redirect } from '@tanstack/react-router';

import { AppShell } from '../../AppShell';

// Pathless layout for every signed-in screen.
export const Route = createFileRoute('/_authenticated')({
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
