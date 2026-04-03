/**
 * Update User page — COUSR02C (CU02) conversion.
 *
 * Pre-populates from the user_id URL param (CDEMO-CU02-USR-SELECTED in COBOL).
 * BMS Map: COUSR2A heading "Update User"
 */
import { PageHeader } from '@/components/ui/PageHeader';
import { UserUpdateForm } from '@/components/forms/UserUpdateForm';

export const metadata = {
  title: 'Update User — CardDemo (COUSR02C)',
};

interface UpdateUserPageProps {
  params: { userId: string };
}

export default function UpdateUserPage({ params }: UpdateUserPageProps) {
  return (
    <div className="rounded-lg shadow-sm overflow-hidden bg-white">
      <PageHeader title="Update User" subtitle="COUSR02C — CU02" />
      <div className="p-6">
        <UserUpdateForm userId={params.userId} />
      </div>
    </div>
  );
}
