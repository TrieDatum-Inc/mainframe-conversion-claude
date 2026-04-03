/**
 * Add User page — COUSR01C (CU01) conversion.
 *
 * Blank form for creating a new user record.
 * BMS Map: COUSR1A heading "Add User"
 */
import { PageHeader } from '@/components/ui/PageHeader';
import { UserAddForm } from '@/components/forms/UserAddForm';

export const metadata = {
  title: 'Add User — CardDemo (COUSR01C)',
};

export default function AddUserPage() {
  return (
    <div className="rounded-lg shadow-sm overflow-hidden bg-white">
      <PageHeader title="Add User" subtitle="COUSR01C — CU01" />
      <div className="p-6">
        <UserAddForm />
      </div>
    </div>
  );
}
