import { createFileRoute } from '@tanstack/react-router';

import { PasswordScreen } from '../../../screens';

export const Route = createFileRoute('/_authenticated/account/password')({
  staticData: {
    title: 'Change password',
    description: 'Update the password for your own account.',
  },
  component: PasswordScreen,
});
