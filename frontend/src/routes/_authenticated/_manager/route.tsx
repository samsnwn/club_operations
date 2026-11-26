import { createFileRoute, redirect } from '@tanstack/react-router';

// Owner/admin only: staff never render these screens, even by typed URL.
export const Route = createFileRoute('/_authenticated/_manager')({
  beforeLoad: ({ context }) => {
    if (context.user.role !== 'owner' && context.user.role !== 'admin') {
      throw redirect({ to: '/account', replace: true });
    }
  },
});
