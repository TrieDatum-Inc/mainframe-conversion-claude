"use client";

import UserForm from "@/components/users/UserForm";

export default function NewUserPage() {
  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-900">Add User</h2>
      <UserForm />
    </div>
  );
}
