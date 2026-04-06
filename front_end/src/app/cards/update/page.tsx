/**
 * Card Update page — COCRDUP (BMS map CCRDUPA)
 *
 * Route: /cards/update
 * API: GET /api/v1/cards/{card_number} + PUT /api/v1/cards/{card_number}
 * COBOL program: COCRDUPC
 *
 * COCRDUPC implemented a 7-state machine:
 *   - CCUP-SHOW-BLANK-SCREEN, CCUP-DISPLAY-CURRENT-RECORD,
 *     CCUP-CAPTURE-NEW-DATA, CCUP-GET-LAST-REFRESH, CCUP-COPY-NEW-DATA,
 *     CCUP-ENTER-KEY, CCUP-PF-KEY
 *
 * Key COBOL business rules preserved here:
 *   1. ACCTSID is PROT (Protected) — account_id CANNOT be changed — shown read-only
 *   2. CRDNAME alpha-only validation (INSPECT CONVERTING equivalent)
 *   3. Expiry month 1-12, year 1950-2099
 *   4. Optimistic locking via CCUP-OLD-DETAILS snapshot →
 *      replaced by updated_at timestamp (optimistic_lock_version)
 *   5. Status CRDSTCD Y/N dropdown
 *
 * DRK button pattern:
 *   - Save/Cancel only appear after successful data load
 *   - Matches COCRDUPC where action buttons are hidden on blank screen
 *
 * Note: expiration_day (EXPDAY hidden DRK PROT FSET BMS field) is preserved
 *       in state — sent back as-is so backend can reconstruct expiration_date.
 */

'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { getCard, updateCard, extractError } from '@/lib/api';
import type { CardDetailResponse } from '@/types';
import { MessageBar } from '@/components/ui/MessageBar';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

// ---------------------------------------------------------------------------
// Form state type
// ---------------------------------------------------------------------------

interface CardForm {
  card_embossed_name: string;
  active_status: 'Y' | 'N';
  expiration_month: string;  // string for input; parsed on submit
  expiration_year: string;   // string for input; parsed on submit
  expiration_day: number | null;  // hidden EXPDAY — preserved from GET, not shown
}

// ---------------------------------------------------------------------------
// Validation
// ---------------------------------------------------------------------------

function validateForm(form: CardForm): string[] {
  const errors: string[] = [];

  // CRDNAME: alpha-only (INSPECT CONVERTING equivalent from COCRDUPC)
  if (!form.card_embossed_name.trim()) {
    errors.push('Embossed name is required');
  } else if (!/^[A-Za-z\s]+$/.test(form.card_embossed_name)) {
    errors.push('Embossed name must contain only letters and spaces');
  } else if (form.card_embossed_name.trim().length > 50) {
    errors.push('Embossed name must be 50 characters or fewer');
  }

  // EXPMON: 1-12
  const month = parseInt(form.expiration_month, 10);
  if (!form.expiration_month || isNaN(month) || month < 1 || month > 12) {
    errors.push('Expiration month must be between 1 and 12');
  }

  // EXPYEAR: 1950-2099
  const year = parseInt(form.expiration_year, 10);
  if (!form.expiration_year || isNaN(year) || year < 1950 || year > 2099) {
    errors.push('Expiration year must be between 1950 and 2099');
  }

  return errors;
}

// ---------------------------------------------------------------------------
// Main content (needs useSearchParams → must be inside Suspense)
// ---------------------------------------------------------------------------

function CardUpdateContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const paramCardNumber = searchParams.get('cardNumber') || '';

  // Search state
  const [searchCardNumber, setSearchCardNumber] = useState(paramCardNumber);

  // Loaded card state
  const [card, setCard] = useState<CardDetailResponse | null>(null);

  // Form state — only editable fields (UNPROT fields on CCRDUPA map)
  const [form, setForm] = useState<CardForm>({
    card_embossed_name: '',
    active_status: 'Y',
    expiration_month: '',
    expiration_year: '',
    expiration_day: null,
  });

  // DRK button state — Save/Cancel hidden until data loaded (mirrors COCRDUPC blank screen)
  const [showSaveCancel, setShowSaveCancel] = useState(false);

  // UI state
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [successMessage, setSuccessMessage] = useState('');

  // Auto-load if card number in URL
  useEffect(() => {
    if (paramCardNumber) {
      setSearchCardNumber(paramCardNumber);
      loadCard(paramCardNumber);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paramCardNumber]);

  async function loadCard(num: string) {
    const trimmed = num.trim();
    if (!trimmed) {
      setError('Card number cannot be empty');
      return;
    }
    if (!/^\d{1,16}$/.test(trimmed)) {
      setError('Card number must be numeric (up to 16 digits)');
      return;
    }

    setLoading(true);
    setError('');
    setValidationErrors([]);
    setSuccessMessage('');
    setCard(null);
    setShowSaveCancel(false);

    try {
      const data = await getCard(trimmed);
      setCard(data);
      // Populate editable fields from loaded card
      setForm({
        card_embossed_name: data.card_embossed_name || '',
        active_status: (data.active_status as 'Y' | 'N') || 'Y',
        expiration_month: String(data.expiration_month || ''),
        expiration_year: String(data.expiration_year || ''),
        expiration_day: data.expiration_day,
      });
      setShowSaveCancel(true);
    } catch (err) {
      const apiErr = extractError(err);
      setError(apiErr.message);
    } finally {
      setLoading(false);
    }
  }

  function handleSearchSubmit(e: React.FormEvent) {
    e.preventDefault();
    loadCard(searchCardNumber);
  }

  function handleFieldChange(field: keyof CardForm, value: string | number | null) {
    setForm((prev) => ({ ...prev, [field]: value }));
    setValidationErrors([]);
    setSuccessMessage('');
  }

  async function handleSave() {
    if (!card) return;

    const errs = validateForm(form);
    if (errs.length > 0) {
      setValidationErrors(errs);
      return;
    }

    setSaving(true);
    setError('');
    setValidationErrors([]);
    setSuccessMessage('');

    try {
      const updated = await updateCard(card.card_number, {
        card_embossed_name: form.card_embossed_name.trim(),
        active_status: form.active_status,
        expiration_month: parseInt(form.expiration_month, 10),
        expiration_year: parseInt(form.expiration_year, 10),
        expiration_day: form.expiration_day ?? undefined,
        optimistic_lock_version: card.updated_at,
      });
      // Refresh card state with updated data (new updated_at for future saves)
      setCard(updated);
      setForm({
        card_embossed_name: updated.card_embossed_name || '',
        active_status: (updated.active_status as 'Y' | 'N') || 'Y',
        expiration_month: String(updated.expiration_month || ''),
        expiration_year: String(updated.expiration_year || ''),
        expiration_day: updated.expiration_day,
      });
      setSuccessMessage(`Card ${card.card_number} updated successfully.`);
    } catch (err) {
      const apiErr = extractError(err);
      // Map COBOL RESP codes to user messages
      if (apiErr.error_code === 'OPTIMISTIC_LOCK_ERROR' || apiErr.error_code === 'CONFLICT') {
        setError(
          'This card was modified by another process. Please reload to get the latest data.'
        );
      } else {
        setError(apiErr.message);
      }
    } finally {
      setSaving(false);
    }
  }

  function handleCancel() {
    if (card) {
      // Reset form to loaded values (discard changes)
      setForm({
        card_embossed_name: card.card_embossed_name || '',
        active_status: (card.active_status as 'Y' | 'N') || 'Y',
        expiration_month: String(card.expiration_month || ''),
        expiration_year: String(card.expiration_year || ''),
        expiration_day: card.expiration_day,
      });
      setValidationErrors([]);
      setError('');
      setSuccessMessage('');
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Page header */}
      <div className="bg-blue-900 text-white px-6 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-yellow-300">CardDemo</h1>
            <p className="text-sm text-blue-200">Credit Card Demo Application</p>
          </div>
          <div className="text-sm text-blue-200">
            <span className="font-medium text-white">COCRDUP</span> — Card Update
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-6 py-6">
        {/* Card number search */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">Update Credit Card</h2>
          <form onSubmit={handleSearchSubmit} className="flex gap-3 items-end">
            <div className="flex-1">
              <label htmlFor="searchCardNumber" className="block text-sm font-medium text-gray-700 mb-1">
                Card Number
                <span className="text-red-500 ml-1">*</span>
              </label>
              <input
                id="searchCardNumber"
                type="text"
                value={searchCardNumber}
                onChange={(e) => setSearchCardNumber(e.target.value)}
                maxLength={16}
                placeholder="16-digit card number"
                autoFocus={!paramCardNumber}
                disabled={loading}
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm
                           focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                           font-mono tracking-widest disabled:bg-gray-50"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 bg-blue-600 text-white rounded-md text-sm font-medium
                         hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Loading...' : 'Load Card'}
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

        {/* Error / validation / success messages */}
        {error && <MessageBar message={error} color="red" className="mb-4" />}
        {validationErrors.length > 0 && (
          <div className="mb-4 rounded-md bg-red-50 border border-red-200 p-4">
            <p className="text-sm font-medium text-red-800 mb-1">Please correct the following:</p>
            <ul className="list-disc list-inside text-sm text-red-700 space-y-1">
              {validationErrors.map((e, i) => (
                <li key={i}>{e}</li>
              ))}
            </ul>
          </div>
        )}
        {successMessage && (
          <MessageBar message={successMessage} color="green" className="mb-4" />
        )}

        {loading && (
          <div className="flex justify-center py-12">
            <LoadingSpinner />
          </div>
        )}

        {/* Edit form — only visible after card loaded */}
        {card && !loading && (
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-base font-semibold text-gray-900">
                Card Details
              </h3>
              <p className="text-xs text-gray-500 mt-0.5">
                Account ID is protected and cannot be modified (ACCTSID PROT).
              </p>
            </div>

            <div className="px-6 py-6 space-y-6">
              {/* ----------------------------------------------------------------
                  PROT fields — read-only (ASKIP on CCRDUPA BMS map)
                  ---------------------------------------------------------------- */}
              <div className="grid grid-cols-2 md:grid-cols-3 gap-x-6 gap-y-4">
                {/* CARDSID — PROT, read-only */}
                <div>
                  <p className="text-xs text-gray-500 uppercase tracking-wide">Card Number</p>
                  <p className="text-sm font-mono font-medium text-gray-900 mt-0.5">
                    {card.card_number}
                  </p>
                </div>
                {/* ACCTSID — PROT, account_id cannot change (COCRDUPC rule) */}
                <div>
                  <p className="text-xs text-gray-500 uppercase tracking-wide">
                    Account ID
                    <span className="ml-1 text-blue-600 text-xs font-normal">(protected)</span>
                  </p>
                  <p className="text-sm font-medium text-gray-900 mt-0.5">
                    {card.account_id}
                  </p>
                </div>
                {/* Customer ID — read-only */}
                <div>
                  <p className="text-xs text-gray-500 uppercase tracking-wide">Customer ID</p>
                  <p className="text-sm font-medium text-gray-900 mt-0.5">
                    {card.customer_id}
                  </p>
                </div>
              </div>

              <hr className="border-gray-100" />

              {/* ----------------------------------------------------------------
                  UNPROT editable fields from CCRDUPA BMS map
                  ---------------------------------------------------------------- */}
              <div className="space-y-5">
                {/* CRDNAME — alpha-only validated (INSPECT CONVERTING in COCRDUPC) */}
                <div>
                  <label htmlFor="embossedName" className="block text-sm font-medium text-gray-700 mb-1">
                    Embossed Name
                    <span className="text-red-500 ml-1">*</span>
                    <span className="text-xs text-gray-400 ml-2">(letters and spaces only)</span>
                  </label>
                  <input
                    id="embossedName"
                    type="text"
                    value={form.card_embossed_name}
                    onChange={(e) => handleFieldChange('card_embossed_name', e.target.value)}
                    maxLength={50}
                    disabled={saving}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm
                               focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                               uppercase disabled:bg-gray-50"
                  />
                </div>

                {/* CRDSTCD — Y/N status toggle */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Active Status
                    <span className="text-red-500 ml-1">*</span>
                  </label>
                  <div className="flex gap-4">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        name="activeStatus"
                        value="Y"
                        checked={form.active_status === 'Y'}
                        onChange={() => handleFieldChange('active_status', 'Y')}
                        disabled={saving}
                        className="text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-700">
                        Y — Active
                      </span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        name="activeStatus"
                        value="N"
                        checked={form.active_status === 'N'}
                        onChange={() => handleFieldChange('active_status', 'N')}
                        disabled={saving}
                        className="text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-700">
                        N — Inactive
                      </span>
                    </label>
                  </div>
                </div>

                {/* EXPMON + EXPYEAR — expiry date inputs */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="expiryMonth" className="block text-sm font-medium text-gray-700 mb-1">
                      Expiry Month (MM)
                      <span className="text-red-500 ml-1">*</span>
                    </label>
                    <input
                      id="expiryMonth"
                      type="number"
                      min={1}
                      max={12}
                      value={form.expiration_month}
                      onChange={(e) => handleFieldChange('expiration_month', e.target.value)}
                      disabled={saving}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm
                                 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                                 disabled:bg-gray-50"
                    />
                    <p className="text-xs text-gray-400 mt-1">1–12</p>
                  </div>
                  <div>
                    <label htmlFor="expiryYear" className="block text-sm font-medium text-gray-700 mb-1">
                      Expiry Year (YYYY)
                      <span className="text-red-500 ml-1">*</span>
                    </label>
                    <input
                      id="expiryYear"
                      type="number"
                      min={1950}
                      max={2099}
                      value={form.expiration_year}
                      onChange={(e) => handleFieldChange('expiration_year', e.target.value)}
                      disabled={saving}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm
                                 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                                 disabled:bg-gray-50"
                    />
                    <p className="text-xs text-gray-400 mt-1">1950–2099</p>
                  </div>
                </div>
              </div>
            </div>

            {/* DRK button row — only shown after card loaded (mirrors COCRDUPC CCUP-SHOW-BLANK behavior) */}
            {showSaveCancel && (
              <div className="px-6 py-4 bg-gray-50 rounded-b-lg border-t border-gray-200 flex items-center justify-between">
                <div className="text-xs text-gray-400">
                  Optimistic lock: {new Date(card.updated_at).toLocaleString()}
                </div>
                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={handleCancel}
                    disabled={saving}
                    className="px-5 py-2 bg-gray-100 text-gray-700 rounded-md text-sm font-medium
                               hover:bg-gray-200 border border-gray-300 disabled:opacity-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={handleSave}
                    disabled={saving}
                    className="px-6 py-2 bg-green-600 text-white rounded-md text-sm font-medium
                               hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {saving ? 'Saving...' : 'PF5 — Save'}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default function CardUpdatePage() {
  return (
    <Suspense
      fallback={
        <div className="flex justify-center items-center min-h-screen">
          <LoadingSpinner />
        </div>
      }
    >
      <CardUpdateContent />
    </Suspense>
  );
}
