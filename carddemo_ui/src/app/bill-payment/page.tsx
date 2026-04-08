/**
 * Bill Payment landing page — entry point for COBIL00C.
 * Prompts for an account ID, verifies it exists, then routes to the
 * existing /accounts/{id}/payment page.
 */
'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { AppShell } from '@/components/layout/AppShell';
import { Button } from '@/components/ui/Button';
import { FormField, Input } from '@/components/ui/FormField';
import { Alert } from '@/components/ui/Alert';
import { ROUTES } from '@/lib/constants/routes';
import { accountService } from '@/services/accountService';
import { extractErrorMessage } from '@/services/apiClient';

export default function BillPaymentPage() {
  const router = useRouter();
  const [accountId, setAccountId] = useState('');
  const [error, setError] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const errorTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (errorTimerRef.current) clearTimeout(errorTimerRef.current);
    };
  }, []);

  const showError = (msg: string) => {
    if (errorTimerRef.current) clearTimeout(errorTimerRef.current);
    setError(msg);
    errorTimerRef.current = setTimeout(() => {
      setError('');
      errorTimerRef.current = null;
    }, 2000);
  };

  const handleAccountIdChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const digitsOnly = e.target.value.replace(/\D/g, '').slice(0, 11);
    setAccountId(digitsOnly);
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = accountId.trim();
    if (!trimmed) {
      showError('Please enter an account ID');
      return;
    }
    if (trimmed.length !== 11) {
      showError('Account number should be a 11 digit number');
      return;
    }
    const parsed = parseInt(trimmed, 10);
    if (isNaN(parsed) || parsed <= 0) {
      showError('Account ID must be a positive number');
      return;
    }
    setIsSearching(true);
    try {
      await accountService.getAccount(parsed);
      router.push(ROUTES.ACCOUNT_PAYMENT(parsed));
    } catch (err) {
      showError(extractErrorMessage(err));
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <AppShell>
      <div className="max-w-xl mx-auto">
        <div className="page-header">
          <div>
            <h1 className="page-title">Bill Payment</h1>
            <p className="page-subtitle">COBIL00C — Pay an account balance</p>
          </div>
        </div>

        <div className="card">
          <form onSubmit={handleSearch} className="space-y-4">
            {error && <Alert variant="error">{error}</Alert>}

            <FormField
              label="Account ID"
              htmlFor="account_id"
              hint="Enter the 11-digit account ID to make a payment for"
              required
            >
              <Input
                id="account_id"
                type="text"
                inputMode="numeric"
                maxLength={11}
                autoFocus
                placeholder="e.g. 10000000001"
                value={accountId}
                onChange={handleAccountIdChange}
              />
            </FormField>

            <Button type="submit" variant="primary" isLoading={isSearching}>
              Continue to Payment
            </Button>
          </form>
        </div>
      </div>
    </AppShell>
  );
}
