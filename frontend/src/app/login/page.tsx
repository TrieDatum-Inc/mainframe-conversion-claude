/**
 * Login Page — replaces COSGN00 BMS map (COSGN0A).
 *
 * Route: /login
 * COBOL program: COSGN00C (Transaction: CC00)
 * BMS mapset: COSGN00, map: COSGN0A
 *
 * This page implements a modern, web-friendly login form that preserves
 * all the functional behavior of the 3270 COSGN0A map:
 *
 * BMS → React field mapping:
 *   USERID  (FSET,IC,NORM,UNPROT,GREEN) → userId input (autoFocus, text)
 *   PASSWD  (DRK,FSET,UNPROT)           → password input (type="password")
 *   ERRMSG  (ASKIP,BRT,FSET,RED)        → error message bar
 *   ENTER key                            → "Sign On" submit button
 *   PF3                                  → "Exit" button
 *
 * Decorative ASCII art (rows 7-15) preserved as a modern card element.
 *
 * Validation (maps COSGN00C PROCESS-ENTER-KEY):
 *   - userId: required, max 8 chars (USERIDI field constraint)
 *   - password: required (PASSWDI field constraint)
 *
 * Auth flow (maps COSGN00C PROCESS-ENTER-KEY → XCTL):
 *   Success + user_type='A' → navigate to /admin/menu (was XCTL COADM01C)
 *   Success + user_type='U' → navigate to /menu (was XCTL COMEN01C)
 *   Failure → display error in ERRMSG bar, clear password field
 */

'use client';

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useRouter, useSearchParams } from 'next/navigation';
import { authApi, ApiClientError } from '@/lib/api-client';
import { useAuthStore } from '@/stores/auth-store';
import { AppHeader } from '@/components/layout/AppHeader';
import { ErrorMessage } from '@/components/ui/ErrorMessage';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

/**
 * Zod validation schema for the login form.
 *
 * Maps COSGN00C PROCESS-ENTER-KEY validation:
 *   IF WS-USER-ID = SPACES → USERID_REQUIRED error
 *   IF WS-USER-PWD = SPACES → PASSWORD_REQUIRED error
 *
 * Note: max_length follows PASSWDI original 8-char BMS field limit.
 * The backend accepts up to 72 chars (bcrypt limit) for new users.
 */
const loginSchema = z.object({
  userId: z
    .string()
    .min(1, 'User ID cannot be empty')
    .max(8, 'User ID must be 8 characters or less'),
  password: z
    .string()
    .min(1, 'Password cannot be empty')
    .max(72, 'Password is too long'),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login, isAuthenticated, user } = useAuthStore();
  const [serverError, setServerError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    resetField,
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
  });

  // If already authenticated, redirect to appropriate menu
  // Maps: COSGN00C behavior when COMMAREA already has signed-on user
  useEffect(() => {
    if (isAuthenticated && user) {
      const destination = user.user_type === 'A' ? '/admin/menu' : '/menu';
      router.replace(destination);
    }
  }, [isAuthenticated, user, router]);

  // Display session expiry message if redirected from middleware
  const reason = searchParams?.get('reason');
  const sessionExpiredMessage =
    reason === 'session_expired' ? 'Your session has expired. Please sign in again.' : '';

  /**
   * Handle form submission — maps COSGN00C PROCESS-ENTER-KEY paragraph.
   *
   * Flow:
   * 1. POST /api/v1/auth/login (replaces EXEC CICS READ DATASET(USRSEC))
   * 2. Store JWT + user info (replaces COMMAREA population)
   * 3. Navigate to redirect_to (replaces CICS XCTL routing)
   * 4. On error: show ERRMSG, clear password (replaces re-send MAP)
   */
  const onSubmit = async (values: LoginFormValues) => {
    setServerError('');
    setIsLoading(true);

    try {
      const response = await authApi.login({
        user_id: values.userId.trim(),
        password: values.password,
      });

      // Store auth state (replaces COMMAREA population in COSGN00C)
      login(response);

      // Set auth cookie for middleware route protection
      if (typeof document !== 'undefined') {
        document.cookie = `carddemo_auth_token=${response.access_token}; path=/; max-age=3600; SameSite=Strict`;
      }

      // Navigate to appropriate menu (replaces CICS XCTL)
      router.push(response.redirect_to);
    } catch (error) {
      // ERRMSG bar equivalent — display error, clear password
      // Maps COSGN00C: MOVE WS-MESSAGE TO ERRMSGO; clear PASSWDI
      if (error instanceof ApiClientError) {
        setServerError(error.message);
      } else {
        setServerError('An unexpected error occurred. Please try again.');
      }
      resetField('password');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-gray-950">
      {/* BMS header rows 1-3 */}
      <AppHeader programName="COSGN00C" transactionId="CC00" />

      {/* Main content */}
      <main className="flex-1 flex flex-col items-center justify-center px-4 py-8">

        {/* Row 5: Application description */}
        <p className="text-gray-400 text-sm mb-8 text-center">
          This is a Credit Card Demo Application for Mainframe Modernization
        </p>

        {/* Rows 7-15: NATIONAL RESERVE NOTE decorative art */}
        <div className="font-mono text-blue-400 text-xs mb-8 border border-blue-700 p-0 hidden md:block">
          <div className="px-2 py-1">+========================================+</div>
          <div className="px-2 py-0">|%%%%%%%  NATIONAL RESERVE NOTE  %%%%%%%%|</div>
          <div className="px-2 py-0">|%(1)  THE UNITED STATES OF KICSLAND (1)%|</div>
          <div className="px-2 py-0">|%$$              ___       ********  $$%|</div>
          <div className="px-2 py-0">|%$    {'{x}'}       (o o)                 $%|</div>
          <div className="px-2 py-0">|%$     ******  (  V  )      O N E     $%|</div>
          <div className="px-2 py-0">|%(1)          ---m-m---             (1)%|</div>
          <div className="px-2 py-0">|%%~~~~~~~~~~~ ONE DOLLAR ~~~~~~~~~~~~~%%|</div>
          <div className="px-2 py-1">+========================================+</div>
        </div>

        {/* Login card — maps rows 17-20 of COSGN0A */}
        <div className="w-full max-w-md bg-gray-900 rounded-lg shadow-xl border border-gray-700 p-8">

          {/* Row 17: Instruction line */}
          <p className="text-cyan-400 text-sm text-center mb-6">
            Type your User ID and Password, then press ENTER:
          </p>

          <form onSubmit={handleSubmit(onSubmit)} noValidate>
            <div className="space-y-5">

              {/* Row 19: User ID field — USERID (FSET,IC,NORM,UNPROT,GREEN) */}
              <div>
                <label htmlFor="userId" className="block text-sm font-medium text-cyan-400 mb-1">
                  User ID
                  <span className="text-gray-500 ml-2 text-xs">(8 Char)</span>
                </label>
                <input
                  id="userId"
                  type="text"
                  maxLength={8}
                  autoFocus  /* IC — initial cursor position */
                  autoComplete="username"
                  autoCapitalize="characters"
                  placeholder="USERID"
                  className={`form-input bg-gray-800 border-gray-600 text-green-400 placeholder-gray-600
                    focus:border-green-500 focus:ring-green-500 font-mono tracking-wider uppercase
                    ${errors.userId ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}`}
                  aria-describedby={errors.userId ? 'userId-error' : undefined}
                  {...register('userId', {
                    onChange: (e) => {
                      // Auto-uppercase — mirrors COBOL uppercase field behavior
                      e.target.value = e.target.value.toUpperCase();
                    },
                  })}
                />
                {errors.userId && (
                  <p id="userId-error" className="mt-1 text-xs text-red-400">
                    {errors.userId.message}
                  </p>
                )}
              </div>

              {/* Row 20: Password field — PASSWD (DRK,FSET,UNPROT) */}
              <div>
                <label htmlFor="password" className="block text-sm font-medium text-cyan-400 mb-1">
                  Password
                  <span className="text-gray-500 ml-2 text-xs">(8 Char)</span>
                </label>
                <input
                  id="password"
                  type="password"  /* DRK attribute → type="password" for masking */
                  maxLength={72}   /* extended from 8 (bcrypt limit) */
                  autoComplete="current-password"
                  placeholder="••••••••"
                  className={`form-input bg-gray-800 border-gray-600 text-green-400 placeholder-gray-700
                    focus:border-green-500 focus:ring-green-500 font-mono
                    ${errors.password ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}`}
                  aria-describedby={errors.password ? 'password-error' : undefined}
                  {...register('password')}
                />
                {errors.password && (
                  <p id="password-error" className="mt-1 text-xs text-red-400">
                    {errors.password.message}
                  </p>
                )}
              </div>

              {/* Submit button — ENTER key equivalent */}
              <button
                type="submit"
                disabled={isLoading}
                className="btn-primary w-full"
              >
                {isLoading ? (
                  <LoadingSpinner size="sm" label="Signing on..." />
                ) : (
                  'Sign On'
                )}
              </button>
            </div>
          </form>

          {/* PF key legend row 24 */}
          <div className="mt-6 pt-4 border-t border-gray-700">
            <p className="text-yellow-500 text-xs font-mono text-center">
              ENTER=Sign-on&nbsp;&nbsp;&nbsp;F3=Exit
            </p>
          </div>
        </div>
      </main>

      {/* Row 23: ERRMSG bar — ASKIP, BRT, FSET, RED */}
      <div className="sticky bottom-0">
        {(serverError || sessionExpiredMessage) && (
          <ErrorMessage
            message={serverError || sessionExpiredMessage}
            color={serverError ? 'red' : 'neutral'}
          />
        )}
      </div>
    </div>
  );
}
