'use client';

/**
 * UserTable — data table for the user list page.
 *
 * COBOL origin: COUSR00C COUSR0AO output map — 10 rows per page:
 *   Columns: User ID (USRID), First Name (FNAME), Last Name (LNAME), Type (UTYPE)
 *   Row actions: Update (replaces 'U' selector) and Delete (replaces 'D' selector)
 *
 * BMS selection flags SEL0001I–SEL0010I ('U'/'D') → Update/Delete buttons per row.
 * UTYPE1O–UTYPE10O shows 'Admin' or 'User' label (COBOL showed 'A' or 'R').
 */

import React from 'react';
import Link from 'next/link';
import type { UserResponse } from '@/types';

interface UserTableProps {
  users: UserResponse[];
  onDeleteClick?: (user: UserResponse) => void;
}

export function UserTable({ users, onDeleteClick }: UserTableProps) {
  if (users.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No users found. Use the filter above or add a new user.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200 border border-gray-200 rounded-lg">
        <thead className="bg-gray-50">
          <tr>
            {/* USRID1O–USRID10O column */}
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
              User ID
            </th>
            {/* FNAME1O–FNAME10O column */}
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
              First Name
            </th>
            {/* LNAME1O–LNAME10O column */}
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
              Last Name
            </th>
            {/* UTYPE1O–UTYPE10O column */}
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
              User Type
            </th>
            {/* SEL0001I–SEL0010I: U=Update, D=Delete → action buttons */}
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-100">
          {users.map((user) => (
            <tr key={user.user_id} className="hover:bg-gray-50 transition-colors">
              <td className="px-4 py-3 text-sm font-mono font-medium text-gray-900">
                {user.user_id}
              </td>
              <td className="px-4 py-3 text-sm text-gray-700">{user.first_name}</td>
              <td className="px-4 py-3 text-sm text-gray-700">{user.last_name}</td>
              <td className="px-4 py-3 text-sm">
                <span
                  className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                    user.user_type === 'A'
                      ? 'bg-purple-100 text-purple-700'
                      : 'bg-blue-100 text-blue-700'
                  }`}
                >
                  {user.user_type === 'A' ? 'Admin' : 'User'}
                </span>
              </td>
              <td className="px-4 py-3 text-sm">
                <div className="flex gap-2">
                  {/* 'U' selector → Update button → COUSR02C */}
                  <Link
                    href={`/admin/users/${user.user_id}/edit`}
                    className="inline-flex items-center px-3 py-1 text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 rounded transition-colors"
                  >
                    Update
                  </Link>
                  {/* 'D' selector → Delete button → COUSR03C */}
                  <Link
                    href={`/admin/users/${user.user_id}/delete`}
                    className="inline-flex items-center px-3 py-1 text-xs font-medium text-white bg-red-600 hover:bg-red-700 rounded transition-colors"
                  >
                    Delete
                  </Link>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
