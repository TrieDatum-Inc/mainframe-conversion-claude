"use client";

/**
 * UserForm component — shared form for Add User (COUSR01C) and Update User (COUSR02C).
 *
 * BMS field mappings:
 *   FNAME    → first_name (20 chars)
 *   LNAME    → last_name  (20 chars)
 *   USERID   → user_id    (8 chars, add-only, disabled on edit)
 *   PASSWD   → password   (8 chars, DRK/non-display → type="password")
 *   USRTYPE  → user_type  (A/U dropdown)
 *
 * COUSR02C behaviour:
 *   - Password field optional on update (only send if non-empty)
 *   - Shows current values pre-populated
 *   - 400 response ("Please modify") shown as inline error
 */
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import type { User, UserType } from "@/types";

// Validation schema mirrors COUSR01C/02C field rules
const baseSchema = z.object({
  first_name: z
    .string()
    .min(1, "First name is required")
    .max(20, "First name must be 20 characters or fewer")
    .trim(),
  last_name: z
    .string()
    .min(1, "Last name is required")
    .max(20, "Last name must be 20 characters or fewer")
    .trim(),
  user_type: z.enum(["A", "U"], {
    errorMap: () => ({ message: "User type must be A (Admin) or U (User)" }),
  }),
  password: z.string().max(8, "Password must be 8 characters or fewer").optional(),
});

const createSchema = baseSchema.extend({
  user_id: z
    .string()
    .min(1, "User ID is required")
    .max(8, "User ID must be 8 characters or fewer")
    .regex(/^[A-Z0-9]+$/, "User ID must be uppercase alphanumeric")
    .trim(),
  password: z
    .string()
    .min(1, "Password is required")
    .max(8, "Password must be 8 characters or fewer"),
});

const updateSchema = baseSchema;

type CreateFormValues = z.infer<typeof createSchema>;
type UpdateFormValues = z.infer<typeof updateSchema>;
type FormValues = CreateFormValues | UpdateFormValues;

interface UserFormProps {
  mode: "create" | "edit";
  initialValues?: User;
  onSubmit: (values: FormValues) => Promise<void>;
  onCancel: () => void;
  isSubmitting?: boolean;
  serverError?: string | null;
}

function FieldError({ message }: { message?: string }) {
  if (!message) return null;
  return <p className="mt-1 text-xs text-red-600">{message}</p>;
}

export default function UserForm({
  mode,
  initialValues,
  onSubmit,
  onCancel,
  isSubmitting = false,
  serverError,
}: UserFormProps) {
  const schema = mode === "create" ? createSchema : updateSchema;

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema as z.ZodType<FormValues>),
    defaultValues:
      mode === "edit" && initialValues
        ? {
            first_name: initialValues.first_name,
            last_name: initialValues.last_name,
            user_type: initialValues.user_type as UserType,
            password: "",
          }
        : {
            first_name: "",
            last_name: "",
            user_id: "",
            password: "",
            user_type: "U" as UserType,
          },
  });

  useEffect(() => {
    if (mode === "edit" && initialValues) {
      reset({
        first_name: initialValues.first_name,
        last_name: initialValues.last_name,
        user_type: initialValues.user_type as UserType,
        password: "",
      });
    }
  }, [initialValues, mode, reset]);

  const inputClass =
    "mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500";
  const labelClass = "block text-sm font-medium text-gray-700";

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>
      {/* Server-side error — mirrors COUSR01C/02C ERRMSG row 23 */}
      {serverError && (
        <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
          {serverError}
        </div>
      )}

      {/* First Name — BMS FNAME field */}
      <div>
        <label htmlFor="first_name" className={labelClass}>
          First Name <span className="text-red-500">*</span>
        </label>
        <input
          id="first_name"
          type="text"
          maxLength={20}
          className={inputClass}
          {...register("first_name")}
        />
        <FieldError message={(errors as Record<string, { message?: string }>).first_name?.message} />
      </div>

      {/* Last Name — BMS LNAME field */}
      <div>
        <label htmlFor="last_name" className={labelClass}>
          Last Name <span className="text-red-500">*</span>
        </label>
        <input
          id="last_name"
          type="text"
          maxLength={20}
          className={inputClass}
          {...register("last_name")}
        />
        <FieldError message={(errors as Record<string, { message?: string }>).last_name?.message} />
      </div>

      {/* User ID — BMS USERID field (add mode only, disabled on edit) */}
      {mode === "create" && (
        <div>
          <label htmlFor="user_id" className={labelClass}>
            User ID <span className="text-red-500">*</span>{" "}
            <span className="text-gray-400 font-normal">(max 8 chars)</span>
          </label>
          <input
            id="user_id"
            type="text"
            maxLength={8}
            className={`${inputClass} font-mono uppercase`}
            placeholder="e.g. JSMITH01"
            {...register("user_id", {
              onChange: (e) => {
                e.target.value = e.target.value.toUpperCase();
              },
            })}
          />
          <FieldError message={(errors as Record<string, { message?: string }>).user_id?.message} />
        </div>
      )}

      {/* Password — BMS PASSWD field (DRK/non-display → type="password") */}
      <div>
        <label htmlFor="password" className={labelClass}>
          Password{" "}
          {mode === "create" && <span className="text-red-500">*</span>}
          {mode === "edit" && (
            <span className="text-gray-400 font-normal ml-1">
              (leave blank to keep current)
            </span>
          )}
        </label>
        <input
          id="password"
          type="password"
          maxLength={8}
          autoComplete="new-password"
          className={inputClass}
          {...register("password")}
        />
        <FieldError message={(errors as Record<string, { message?: string }>).password?.message} />
      </div>

      {/* User Type — BMS USRTYPE field (A=Admin, U=User) */}
      <div>
        <label htmlFor="user_type" className={labelClass}>
          User Type <span className="text-red-500">*</span>
        </label>
        <select
          id="user_type"
          className={inputClass}
          {...register("user_type")}
        >
          <option value="U">U — Regular User</option>
          <option value="A">A — Administrator</option>
        </select>
        <FieldError message={(errors as Record<string, { message?: string }>).user_type?.message} />
      </div>

      {/* Action buttons — mirrors BMS row 24 function key legend */}
      <div className="flex gap-3 pt-2">
        <button
          type="submit"
          disabled={isSubmitting}
          className="px-5 py-2 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSubmitting
            ? "Saving..."
            : mode === "create"
              ? "Add User (Enter)"
              : "Save Changes (F5)"}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="px-5 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-300"
        >
          Cancel (F3)
        </button>
      </div>
    </form>
  );
}
