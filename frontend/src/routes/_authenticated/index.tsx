import { createFileRoute, redirect } from '@tanstack/react-router';

// `/` has no screen of its own: it sends each role to its landing page.
export const Route = createFileRoute('/_authenticated/')({
  beforeLoad: ({ context }) => {
    throw redirect({
      to: context.user.role === 'staff' ? '/account' : '/invoices',
      replace: true,
    });
  },
});
