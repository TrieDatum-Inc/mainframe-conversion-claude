/**
 * Transaction types list — derived from COTRTLIC (CICS transaction CTLI).
 * BMS map: COTRTLI
 *
 * Admin only. Keyset pagination (7 rows per screen per COTRTLIC).
 * Supports type_cd and desc_filter search.
 */
'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { AppShell } from '@/components/layout/AppShell';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/FormField';
import { Alert } from '@/components/ui/Alert';
import { Pagination } from '@/components/ui/Pagination';
import { transactionTypeService } from '@/services/transactionTypeService';
import { usePagination } from '@/hooks/usePagination';
import { extractErrorMessage } from '@/services/apiClient';
import { ROUTES } from '@/lib/constants/routes';
import type { TransactionTypeListResponse } from '@/lib/types/api';

export default function TransactionTypesPage() {
  const { cursor, direction, page, goNext, goPrev, reset } = usePagination();
  const [data, setData] = useState<TransactionTypeListResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [typeCdFilter, setTypeCdFilter] = useState('');
  const [descFilter, setDescFilter] = useState('');
  const [deletingCode, setDeletingCode] = useState<string | null>(null);

  const fetchTypes = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await transactionTypeService.listTransactionTypes({
        cursor,
        direction,
        limit: 7,
        type_cd: typeCdFilter || undefined,
        desc_filter: descFilter || undefined,
      });
      setData(result);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  }, [cursor, direction, typeCdFilter, descFilter]);

  useEffect(() => {
    fetchTypes();
  }, [fetchTypes]);

  const handleDelete = async (typeCd: string) => {
    if (!confirm(`Delete transaction type "${typeCd}"?`)) return;
    setDeletingCode(typeCd);
    setDeleteError(null);
    try {
      await transactionTypeService.deleteTransactionType(typeCd);
      await fetchTypes();
    } catch (err) {
      setDeleteError(extractErrorMessage(err));
    } finally {
      setDeletingCode(null);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    reset();
  };

  return (
    <AppShell>
      <div className="max-w-3xl mx-auto">
        <div className="page-header">
          <div>
            <h1 className="page-title">Transaction Types</h1>
            <p className="page-subtitle">COTRTLIC — Admin Only</p>
          </div>
          <Link href={`${ROUTES.ADMIN_TRANSACTION_TYPES}/new`}>
            <Button variant="primary" size="sm">+ Add Type</Button>
          </Link>
        </div>

        {error && <Alert variant="error" className="mb-4">{error}</Alert>}
        {deleteError && <Alert variant="error" className="mb-4">{deleteError}</Alert>}

        {/* Filter bar */}
        <form onSubmit={handleSearch} className="flex gap-3 mb-4">
          <Input
            type="text"
            placeholder="Type code (e.g. 01)"
            maxLength={2}
            value={typeCdFilter}
            onChange={(e) => setTypeCdFilter(e.target.value)}
            className="w-32"
          />
          <Input
            type="text"
            placeholder="Description filter"
            value={descFilter}
            onChange={(e) => setDescFilter(e.target.value)}
            className="flex-1"
          />
          <Button type="submit" variant="secondary" size="md">Search</Button>
        </form>

        <div className="card">
          {isLoading ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin h-6 w-6 rounded-full border-4 border-blue-600 border-t-transparent" />
            </div>
          ) : data?.items.length === 0 ? (
            <p className="text-center text-gray-500 py-8">No transaction types found.</p>
          ) : (
            <>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Code</th>
                    <th>Description</th>
                    <th className="sr-only">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {data?.items.map((type) => (
                    <tr key={type.type_cd} className="hover:bg-gray-50">
                      <td className="font-mono font-semibold">{type.type_cd}</td>
                      <td>{type.description}</td>
                      <td className="text-right">
                        <div className="flex gap-1 justify-end">
                          <Link href={ROUTES.ADMIN_TRANSACTION_TYPE_EDIT(type.type_cd)}>
                            <Button variant="ghost" size="sm">Edit</Button>
                          </Link>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-red-600 hover:bg-red-50"
                            isLoading={deletingCode === type.type_cd}
                            onClick={() => handleDelete(type.type_cd)}
                          >
                            Delete
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <Pagination
                page={page}
                hasNext={!!data?.next_cursor}
                hasPrev={!!data?.prev_cursor}
                onNext={() => goNext(data?.next_cursor)}
                onPrev={() => goPrev(data?.prev_cursor)}
                total={data?.total}
              />
            </>
          )}
        </div>
      </div>
    </AppShell>
  );
}
