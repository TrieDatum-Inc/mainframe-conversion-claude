/**
 * Delete User confirmation page — COUSR03C (CU03) conversion.
 *
 * Pre-populates from the user_id URL param (CDEMO-CU03-USR-SELECTED in COBOL).
 * Shows user info in read-only fields for confirmation before deletion.
 * BMS Map: COUSR3A heading "Delete User"
 *
 * Key difference from Update page:
 *   - FNAME/LNAME/USRTYPE are ASKIP (read-only) in COUSR03 BMS map
 *   - PF3 cancels without deleting (unlike COUSR02C where PF3 saves)
 *   - No password field on this screen
 */
import { PageHeader } from '@/components/ui/PageHeader';
import { UserDeleteConfirm } from '@/components/forms/UserDeleteConfirm';

export const metadata = {
  title: 'Delete User — CardDemo (COUSR03C)',
};

interface DeleteUserPageProps {
  params: { userId: string };
}

export default function DeleteUserPage({ params }: DeleteUserPageProps) {
  return (
    <div className="rounded-lg shadow-sm overflow-hidden bg-white">
      <PageHeader title="Delete User" subtitle="COUSR03C — CU03" />
      <div className="p-6">
        <UserDeleteConfirm userId={params.userId} />
      </div>
    </div>
  );
}
