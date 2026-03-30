"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { UserRead, UserCreate, UserUpdate, MessageResponse } from "@/lib/types";
import { ApiError } from "@/lib/api";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import AlertMessage from "@/components/ui/AlertMessage";
import FormField from "@/components/ui/FormField";

interface UserFormProps {
  userId?: string; // undefined = create mode
}

export default function UserForm({ userId }: UserFormProps) {
  const router = useRouter();
  const isEdit = !!userId;
  const [loading, setLoading] = useState(isEdit);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [fieldError, setFieldError] = useState<Record<string, string>>({});
  const [success, setSuccess] = useState("");
  const [form, setForm] = useState({
    usr_id: "",
    usr_fname: "",
    usr_lname: "",
    usr_pwd: "",
    usr_type: "U",
  });

  useEffect(() => {
    if (!userId) return;
    setLoading(true);
    api
      .get<UserRead>(`/api/users/${userId}`)
      .then((data) => {
        setForm({
          usr_id: data.usr_id,
          usr_fname: data.usr_fname,
          usr_lname: data.usr_lname,
          usr_pwd: "",
          usr_type: data.usr_type,
        });
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [userId]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFieldError((prev) => ({ ...prev, [name]: "" }));
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");
    setFieldError({});

    try {
      if (isEdit) {
        const body: UserUpdate = {
          usr_fname: form.usr_fname,
          usr_lname: form.usr_lname,
          usr_type: form.usr_type,
        };
        if (form.usr_pwd) body.usr_pwd = form.usr_pwd;
        const res = await api.put<MessageResponse>(`/api/users/${userId}`, body);
        setSuccess(res.message || "User updated successfully.");
      } else {
        const body: UserCreate = {
          usr_id: form.usr_id,
          usr_fname: form.usr_fname,
          usr_lname: form.usr_lname,
          usr_pwd: form.usr_pwd,
          usr_type: form.usr_type,
        };
        const res = await api.post<MessageResponse>("/api/users", body);
        setSuccess(res.message || "User created successfully.");
        router.push("/admin/users");
      }
    } catch (err) {
      if (err instanceof ApiError && err.field) {
        setFieldError({ [err.field]: err.message });
      } else if (err instanceof Error) {
        setError(err.message);
      }
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && <AlertMessage type="error" message={error} onDismiss={() => setError("")} />}
      {success && <AlertMessage type="success" message={success} onDismiss={() => setSuccess("")} />}

      <section className="rounded-lg border border-gray-200 bg-white">
        <div className="border-b border-gray-200 bg-gray-50 px-6 py-3">
          <h3 className="text-sm font-semibold text-gray-700">{isEdit ? "Edit User" : "Create User"}</h3>
        </div>
        <div className="grid grid-cols-1 gap-4 p-6 sm:grid-cols-2">
          <FormField
            label="User ID"
            name="usr_id"
            value={form.usr_id}
            onChange={handleChange}
            required
            disabled={isEdit}
            error={fieldError.usr_id}
          />
          <FormField
            label="First Name"
            name="usr_fname"
            value={form.usr_fname}
            onChange={handleChange}
            required
            error={fieldError.usr_fname}
          />
          <FormField
            label="Last Name"
            name="usr_lname"
            value={form.usr_lname}
            onChange={handleChange}
            required
            error={fieldError.usr_lname}
          />
          <FormField
            label={isEdit ? "New Password (leave blank to keep)" : "Password"}
            name="usr_pwd"
            type="password"
            value={form.usr_pwd}
            onChange={handleChange}
            required={!isEdit}
            error={fieldError.usr_pwd}
          />
          <FormField
            label="User Type"
            name="usr_type"
            value={form.usr_type}
            onChange={handleChange}
            options={[
              { value: "U", label: "Regular User" },
              { value: "A", label: "Administrator" },
            ]}
            error={fieldError.usr_type}
          />
        </div>
      </section>

      <div className="flex justify-end gap-3">
        <button
          type="button"
          onClick={() => router.push("/admin/users")}
          className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={saving}
          className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-brand-700 disabled:opacity-50"
        >
          {saving ? "Saving..." : isEdit ? "Save Changes" : "Create User"}
        </button>
      </div>
    </form>
  );
}
