import { createFileRoute } from '@tanstack/react-router';

import { AccountScreen } from '../../../screens';

export const Route = createFileRoute('/_authenticated/account/')({
  staticData: {
    title: 'Your account',
    description:
      'Your account is active. Invoice review is limited to owners and administrators; you can change your password or sign out.',
  },
  component: AccountScreen,
});
