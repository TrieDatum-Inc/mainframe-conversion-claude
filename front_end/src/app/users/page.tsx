/**
 * User List page — COUSR00C (CU00) conversion.
 *
 * Displays paginated list of users with search and row selection.
 * BMS Map: COUSR0A heading "List Users"
 */
import { Suspense } from 'react';

import { PageHeader } from '@/components/ui/PageHeader';
import { UserListTable } from '@/components/forms/UserListTable';

export const metadata = {
  title: 'List Users — CardDemo (COUSR00C)',
};

export default function UsersPage() {
  return (
    <div className="rounded-lg shadow-sm overflow-hidden bg-white">
      <PageHeader title="List Users" subtitle="COUSR00C — CU00" />
      <div className="p-6">
        <Suspense fallback={<p className="text-gray-500 text-sm">Loading users...</p>}>
          <UserListTable />
        </Suspense>
      </div>
    </div>
  );
}
