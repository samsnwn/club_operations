import { createFileRoute } from '@tanstack/react-router';

import { InvoicesScreen } from '../../../screens';

export const Route = createFileRoute('/_authenticated/_manager/invoices')({
  staticData: {
    title: 'Invoice review',
    description:
      'Import captured invoices, check the suggestions, and confirm what is ready for export.',
  },
  component: InvoicesScreen,
});
