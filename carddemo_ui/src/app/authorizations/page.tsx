/**
 * Authorizations landing page — entry point for COPAUS0C/COPAUS1C screens.
 * Look up authorizations by account ID.
 */
'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { AppShell } from '@/components/layout/AppShell';
import { Button } from '@/components/ui/Button';
import { FormField, Input } from '@/components/ui/FormField';
import { Alert } from '@/components/ui/Alert';
import { ROUTES } from '@/lib/constants/routes';
import { accountService } from '@/services/accountService';
import { extractErrorMessage } from '@/services/apiClient';

export default function AuthorizationsPage() {
  const router = useRouter();
  const [accountId, setAccountId] = useState('');
  const [error, setError] = useState('');
  const [isSearching, setIsSearching] = useState(false);

  // Auto-hide error after 2 seconds
  useEffect(() => {
    if (!error) return;
    const t = setTimeout(() => setError(''), 2000);
    return () => clearTimeout(t);
  }, [error]);

  const handleAccountIdChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    // Restrict input to digits only, max 11 chars
    const digitsOnly = e.target.value.replace(/\D/g, '').slice(0, 11);
    setAccountId(digitsOnly);
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = accountId.trim();
    if (!trimmed) {
      setError('Please enter an account ID');
      return;
    }
    if (trimmed.length !== 11) {
      setError('Account number should be a 11 digit number');
      return;
    }
    const parsed = parseInt(trimmed, 10);
    if (isNaN(parsed) || parsed <= 0) {
      setError('Account ID must be a positive number');
      return;
    }
    setError('');
    setIsSearching(true);
    try {
      // Verify the account exists before navigating so errors render here.
      await accountService.getAccount(parsed);
      router.push(ROUTES.AUTHORIZATION_BY_ACCOUNT(parsed));
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <AppShell>
      <div className="max-w-xl mx-auto">
        <div className="page-header">
          <div>
            <h1 className="page-title">Authorizations</h1>
            <p className="page-subtitle">COPAUS0C/COPAUS1C — View authorization history</p>
          </div>
          <Link href="/authorizations/new">
            <Button variant="primary" size="sm">Process Auth</Button>
          </Link>
        </div>

        <div className="card">
          <form onSubmit={handleSearch} className="space-y-4">
            {error && <Alert variant="error">{error}</Alert>}

            <FormField
              label="Account ID"
              htmlFor="account_id"
              hint="Look up authorization history for this account"
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
              View Authorizations
            </Button>
          </form>
        </div>
      </div>
    </AppShell>
  );
}
