/**
 * Add user page — derived from COUSR01C (CICS transaction CU01).
 * BMS map: COUSR01
 *
 * COBOL validation:
 *   - user_id: max 8 chars, uppercased
 *   - password: max 8 chars
 *   - Duplicate user → 409 Conflict (CICS DUPREC)
 */
'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { AppShell } from '@/components/layout/AppShell';
import { Button } from '@/components/ui/Button';
import { FormField, Input, Select } from '@/components/ui/FormField';
import { Alert } from '@/components/ui/Alert';
import { userService } from '@/services/userService';
import { userCreateSchema, type UserCreateFormValues } from '@/lib/validators/user';
import { extractErrorMessage } from '@/services/apiClient';
import { ROUTES } from '@/lib/constants/routes';

export default function NewUserPage() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<UserCreateFormValues>({
    resolver: zodResolver(userCreateSchema),
    defaultValues: { user_type: 'U' },
  });

  const onSubmit = async (values: UserCreateFormValues) => {
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      await userService.createUser({
        user_id: values.user_id,
        password: values.password,
        first_name: values.first_name,
        last_name: values.last_name,
        user_type: values.user_type,
      });
      router.push(ROUTES.ADMIN_USERS);
    } catch (err) {
      setSubmitError(extractErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AppShell>
      <div className="max-w-xl mx-auto">
        <div className="page-header">
          <div>
            <h1 className="page-title">Add User</h1>
            <p className="page-subtitle">COUSR01C</p>
          </div>
          <Link href={ROUTES.ADMIN_USERS}>
            <Button variant="outline" size="sm">Cancel</Button>
          </Link>
        </div>

        <div className="card">
          {submitError && <Alert variant="error" className="mb-4">{submitError}</Alert>}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              label="User ID"
              htmlFor="user_id"
              error={errors.user_id?.message}
              hint="SEC-USR-ID PIC X(08) — max 8 chars, uppercased"
              required
            >
              <Input
                id="user_id"
                autoFocus
                maxLength={8}
                autoCapitalize="characters"
                placeholder="e.g. JDOE0001"
                hasError={!!errors.user_id}
                {...register('user_id')}
              />
            </FormField>

            <FormField
              label="Password"
              htmlFor="password"
              error={errors.password?.message}
              hint="SEC-USR-PWD PIC X(08) — max 8 chars"
              required
            >
              <Input
                id="password"
                type="password"
                maxLength={8}
                hasError={!!errors.password}
                {...register('password')}
              />
            </FormField>

            <div className="grid grid-cols-2 gap-4">
              <FormField label="First Name" htmlFor="first_name" error={errors.first_name?.message}>
                <Input id="first_name" maxLength={20} {...register('first_name')} />
              </FormField>
              <FormField label="Last Name" htmlFor="last_name" error={errors.last_name?.message}>
                <Input id="last_name" maxLength={20} {...register('last_name')} />
              </FormField>
            </div>

            <FormField
              label="User Type"
              htmlFor="user_type"
              error={errors.user_type?.message}
              hint="SEC-USR-TYPE: A=admin, U=regular"
            >
              <Select id="user_type" {...register('user_type')}>
                <option value="U">U — Regular User</option>
                <option value="A">A — Administrator</option>
              </Select>
            </FormField>

            <div className="flex justify-end gap-3 pt-2">
              <Link href={ROUTES.ADMIN_USERS}>
                <Button variant="outline">Cancel</Button>
              </Link>
              <Button type="submit" variant="primary" isLoading={isSubmitting}>
                Create User
              </Button>
            </div>
          </form>
        </div>
      </div>
    </AppShell>
  );
}
