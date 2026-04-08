/**
 * Login page — derived from COSGN00C (CICS transaction CC00).
 * BMS map: COSGN00 (COSGN0A)
 *
 * BMS fields mapped:
 *   USERID (UNPROT, IC, GREEN)  -> user_id input (autofocus)
 *   PASSWD (DRK, UNPROT)        -> password input (type=password)
 *   ERRMSG (BRT, RED, row 23)   -> Alert component
 */
'use client';

import { useEffect, useRef, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useRouter } from 'next/navigation';
import { authService } from '@/services/authService';
import { extractErrorMessage } from '@/services/apiClient';
import { loginSchema, type LoginFormValues } from '@/lib/validators/auth';
import { Button } from '@/components/ui/Button';
import { FormField, Input } from '@/components/ui/FormField';
import { Alert } from '@/components/ui/Alert';

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const errorTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // If already authenticated, redirect to dashboard
  useEffect(() => {
    if (authService.isAuthenticated()) {
      router.replace('/dashboard');
    }
  }, [router]);

  // Clean up the error timer on unmount
  useEffect(() => {
    return () => {
      if (errorTimerRef.current) clearTimeout(errorTimerRef.current);
    };
  }, []);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
  });

  const showError = (msg: string) => {
    if (errorTimerRef.current) clearTimeout(errorTimerRef.current);
    setError(msg);
    errorTimerRef.current = setTimeout(() => {
      setError(null);
      errorTimerRef.current = null;
    }, 2000);
  };

  const onSubmit = async (values: LoginFormValues) => {
    setIsLoading(true);
    setError(null);
    if (errorTimerRef.current) {
      clearTimeout(errorTimerRef.current);
      errorTimerRef.current = null;
    }
    try {
      await authService.login({
        user_id: values.user_id,
        password: values.password,
      });
      router.push('/dashboard');
    } catch (err) {
      showError(extractErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-950 to-gray-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md animate-fade-in">
        {/* Card */}
        <div className="bg-white rounded-2xl shadow-2xl overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-700 to-blue-600 px-8 py-8 text-center">
            <div className="flex justify-center mb-3">
              <div className="h-14 w-14 rounded-full bg-white/20 flex items-center justify-center">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={1.5}
                  stroke="currentColor"
                  className="h-8 w-8 text-white"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z"
                  />
                </svg>
              </div>
            </div>
            <h1 className="text-2xl font-bold text-white">CardDemo</h1>
            <p className="text-blue-200 text-sm mt-1">
              Credit Card Management System
            </p>
          </div>

          {/* Form */}
          <div className="px-8 py-8">
            <h2 className="text-lg font-semibold text-gray-900 mb-6">Sign in to your account</h2>

            {/* Error message — maps to ERRMSG BRT RED row 23 */}
            {error && (
              <Alert variant="error" className="mb-5">
                {error}
              </Alert>
            )}

            <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-5">
              {/* USERID field — UNPROT, IC (autofocus), GREEN */}
              <FormField
                label="User ID"
                htmlFor="user_id"
                error={errors.user_id?.message}
                required
                hint="Up to 8 characters"
              >
                <Input
                  id="user_id"
                  type="text"
                  autoFocus
                  autoComplete="username"
                  autoCapitalize="characters"
                  maxLength={8}
                  hasError={!!errors.user_id}
                  placeholder="Enter user ID"
                  {...register('user_id')}
                />
              </FormField>

              {/* PASSWD field — DRK (type=password), UNPROT */}
              <FormField
                label="Password"
                htmlFor="password"
                error={errors.password?.message}
                required
                hint="Up to 8 characters"
              >
                <Input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  maxLength={8}
                  hasError={!!errors.password}
                  placeholder="Enter password"
                  {...register('password')}
                />
              </FormField>

              {/* ENTER = Sign-on (row 24 in BMS) */}
              <Button
                type="submit"
                variant="primary"
                size="lg"
                isLoading={isLoading}
                className="w-full mt-2"
              >
                {isLoading ? 'Signing in...' : 'Sign In'}
              </Button>
            </form>

            {/* Footer hint — maps to row 24: "ENTER=Sign-on  F3=Exit" */}
            <p className="text-center text-xs text-gray-400 mt-6">
              Credit Card Demo Application for Mainframe Modernization
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
