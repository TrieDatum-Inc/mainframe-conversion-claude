"use client";

import { useParams } from "next/navigation";
import UserForm from "@/components/users/UserForm";

export default function EditUserPage() {
  const params = useParams();
  const userId = params.id as string;

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-900">Edit User: {userId}</h2>
      <UserForm userId={userId} />
    </div>
  );
}
