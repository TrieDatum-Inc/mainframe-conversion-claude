'use client';

// ============================================================
// Login Page
// Mirrors COSGN00C sign-on program and COSGN00 BMS map.
// Fields: user_id (PIC X(8)), password (PIC X(8)).
// On success, navigates to /dashboard (COMEN01C or COADM01C).
// ============================================================

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Building2, Lock, User } from 'lucide-react';
import { useState } from 'react';
import toast from 'react-hot-toast';
import { useAuth, getErrorMessage } from '@/contexts/AuthContext';
import { loginSchema, type LoginFormValues } from '@/lib/validators';
import { FormField, inputClass } from '@/components/ui/FormField';

export default function LoginPage() {
  const { login } = useAuth();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (values: LoginFormValues) => {
    setIsSubmitting(true);
    try {
      await login(values.user_id, values.password);
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900 px-4">
      <div className="w-full max-w-md">
        {/* Card */}
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          {/* Header */}
          <div className="flex flex-col items-center mb-8">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-600 mb-4 shadow-lg">
              <Building2 className="h-7 w-7 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-slate-900">CardDemo</h1>
            <p className="mt-1 text-sm text-slate-500">
              Sign in to your account
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-5">
            <FormField
              label="User ID"
              htmlFor="user_id"
              error={errors.user_id}
              required
            >
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <input
                  id="user_id"
                  type="text"
                  autoComplete="username"
                  autoFocus
                  maxLength={8}
                  placeholder="Enter user ID"
                  {...register('user_id', {
                    setValueAs: (v: string) => v.toUpperCase(),
                  })}
                  className={`${inputClass(Boolean(errors.user_id))} pl-9 uppercase`}
                />
              </div>
            </FormField>

            <FormField
              label="Password"
              htmlFor="password"
              error={errors.password}
              required
            >
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  maxLength={8}
                  placeholder="Enter password"
                  {...register('password')}
                  className={`${inputClass(Boolean(errors.password))} pl-9`}
                />
              </div>
            </FormField>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2.5 rounded-lg transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {isSubmitting && (
                <span className="h-4 w-4 rounded-full border-2 border-white/30 border-t-white animate-spin" />
              )}
              {isSubmitting ? 'Signing in...' : 'Sign In'}
            </button>
          </form>
        </div>

        <p className="mt-4 text-center text-xs text-slate-400">
          AWS Mainframe Modernization — CardDemo
        </p>
      </div>
    </div>
  );
}
