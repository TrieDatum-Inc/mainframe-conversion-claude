'use client'

import { useState } from 'react'
import { useForm, useFieldArray } from 'react-hook-form'
import { postTransactions } from '@/lib/api'
import { AlertBanner } from '@/components/ui/AlertBanner'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { formatCurrency, getReasonCodeLabel, todayISOString } from '@/lib/utils'
import type { TransactionPostingResponse } from '@/types'

interface TransactionFormFields {
  tran_id: string
  tran_type_cd: string
  tran_cat_cd: string
  tran_source: string
  tran_desc: string
  tran_amt: string
  tran_merchant_id: string
  tran_merchant_name: string
  tran_merchant_city: string
  tran_merchant_zip: string
  tran_card_num: string
  tran_orig_ts: string
}

interface FormValues {
  transactions: TransactionFormFields[]
}

const DEFAULT_TRANSACTION: TransactionFormFields = {
  tran_id: '',
  tran_type_cd: '01',
  tran_cat_cd: '0001',
  tran_source: 'POS',
  tran_desc: '',
  tran_amt: '-0.00',
  tran_merchant_id: '',
  tran_merchant_name: '',
  tran_merchant_city: '',
  tran_merchant_zip: '',
  tran_card_num: '',
  tran_orig_ts: todayISOString() + 'T12:00:00Z',
}

/**
 * Transaction Posting Form — CBTRN02C UI equivalent.
 *
 * Maps DALYTRAN input fields to a web form.
 * Validation mirrors CBTRN02C 1500-VALIDATE-TRAN field rules.
 */
export function TransactionPostingForm() {
  const [result, setResult] = useState<TransactionPostingResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const { register, control, handleSubmit, formState: { errors } } = useForm<FormValues>({
    defaultValues: { transactions: [{ ...DEFAULT_TRANSACTION }] },
  })

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'transactions',
  })

  async function onSubmit(data: FormValues) {
    setError(null)
    setResult(null)
    setIsLoading(true)
    try {
      const response = await postTransactions({
        transactions: data.transactions.map(t => ({
          ...t,
          tran_amt: parseFloat(t.tran_amt),
        })),
      })
      setResult(response)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unexpected error')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="card p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-1">
          Daily Transaction Posting
        </h2>
        <p className="text-sm text-gray-500 mb-6">
          CBTRN02C — Validates and posts daily transactions. Invalid transactions are
          written to the reject file with reason codes.
        </p>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {fields.map((field, index) => (
            <div key={field.id} className="border border-gray-200 rounded-lg p-4 space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-sm font-medium text-gray-700">
                  Transaction {index + 1}
                </h3>
                {fields.length > 1 && (
                  <button
                    type="button"
                    onClick={() => remove(index)}
                    className="text-xs text-red-600 hover:text-red-700"
                    aria-label={`Remove transaction ${index + 1}`}
                  >
                    Remove
                  </button>
                )}
              </div>

              {/* Row 1: ID, Card, Amount */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="form-label" htmlFor={`tran_id_${index}`}>
                    Transaction ID <span className="text-red-500">*</span>
                  </label>
                  <input
                    id={`tran_id_${index}`}
                    className="form-input"
                    placeholder="TXN0000000000001"
                    aria-describedby={errors.transactions?.[index]?.tran_id ? `tran_id_err_${index}` : undefined}
                    {...register(`transactions.${index}.tran_id`, {
                      required: 'Transaction ID is required',
                      maxLength: { value: 16, message: 'Max 16 characters' },
                    })}
                  />
                  {errors.transactions?.[index]?.tran_id && (
                    <p id={`tran_id_err_${index}`} className="form-error">
                      {errors.transactions[index]?.tran_id?.message}
                    </p>
                  )}
                </div>

                <div>
                  <label className="form-label" htmlFor={`card_${index}`}>
                    Card Number <span className="text-red-500">*</span>
                  </label>
                  <input
                    id={`card_${index}`}
                    className="form-input font-mono"
                    placeholder="4111111111111111"
                    maxLength={16}
                    inputMode="numeric"
                    {...register(`transactions.${index}.tran_card_num`, {
                      required: 'Card number is required',
                      pattern: { value: /^\d{16}$/, message: '16 numeric digits required' },
                    })}
                  />
                  {errors.transactions?.[index]?.tran_card_num && (
                    <p className="form-error">
                      {errors.transactions[index]?.tran_card_num?.message}
                    </p>
                  )}
                </div>

                <div>
                  <label className="form-label" htmlFor={`amt_${index}`}>
                    Amount <span className="text-red-500">*</span>
                  </label>
                  <input
                    id={`amt_${index}`}
                    type="number"
                    step="0.01"
                    className="form-input"
                    placeholder="-50.00"
                    {...register(`transactions.${index}.tran_amt`, {
                      required: 'Amount is required',
                    })}
                  />
                  <p className="text-xs text-gray-400 mt-0.5">Negative = debit, Positive = credit</p>
                </div>
              </div>

              {/* Row 2: Type, Category, Source */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="form-label" htmlFor={`type_${index}`}>
                    Type Code <span className="text-red-500">*</span>
                  </label>
                  <select
                    id={`type_${index}`}
                    className="form-input"
                    {...register(`transactions.${index}.tran_type_cd`, { required: true })}
                  >
                    <option value="01">01 - Purchase</option>
                    <option value="02">02 - Refund</option>
                    <option value="03">03 - Cash Advance</option>
                    <option value="07">07 - Payment</option>
                  </select>
                </div>

                <div>
                  <label className="form-label" htmlFor={`cat_${index}`}>
                    Category Code <span className="text-red-500">*</span>
                  </label>
                  <select
                    id={`cat_${index}`}
                    className="form-input"
                    {...register(`transactions.${index}.tran_cat_cd`, { required: true })}
                  >
                    <option value="0001">0001 - Groceries</option>
                    <option value="0002">0002 - Restaurants</option>
                    <option value="0003">0003 - Gas</option>
                    <option value="0004">0004 - Travel</option>
                    <option value="0006">0006 - Entertainment</option>
                    <option value="0007">0007 - Healthcare</option>
                    <option value="0008">0008 - Online Shopping</option>
                  </select>
                </div>

                <div>
                  <label className="form-label" htmlFor={`src_${index}`}>
                    Source
                  </label>
                  <select
                    id={`src_${index}`}
                    className="form-input"
                    {...register(`transactions.${index}.tran_source`)}
                  >
                    <option value="POS">POS</option>
                    <option value="WEB">WEB</option>
                    <option value="MOBILE">MOBILE</option>
                    <option value="ATM">ATM</option>
                  </select>
                </div>
              </div>

              {/* Row 3: Description, Merchant */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="form-label" htmlFor={`desc_${index}`}>
                    Description <span className="text-red-500">*</span>
                  </label>
                  <input
                    id={`desc_${index}`}
                    className="form-input"
                    placeholder="Purchase description"
                    maxLength={100}
                    {...register(`transactions.${index}.tran_desc`, {
                      required: 'Description is required',
                    })}
                  />
                </div>

                <div>
                  <label className="form-label" htmlFor={`merchant_${index}`}>
                    Merchant Name
                  </label>
                  <input
                    id={`merchant_${index}`}
                    className="form-input"
                    placeholder="Merchant name"
                    maxLength={50}
                    {...register(`transactions.${index}.tran_merchant_name`)}
                  />
                </div>
              </div>

              {/* Row 4: Origination timestamp */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="form-label" htmlFor={`ts_${index}`}>
                    Origination Timestamp <span className="text-red-500">*</span>
                  </label>
                  <input
                    id={`ts_${index}`}
                    type="datetime-local"
                    className="form-input"
                    {...register(`transactions.${index}.tran_orig_ts`, {
                      required: 'Origination time is required',
                    })}
                  />
                </div>
              </div>
            </div>
          ))}

          {/* Add another transaction */}
          <button
            type="button"
            onClick={() => append({ ...DEFAULT_TRANSACTION })}
            className="btn-secondary w-full"
          >
            + Add Another Transaction
          </button>

          {/* Submit */}
          <button
            type="submit"
            className="btn-primary w-full"
            disabled={isLoading}
            aria-label="Post transactions"
          >
            {isLoading ? 'Posting...' : `Post ${fields.length} Transaction${fields.length !== 1 ? 's' : ''}`}
          </button>
        </form>
      </div>

      {/* Loading state */}
      {isLoading && <LoadingSpinner message="Posting transactions to TRANSACT file..." />}

      {/* Error */}
      {error && <AlertBanner type="error" title="Posting Failed" message={error} />}

      {/* Result */}
      {result && (
        <div className="card p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-gray-900">Posting Result</h3>
            <StatusBadge status={result.status} />
          </div>

          <div className="grid grid-cols-3 gap-4 text-center">
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-2xl font-bold text-gray-900">{result.transactions_processed}</p>
              <p className="text-xs text-gray-500">Processed</p>
            </div>
            <div className="bg-green-50 rounded-lg p-3">
              <p className="text-2xl font-bold text-green-700">{result.transactions_posted}</p>
              <p className="text-xs text-gray-500">Posted</p>
            </div>
            <div className={`rounded-lg p-3 ${result.has_rejects ? 'bg-red-50' : 'bg-gray-50'}`}>
              <p className={`text-2xl font-bold ${result.has_rejects ? 'text-red-700' : 'text-gray-700'}`}>
                {result.transactions_rejected}
              </p>
              <p className="text-xs text-gray-500">Rejected</p>
            </div>
          </div>

          {/* COBOL return code equivalent notice */}
          {result.has_rejects && (
            <AlertBanner
              type="warning"
              title="Rejects Occurred (Return Code 4)"
              message="Some transactions failed validation. Review the reject details below."
            />
          )}

          {/* Reject details */}
          {result.rejects.length > 0 && (
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Rejected Transactions</h4>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-gray-50 text-left text-xs text-gray-600">
                      <th className="p-2 font-medium">Transaction ID</th>
                      <th className="p-2 font-medium">Card Number</th>
                      <th className="p-2 font-medium">Reason Code</th>
                      <th className="p-2 font-medium">Reason</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.rejects.map((r) => (
                      <tr key={r.tran_id} className="border-t border-gray-100">
                        <td className="p-2 font-mono text-xs">{r.tran_id}</td>
                        <td className="p-2 font-mono text-xs">{r.card_num}</td>
                        <td className="p-2">
                          <span className="badge text-red-700 bg-red-50 border-red-200">
                            {r.reason_code}
                          </span>
                        </td>
                        <td className="p-2">{getReasonCodeLabel(r.reason_code)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          <p className="text-sm text-gray-500">{result.message}</p>
        </div>
      )}
    </div>
  )
}
