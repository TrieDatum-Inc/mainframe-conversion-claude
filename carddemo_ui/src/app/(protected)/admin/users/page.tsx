"use client";

import Link from "next/link";
import UserTable from "@/components/users/UserTable";

export default function UsersPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900">User Management</h2>
        <Link
          href="/admin/users/new"
          className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-brand-700"
        >
          Add User
        </Link>
      </div>
      <UserTable />
    </div>
  );
}
