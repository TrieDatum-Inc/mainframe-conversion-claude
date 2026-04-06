'use client';

/**
 * Delete User confirmation page — /admin/users/[userId]/delete
 *
 * COBOL origin: COUSR03C (Transaction CU03), BMS map COUSR3A
 *
 * Replaces:
 *   - READ-USER-SEC-FILE on first entry → display FNAME, LNAME, UTYPE (read-only)
 *   - Password NOT shown (COUSR3A intentionally has no PASSWDI field)
 *   - PF5 → DELETE-USER-INFO → DELETE-USER-SEC-FILE (confirm delete)
 *   - PF3 → Back to User List without delete (CDEMO-FROM-PROGRAM)
 *   - PF12 → Admin Menu without delete (COADM01C)
 *   - Success: fields cleared to allow deleting another user
 *
 * Bug fix: COUSR03C DELETE-USER-SEC-FILE OTHER branch said 'Unable to Update User...'
 * This page shows correct 'Unable to delete user' messaging via API 500 errors.
 *
 * Admin only.
 */

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { getUser, deleteUser, extractError } from '@/lib/api';
import { MessageBar } from '@/components/ui/MessageBar';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import type { UserResponse } from '@/types';

export default function DeleteUserPage() {
  const params = useParams();
  const userId = params.userId as string;
  const router = useRouter();

  const [user, setUser] = useState<UserResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);
  const [loadError, setLoadError] = useState('');
  const [deleteError, setDeleteError] = useState('');
  const [deleted, setDeleted] = useState(false);

  /**
   * On mount: load user for confirmation display.
   * COUSR03C PROCESS-ENTER-KEY → READ-USER-SEC-FILE:
   *   Display FNAME, LNAME, UTYPE for confirmation.
   *   Password NOT displayed (COUSR3A map has no PASSWDI field).
   */
  useEffect(() => {
    const loadUser = async () => {
      setLoading(true);
      try {
        const data = await getUser(userId);
        setUser(data);
      } catch (err) {
        const apiError = extractError(err);
        setLoadError(apiError.message);
      } finally {
        setLoading(false);
      }
    };
    loadUser();
  }, [userId]);

  /**
   * PF5 → Confirm delete.
   * COUSR03C DELETE-USER-INFO → DELETE-USER-SEC-FILE.
   * Two-step: read (already done on mount) then delete.
   *
   * Bug fix: COUSR03C DELETE-USER-SEC-FILE OTHER showed 'Unable to Update User...'
   * This implementation returns the correct error message from the API.
   */
  const handleConfirmDelete = async () => {
    setDeleting(true);
    setDeleteError('');
    try {
      await deleteUser(userId);
      setDeleted(true);
      // COUSR03C: after success redirect back to list
      setTimeout(() => router.push('/admin/users'), 1500);
    } catch (err) {
      const apiError = extractError(err);
      setDeleteError(apiError.message);
    } finally {
      setDeleting(false);
    }
  };

  if (loading) return <LoadingSpinner label="Loading user details..." />;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-red-900 text-white py-3 px-6">
        <div className="flex justify-between items-center">
          <div>
            <p className="text-xs text-red-300">COUSR03C | CU03</p>
            <h1 className="text-lg font-bold">Delete User — Confirmation Required</h1>
          </div>
          <div className="text-xs text-red-300">
            <p>Admin Only</p>
          </div>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-6 space-y-4">
        {loadError && <MessageBar message={loadError} variant="error" />}
        {deleteError && <MessageBar message={deleteError} variant="error" />}

        {deleted ? (
          <MessageBar
            message={`User ${userId} has been deleted successfully. Redirecting...`}
            variant="success"
          />
        ) : (
          <>
            {/* DFHNEUTR prompt — 'Press PF5 key to delete...' equivalent */}
            {!loadError && (
              <MessageBar
                message="Review the user details below and click Confirm Delete to proceed."
                variant="info"
              />
            )}

            {user && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h2 className="text-base font-semibold text-gray-900 mb-4">
                  User to be Deleted
                </h2>

                {/*
                 * Read-only display — COUSR3A map fields (all ASKIP/output-only):
                 * FNAMEI, LNAMEI, USRTYPEI displayed; PASSWDI NOT shown (not in COUSR3A).
                 */}
                <dl className="space-y-3">
                  <div className="flex">
                    <dt className="w-32 text-sm font-medium text-gray-500">User ID</dt>
                    <dd className="text-sm font-mono font-bold text-gray-900">{user.user_id}</dd>
                  </div>
                  <div className="flex">
                    <dt className="w-32 text-sm font-medium text-gray-500">First Name</dt>
                    <dd className="text-sm text-gray-900">{user.first_name}</dd>
                  </div>
                  <div className="flex">
                    <dt className="w-32 text-sm font-medium text-gray-500">Last Name</dt>
                    <dd className="text-sm text-gray-900">{user.last_name}</dd>
                  </div>
                  <div className="flex">
                    <dt className="w-32 text-sm font-medium text-gray-500">User Type</dt>
                    <dd className="text-sm">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                          user.user_type === 'A'
                            ? 'bg-purple-100 text-purple-700'
                            : 'bg-blue-100 text-blue-700'
                        }`}
                      >
                        {user.user_type === 'A' ? 'Administrator' : 'Regular User'}
                      </span>
                    </dd>
                  </div>
                </dl>

                <div className="mt-6 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                  <strong>Warning:</strong> This action cannot be undone. The user will be
                  permanently removed from the system.
                </div>

                {/* Action buttons */}
                <div className="flex gap-3 mt-6">
                  {/* PF5 — Confirm delete */}
                  <button
                    type="button"
                    onClick={handleConfirmDelete}
                    disabled={deleting}
                    className="px-6 py-2 bg-red-600 text-white text-sm font-medium rounded hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {deleting ? 'Deleting...' : 'Confirm Delete (PF5)'}
                  </button>

                  {/* PF3 — Back to User List without delete */}
                  <Link
                    href="/admin/users"
                    className="px-4 py-2 bg-gray-100 text-gray-700 text-sm font-medium rounded hover:bg-gray-200 transition-colors"
                  >
                    Cancel — Back to Users (PF3)
                  </Link>

                  {/* PF12 — Admin Menu without delete */}
                  <Link
                    href="/admin/menu"
                    className="px-4 py-2 text-gray-500 text-sm font-medium rounded hover:bg-gray-100 transition-colors"
                  >
                    Admin Menu (PF12)
                  </Link>
                </div>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
