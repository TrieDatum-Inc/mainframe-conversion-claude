/**
 * Account Update page — COACTUP (BMS map CACTUPA)
 *
 * Route: /accounts/update
 * API: GET /api/v1/accounts/{account_id} (load), PUT /api/v1/accounts/{account_id} (save)
 * COBOL program: COACTUPC
 *
 * Modern UI improvements over BMS:
 *   - Date fields as single <input type="date"> (NOT split year/month/day like CACTUPA BMS)
 *   - SSN as three separate inputs (matching ACTSSN1/2/3 BMS structure)
 *   - Phone as single NNN-NNN-NNNN input (NOT split parts like ACSPH1A/B/C)
 *   - SSN displayed masked in confirmation; not shown in plain text
 *
 * DRK button pattern: Save/Cancel buttons hidden until data loaded
 *   → React state showSaveCancel (mirrors FKEY05 DRK / FKEY12 DRK pattern)
 *
 * COACTUPC validation rules enforced by Zod + Pydantic backend:
 *   - active_status Y or N
 *   - dates valid calendar dates
 *   - credit_limit >= 0, cash_credit_limit <= credit_limit
 *   - first/last name alpha-only
 *   - SSN part1 not 000, not 666, not 900-999
 *   - fico_score 300-850
 *   - phone NNN-NNN-NNNN format
 */

'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { getAccount, updateAccount, extractError } from '@/lib/api';
import type { AccountViewResponse, AccountUpdateRequest } from '@/types';
import { MessageBar } from '@/components/ui/MessageBar';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

function AccountUpdateForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialAccountId = searchParams.get('accountId') || '';

  const [accountIdInput, setAccountIdInput] = useState(initialAccountId);
  const [account, setAccount] = useState<AccountViewResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [showSaveCancel, setShowSaveCancel] = useState(false);

  // Account fields
  const [activeStatus, setActiveStatus] = useState('Y');
  const [openDate, setOpenDate] = useState('');
  const [expirationDate, setExpirationDate] = useState('');
  const [reissueDate, setReissueDate] = useState('');
  const [creditLimit, setCreditLimit] = useState('');
  const [cashCreditLimit, setCashCreditLimit] = useState('');
  const [currentBalance, setCurrentBalance] = useState('');
  const [currCycleCredit, setCurrCycleCredit] = useState('');
  const [currCycleDebit, setCurrCycleDebit] = useState('');
  const [groupId, setGroupId] = useState('');

  // Customer fields
  const [firstName, setFirstName] = useState('');
  const [middleName, setMiddleName] = useState('');
  const [lastName, setLastName] = useState('');
  const [addressLine1, setAddressLine1] = useState('');
  const [addressLine2, setAddressLine2] = useState('');
  const [city, setCity] = useState('');
  const [stateCode, setStateCode] = useState('');
  const [zipCode, setZipCode] = useState('');
  const [countryCode, setCountryCode] = useState('');
  const [phone1, setPhone1] = useState('');
  const [phone2, setPhone2] = useState('');
  const [ssnPart1, setSsnPart1] = useState('');
  const [ssnPart2, setSsnPart2] = useState('');
  const [ssnPart3, setSsnPart3] = useState('');
  const [dateOfBirth, setDateOfBirth] = useState('');
  const [ficoScore, setFicoScore] = useState('');
  const [governmentIdRef, setGovernmentIdRef] = useState('');
  const [eftAccountId, setEftAccountId] = useState('');
  const [primaryCardHolder, setPrimaryCardHolder] = useState('Y');

  useEffect(() => {
    if (initialAccountId) {
      loadAccount(parseInt(initialAccountId, 10));
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  function populateForm(data: AccountViewResponse) {
    setActiveStatus(data.active_status);
    setOpenDate(data.open_date || '');
    setExpirationDate(data.expiration_date || '');
    setReissueDate(data.reissue_date || '');
    setCreditLimit(data.credit_limit);
    setCashCreditLimit(data.cash_credit_limit);
    setCurrentBalance(data.current_balance);
    setCurrCycleCredit(data.curr_cycle_credit);
    setCurrCycleDebit(data.curr_cycle_debit);
    setGroupId(data.group_id || '');

    const c = data.customer;
    setFirstName(c.first_name);
    setMiddleName(c.middle_name || '');
    setLastName(c.last_name);
    setAddressLine1(c.address_line_1 || '');
    setAddressLine2(c.address_line_2 || '');
    setCity(c.city || '');
    setStateCode(c.state_code || '');
    setZipCode(c.zip_code || '');
    setCountryCode(c.country_code || '');
    setPhone1(c.phone_1 || '');
    setPhone2(c.phone_2 || '');
    // SSN is masked in view; split into parts for editing
    // Parts cannot be pre-populated from masked display — user must re-enter
    setSsnPart1('');
    setSsnPart2('');
    setSsnPart3('');
    setDateOfBirth(c.date_of_birth || '');
    setFicoScore(c.fico_score != null ? String(c.fico_score) : '');
    setGovernmentIdRef(c.government_id_ref || '');
    setEftAccountId(c.eft_account_id || '');
    setPrimaryCardHolder(c.primary_card_holder);
  }

  async function loadAccount(id: number) {
    setLoading(true);
    setError('');
    setShowSaveCancel(false);
    try {
      const data = await getAccount(id);
      setAccount(data);
      populateForm(data);
      setShowSaveCancel(true); // mirrors DRK button pattern — show after data load
    } catch (err) {
      setError(extractError(err).message);
    } finally {
      setLoading(false);
    }
  }

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!accountIdInput.trim()) {
      setError('Account ID cannot be empty');
      return;
    }
    await loadAccount(parseInt(accountIdInput.trim(), 10));
  }

  function validateForm(): string | null {
    if (!['Y', 'N'].includes(activeStatus)) return 'Active status must be Y or N';
    if (!openDate) return 'Open date is required';
    if (!expirationDate) return 'Expiration date is required';
    if (!reissueDate) return 'Reissue date is required';
    const cl = parseFloat(creditLimit);
    const ccl = parseFloat(cashCreditLimit);
    if (isNaN(cl) || cl < 0) return 'Credit limit must be >= 0';
    if (isNaN(ccl) || ccl < 0) return 'Cash credit limit must be >= 0';
    if (ccl > cl) return 'Cash credit limit must not exceed credit limit';
    if (!firstName.trim()) return 'First name is required';
    if (!lastName.trim()) return 'Last name is required';
    if (!/^[A-Za-z\s\-']+$/.test(firstName)) return 'First name must contain only letters';
    if (!/^[A-Za-z\s\-']+$/.test(lastName)) return 'Last name must contain only letters';
    if (ssnPart1) {
      const p1 = parseInt(ssnPart1, 10);
      if (p1 === 0) return 'SSN part 1 cannot be 000';
      if (p1 === 666) return 'SSN part 1 cannot be 666';
      if (p1 >= 900 && p1 <= 999) return 'SSN part 1 cannot be in range 900-999';
    }
    if (ficoScore) {
      const fico = parseInt(ficoScore, 10);
      if (isNaN(fico) || fico < 300 || fico > 850) return 'FICO score must be between 300 and 850';
    }
    return null;
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    if (!account) return;

    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    setSaving(true);
    setError('');
    setSuccessMsg('');

    try {
      const payload: AccountUpdateRequest = {
        active_status: activeStatus as 'Y' | 'N',
        open_date: openDate,
        expiration_date: expirationDate,
        reissue_date: reissueDate,
        credit_limit: creditLimit,
        cash_credit_limit: cashCreditLimit,
        current_balance: currentBalance,
        curr_cycle_credit: currCycleCredit,
        curr_cycle_debit: currCycleDebit,
        group_id: groupId || undefined,
        customer: {
          customer_id: account.customer.customer_id,
          first_name: firstName,
          middle_name: middleName || undefined,
          last_name: lastName,
          address_line_1: addressLine1 || undefined,
          address_line_2: addressLine2 || undefined,
          city: city || undefined,
          state_code: stateCode || undefined,
          zip_code: zipCode || undefined,
          country_code: countryCode || undefined,
          phone_1: phone1 || undefined,
          phone_2: phone2 || undefined,
          ssn_part1: ssnPart1 || '000',
          ssn_part2: ssnPart2 || '00',
          ssn_part3: ssnPart3 || '0000',
          date_of_birth: dateOfBirth,
          fico_score: ficoScore ? parseInt(ficoScore, 10) : undefined,
          government_id_ref: governmentIdRef || undefined,
          eft_account_id: eftAccountId || undefined,
          primary_card_holder: primaryCardHolder as 'Y' | 'N',
        },
      };

      const updated = await updateAccount(account.account_id, payload);
      setAccount(updated);
      populateForm(updated);
      setSuccessMsg('Account updated successfully');
    } catch (err) {
      setError(extractError(err).message);
    } finally {
      setSaving(false);
    }
  }

  function handleCancel() {
    if (account) populateForm(account);
    setError('');
    setSuccessMsg('');
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-blue-900 text-white px-6 py-4">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-yellow-300">CardDemo</h1>
            <p className="text-sm text-blue-200">Credit Card Demo Application</p>
          </div>
          <div className="text-sm text-blue-200">
            <span className="font-medium text-white">COACTUP</span> — Account Update
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-6 py-6">
        {/* Account ID search */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <form onSubmit={handleSearch} className="flex gap-3 items-end">
            <div className="flex-1">
              <label htmlFor="accountIdInput" className="block text-sm font-medium text-gray-700 mb-1">
                Account ID
              </label>
              <input
                id="accountIdInput"
                type="text"
                value={accountIdInput}
                onChange={(e) => setAccountIdInput(e.target.value)}
                maxLength={11}
                placeholder="11-digit account number"
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm font-mono
                           focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 bg-blue-600 text-white rounded-md text-sm font-medium
                         hover:bg-blue-700 disabled:opacity-50"
            >
              Load
            </button>
            <button
              type="button"
              onClick={() => router.back()}
              className="px-6 py-2 bg-gray-100 text-gray-700 rounded-md text-sm font-medium
                         hover:bg-gray-200 border border-gray-300"
            >
              Back
            </button>
          </form>
        </div>

        {error && <MessageBar message={error} color="red" className="mb-4" />}
        {successMsg && <MessageBar message={successMsg} color="green" className="mb-4" />}
        {loading && <div className="flex justify-center py-12"><LoadingSpinner /></div>}

        {account && !loading && (
          <form onSubmit={handleSave}>
            {/* Account fields */}
            <div className="bg-white rounded-lg shadow p-6 mb-6">
              <h3 className="text-base font-semibold text-gray-900 mb-4">
                Account #{account.account_id}
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-x-6 gap-y-4">
                <FormField label="Active Status" required>
                  <select
                    value={activeStatus}
                    onChange={(e) => setActiveStatus(e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  >
                    <option value="Y">Y - Active</option>
                    <option value="N">N - Inactive</option>
                  </select>
                </FormField>
                <FormField label="Open Date" required>
                  <input type="date" value={openDate} onChange={(e) => setOpenDate(e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm" />
                </FormField>
                <FormField label="Expiration Date" required>
                  <input type="date" value={expirationDate} onChange={(e) => setExpirationDate(e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm" />
                </FormField>
                <FormField label="Reissue Date" required>
                  <input type="date" value={reissueDate} onChange={(e) => setReissueDate(e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm" />
                </FormField>
                <FormField label="Credit Limit">
                  <input type="number" step="0.01" min="0" value={creditLimit}
                    onChange={(e) => setCreditLimit(e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-right" />
                </FormField>
                <FormField label="Cash Credit Limit">
                  <input type="number" step="0.01" min="0" value={cashCreditLimit}
                    onChange={(e) => setCashCreditLimit(e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-right" />
                </FormField>
                <FormField label="Current Balance">
                  <input type="number" step="0.01" value={currentBalance}
                    onChange={(e) => setCurrentBalance(e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-right" />
                </FormField>
                <FormField label="Cycle Credit">
                  <input type="number" step="0.01" min="0" value={currCycleCredit}
                    onChange={(e) => setCurrCycleCredit(e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-right" />
                </FormField>
                <FormField label="Cycle Debit">
                  <input type="number" step="0.01" min="0" value={currCycleDebit}
                    onChange={(e) => setCurrCycleDebit(e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-right" />
                </FormField>
                <FormField label="Account Group">
                  <input type="text" maxLength={10} value={groupId}
                    onChange={(e) => setGroupId(e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm" />
                </FormField>
              </div>
            </div>

            {/* Customer fields */}
            <div className="bg-white rounded-lg shadow p-6 mb-6">
              <h3 className="text-base font-semibold text-gray-900 mb-4">
                Customer Information
                <span className="ml-2 text-sm font-normal text-gray-500">
                  ID: {account.customer.customer_id}
                </span>
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-x-6 gap-y-4">
                <FormField label="First Name" required>
                  <input type="text" maxLength={25} value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm" />
                </FormField>
                <FormField label="Middle Name">
                  <input type="text" maxLength={25} value={middleName}
                    onChange={(e) => setMiddleName(e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm" />
                </FormField>
                <FormField label="Last Name" required>
                  <input type="text" maxLength={25} value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm" />
                </FormField>

                {/* SSN — three parts matching ACTSSN1/2/3 BMS fields */}
                <FormField label="SSN">
                  <div className="flex items-center gap-1">
                    <input type="text" maxLength={3} value={ssnPart1}
                      onChange={(e) => setSsnPart1(e.target.value)}
                      placeholder="XXX" className="w-16 border border-gray-300 rounded-md px-2 py-2 text-sm font-mono text-center" />
                    <span className="text-gray-400">-</span>
                    <input type="text" maxLength={2} value={ssnPart2}
                      onChange={(e) => setSsnPart2(e.target.value)}
                      placeholder="XX" className="w-12 border border-gray-300 rounded-md px-2 py-2 text-sm font-mono text-center" />
                    <span className="text-gray-400">-</span>
                    <input type="text" maxLength={4} value={ssnPart3}
                      onChange={(e) => setSsnPart3(e.target.value)}
                      placeholder="XXXX" className="w-16 border border-gray-300 rounded-md px-2 py-2 text-sm font-mono text-center" />
                    <span className="text-xs text-gray-400 ml-1">
                      (Current: {account.customer.ssn_masked})
                    </span>
                  </div>
                </FormField>

                <FormField label="Date of Birth" required>
                  <input type="date" value={dateOfBirth}
                    onChange={(e) => setDateOfBirth(e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm" />
                </FormField>
                <FormField label="FICO Score">
                  <input type="number" min={300} max={850} value={ficoScore}
                    onChange={(e) => setFicoScore(e.target.value)}
                    placeholder="300-850"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm" />
                </FormField>

                <FormField label="Address Line 1">
                  <input type="text" maxLength={50} value={addressLine1}
                    onChange={(e) => setAddressLine1(e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm" />
                </FormField>
                <FormField label="Address Line 2">
                  <input type="text" maxLength={50} value={addressLine2}
                    onChange={(e) => setAddressLine2(e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm" />
                </FormField>
                <FormField label="City">
                  <input type="text" maxLength={50} value={city}
                    onChange={(e) => setCity(e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm" />
                </FormField>
                <FormField label="State">
                  <input type="text" maxLength={2} value={stateCode}
                    onChange={(e) => setStateCode(e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm uppercase" />
                </FormField>
                <FormField label="ZIP Code">
                  <input type="text" maxLength={10} value={zipCode}
                    onChange={(e) => setZipCode(e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm" />
                </FormField>
                <FormField label="Country">
                  <input type="text" maxLength={3} value={countryCode}
                    onChange={(e) => setCountryCode(e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm uppercase" />
                </FormField>
                <FormField label="Phone 1">
                  <input type="text" value={phone1}
                    onChange={(e) => setPhone1(e.target.value)}
                    placeholder="NNN-NNN-NNNN"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm font-mono" />
                </FormField>
                <FormField label="Phone 2">
                  <input type="text" value={phone2}
                    onChange={(e) => setPhone2(e.target.value)}
                    placeholder="NNN-NNN-NNNN"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm font-mono" />
                </FormField>
                <FormField label="Govt ID Reference">
                  <input type="text" maxLength={20} value={governmentIdRef}
                    onChange={(e) => setGovernmentIdRef(e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm" />
                </FormField>
                <FormField label="EFT Account ID">
                  <input type="text" maxLength={10} value={eftAccountId}
                    onChange={(e) => setEftAccountId(e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm" />
                </FormField>
                <FormField label="Primary Card Holder" required>
                  <select value={primaryCardHolder} onChange={(e) => setPrimaryCardHolder(e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm">
                    <option value="Y">Y - Primary</option>
                    <option value="N">N - Secondary</option>
                  </select>
                </FormField>
              </div>
            </div>

            {/* Action buttons — DRK pattern: only shown after data loaded */}
            {showSaveCancel && (
              <div className="flex gap-3 justify-end">
                <button
                  type="button"
                  onClick={handleCancel}
                  className="px-6 py-2 bg-gray-100 text-gray-700 rounded-md text-sm font-medium
                             hover:bg-gray-200 border border-gray-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="px-8 py-2 bg-blue-600 text-white rounded-md text-sm font-medium
                             hover:bg-blue-700 disabled:opacity-50"
                >
                  {saving ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            )}
          </form>
        )}
      </div>
    </div>
  );
}

function FormField({
  label,
  required,
  children,
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>
      {children}
    </div>
  );
}

export default function AccountUpdatePage() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <AccountUpdateForm />
    </Suspense>
  );
}
