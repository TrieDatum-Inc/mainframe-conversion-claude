/**
 * UserDeleteConfirm — COUSR03C (CU03) Delete User screen conversion.
 *
 * BMS Map: COUSR3A (COUSR03 mapset), 24x80
 *
 * Two-phase interaction (mirroring COUSR03C):
 *   Phase 1 (ENTER key):
 *     - Fetch user data for confirmation display
 *     - Show FNAME, LNAME, USRTYPE as ASKIP (read-only) fields
 *     - No password field (COUSR03 BMS map has no PASSWD field)
 *   Phase 2 (PF5 key):
 *     - Confirm deletion
 *     - DELETE-USER-SEC-FILE
 *
 * Critical design distinction from COUSR02C:
 *   FNAME/LNAME/USRTYPE are ASKIP (read-only) — shown for review only.
 *   PF3 = Back/Cancel (no delete — unlike COUSR02C where PF3 saves)
 *   PF5 = Confirm Delete
 *
 * COBOL bug fixed:
 *   Error message on delete failure says "Unable to Delete User"
 *   (original COUSR03C said "Unable to Update User" — copy-paste bug)
 */
'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

import { Button } from '@/components/ui/Button';
import { FormField } from '@/components/ui/FormField';
import { StatusMessage } from '@/components/ui/StatusMessage';
import { ApiError, deleteUser, getUser } from '@/lib/api';
import { formatUserType, getErrorMessage } from '@/lib/utils';
import type { UserResponse } from '@/types/user';

interface UserDeleteConfirmProps {
  /** user_id pre-selected from list (CDEMO-CU03-USR-SELECTED in COBOL) */
  userId: string;
}

type MessageState = {
  text: string;
  type: 'success' | 'error' | 'info';
} | null;

export function UserDeleteConfirm({ userId }: UserDeleteConfirmProps) {
  const router = useRouter();
  const [user, setUser] = useState<UserResponse | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<MessageState>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleted, setDeleted] = useState(false);

  // On mount, auto-fetch user data for confirmation display (COUSR03C PROCESS-ENTER-KEY)
  useEffect(() => {
    const fetchUser = async () => {
      try {
        const data = await getUser(userId);
        setUser(data);
        // 'Press PF5 key to delete this user ...' (COUSR03C READ-USER-SEC-FILE success)
        setStatusMessage({
          text: 'Review the user details below. Press Delete (F5) to confirm deletion.',
          type: 'info',
        });
      } catch (err) {
        if (err instanceof ApiError) {
          setLoadError(err.message);
        } else {
          setLoadError(getErrorMessage(err));
        }
      }
    };
    fetchUser();
  }, [userId]);

  // PF5 = Delete confirmation
  const handleDelete = async () => {
    setIsDeleting(true);
    setStatusMessage(null);
    try {
      await deleteUser(userId);
      // COUSR03C DELETE-USER-SEC-FILE success: clear screen, show green message
      // 'User [ID] has been deleted ...'
      setDeleted(true);
      setStatusMessage({
        text: `User ${userId} has been deleted ...`,
        type: 'success',
      });
      // After success, screen is cleared (INITIALIZE-ALL-FIELDS in COBOL)
      // Redirect back to list after a brief pause
      setTimeout(() => router.push('/users'), 2000);
    } catch (err) {
      // COBOL bug fixed: "Unable to Delete User" (not "Unable to Update User")
      if (err instanceof ApiError) {
        setStatusMessage({ text: err.message, type: 'error' });
      } else {
        setStatusMessage({ text: getErrorMessage(err), type: 'error' });
      }
    } finally {
      setIsDeleting(false);
    }
  };

  // PF3 = Back (no delete — different from COUSR02C where PF3 saves)
  const handleBack = () => {
    router.push('/users');
  };

  // PF4 = Clear
  const handleClear = () => {
    setStatusMessage(null);
  };

  if (loadError) {
    return (
      <div className="space-y-4">
        <StatusMessage message={loadError} type="error" />
        <Button variant="secondary" onClick={handleBack}>
          Back (F3)
        </Button>
      </div>
    );
  }

  if (!user) {
    return <p className="text-gray-500 text-sm">Loading user data...</p>;
  }

  return (
    <div className="space-y-6">
      {/* User ID — search key field (USRIDIN on BMS map) */}
      <div className="bg-gray-50 border border-gray-200 rounded-md px-4 py-3">
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-green-700">Enter User ID:</span>
          <span className="text-sm font-mono font-bold text-green-700">{userId}</span>
        </div>
      </div>

      {/* Separator — Row 8 asterisk line */}
      <div className="border-t-2 border-yellow-400" />

      {/* Status message — ERRMSG field */}
      {statusMessage && (
        <StatusMessage message={statusMessage.text} type={statusMessage.type} />
      )}

      {!deleted && (
        <>
          {/* Read-only confirmation fields (ASKIP in BMS — not editable) */}
          {/* Row 11: First Name — ASKIP,FSET,NORM BLUE */}
          <div className="space-y-4">
            <FormField
              label="First Name"
              value={user.first_name}
              readOnly
              aria-label="First Name (read-only for confirmation)"
            />

            {/* Row 13: Last Name — ASKIP,FSET,NORM BLUE (stacked, not beside First Name) */}
            <FormField
              label="Last Name"
              value={user.last_name}
              readOnly
              aria-label="Last Name (read-only for confirmation)"
            />

            {/* Row 15: User Type — ASKIP,FSET,NORM BLUE */}
            <div>
              <label className="block text-sm font-medium text-gray-500 mb-1">
                User Type
                <span className="ml-2 text-xs font-normal text-blue-600">(A=Admin, U=User)</span>
              </label>
              <div className="rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-700 cursor-default">
                {user.user_type} — {formatUserType(user.user_type)}
              </div>
            </div>
          </div>

          {/* Warning banner — visual cue that this is a destructive action */}
          <div className="bg-red-50 border border-red-300 rounded-md px-4 py-3">
            <p className="text-sm text-red-800 font-medium">
              Warning: This action is permanent and cannot be undone.
            </p>
            <p className="text-sm text-red-700 mt-1">
              User <strong>{userId}</strong> ({user.first_name} {user.last_name}) will be permanently deleted.
            </p>
          </div>

          {/* Row 24: ENTER=Fetch F3=Back F4=Clear F5=Delete */}
          <div className="flex flex-wrap gap-3 pt-4 border-t border-gray-200">
            {/* F5=Delete (confirm) */}
            <Button variant="danger" onClick={handleDelete} isLoading={isDeleting}>
              Delete (F5)
            </Button>
            {/* F3=Back (cancel — no delete, different from COUSR02C PF3) */}
            <Button variant="secondary" onClick={handleBack}>
              Back / Cancel (F3)
            </Button>
            {/* F4=Clear */}
            <Button variant="ghost" onClick={handleClear}>
              Clear (F4)
            </Button>
          </div>
        </>
      )}
    </div>
  );
}
