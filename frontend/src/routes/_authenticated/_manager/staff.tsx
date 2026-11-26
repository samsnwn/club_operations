import { createFileRoute } from '@tanstack/react-router';

import { StaffScreen } from '../../../screens';

export const Route = createFileRoute('/_authenticated/_manager/staff')({
  staticData: {
    title: 'Internal accounts',
    description: 'Create staff accounts and manage access.',
  },
  component: StaffScreen,
});
