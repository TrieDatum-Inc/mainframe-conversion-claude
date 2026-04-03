'use client'

import { useState } from 'react'
import { exportData, importData } from '@/lib/api'
import { AlertBanner } from '@/components/ui/AlertBanner'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { formatDateTime } from '@/lib/utils'
import type { ExportResponse, ImportResponse, ExportPayload } from '@/types'

/**
 * Export/Import Panel — CBEXPORT and CBIMPORT UI equivalents.
 *
 * CBEXPORT: Reads all 5 entity tables, exports as JSON.
 * CBIMPORT: Imports JSON payload with validation (3000-VALIDATE-IMPORT implemented).
 * Processing order preserved: C -> A -> X -> T -> D.
 */
export function ExportImportPanel() {
  const [exportResult, setExportResult] = useState<ExportResponse | null>(null)
  const [importResult, setImportResult] = useState<ImportResponse | null>(null)
  const [importError, setImportError] = useState<string | null>(null)
  const [exportError, setExportError] = useState<string | null>(null)
  const [isExporting, setIsExporting] = useState(false)
  const [isImporting, setIsImporting] = useState(false)

  // --------------------------------------------------------
  // Export
  // --------------------------------------------------------

  async function handleExport() {
    setExportError(null)
    setExportResult(null)
    setIsExporting(true)
    try {
      const response = await exportData()
      setExportResult(response)
    } catch (e) {
      setExportError(e instanceof Error ? e.message : 'Export failed')
    } finally {
      setIsExporting(false)
    }
  }

  function handleDownloadExport() {
    if (!exportResult) return
    const blob = new Blob([JSON.stringify(exportResult.payload, null, 2)], {
      type: 'application/json',
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `carddemo_export_${new Date().toISOString().split('T')[0]}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  // --------------------------------------------------------
  // Import
  // --------------------------------------------------------

  async function handleImportFromExport() {
    if (!exportResult) return
    setImportError(null)
    setImportResult(null)
    setIsImporting(true)
    try {
      const response = await importData({ payload: exportResult.payload })
      setImportResult(response)
    } catch (e) {
      setImportError(e instanceof Error ? e.message : 'Import failed')
    } finally {
      setIsImporting(false)
    }
  }

  async function handleImportFromFile(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (!file) return

    setImportError(null)
    setImportResult(null)
    setIsImporting(true)
    try {
      const text = await file.text()
      const payload: ExportPayload = JSON.parse(text)
      const response = await importData({ payload })
      setImportResult(response)
    } catch (e) {
      setImportError(e instanceof Error ? e.message : 'Import failed — invalid JSON payload')
    } finally {
      setIsImporting(false)
      event.target.value = ''
    }
  }

  return (
    <div className="space-y-6">
      {/* CBEXPORT Section */}
      <div className="card p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-1">
          Data Export (CBEXPORT)
        </h2>
        <p className="text-sm text-gray-500 mb-4">
          Reads all 5 entity tables sequentially in order: Customers → Accounts →
          XRefs → Transactions → Cards. Branch ID and Region Code are hardcoded per spec.
        </p>

        <div className="flex flex-wrap gap-3">
          <button
            onClick={handleExport}
            disabled={isExporting}
            className="btn-primary"
            aria-label="Run CBEXPORT data export"
          >
            {isExporting ? 'Exporting...' : 'Run Export'}
          </button>
          {exportResult && (
            <button
              onClick={handleDownloadExport}
              className="btn-secondary"
              aria-label="Download export JSON file"
            >
              Download JSON
            </button>
          )}
        </div>
      </div>

      {isExporting && <LoadingSpinner message="Exporting all entity data..." />}
      {exportError && <AlertBanner type="error" title="Export Failed" message={exportError} />}

      {exportResult && (
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900">Export Result</h3>
            <StatusBadge status={exportResult.status} />
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 text-center mb-4">
            {[
              { label: 'Customers (C)', value: exportResult.customers_exported },
              { label: 'Accounts (A)', value: exportResult.accounts_exported },
              { label: 'XRefs (X)', value: exportResult.xrefs_exported },
              { label: 'Transactions (T)', value: exportResult.transactions_exported },
              { label: 'Cards (D)', value: exportResult.cards_exported },
              { label: 'Total', value: exportResult.total_records_exported, bold: true },
            ].map(({ label, value, bold }) => (
              <div key={label} className={`rounded-lg p-3 ${bold ? 'bg-blue-50' : 'bg-gray-50'}`}>
                <p className={`text-xl font-bold ${bold ? 'text-blue-700' : 'text-gray-900'}`}>
                  {value}
                </p>
                <p className="text-xs text-gray-500">{label}</p>
              </div>
            ))}
          </div>

          <div className="text-xs text-gray-500 space-y-1">
            <p>Timestamp: {exportResult.payload.export_timestamp}</p>
            <p>Branch: {exportResult.payload.branch_id} / Region: {exportResult.payload.region_code}</p>
          </div>
        </div>
      )}

      {/* CBIMPORT Section */}
      <div className="card p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-1">
          Data Import (CBIMPORT)
        </h2>
        <p className="text-sm text-gray-500 mb-4">
          Routes records by type code (C/A/X/T/D) to appropriate tables.
          Validation implemented from the 3000-VALIDATE-IMPORT stub: referential integrity,
          required fields, status value validation.
        </p>

        <div className="flex flex-wrap gap-3">
          {exportResult && (
            <button
              onClick={handleImportFromExport}
              disabled={isImporting}
              className="btn-primary"
              aria-label="Import from current export result"
            >
              {isImporting ? 'Importing...' : 'Import from Export Result'}
            </button>
          )}

          <label className="btn-secondary cursor-pointer" aria-label="Import from JSON file">
            Import from JSON File
            <input
              type="file"
              accept=".json"
              className="sr-only"
              onChange={handleImportFromFile}
              disabled={isImporting}
            />
          </label>
        </div>
      </div>

      {isImporting && <LoadingSpinner message="Importing and validating data..." />}
      {importError && <AlertBanner type="error" title="Import Failed" message={importError} />}

      {importResult && (
        <div className="card p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-gray-900">Import Result</h3>
            <StatusBadge status={importResult.status} />
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 text-center">
            {[
              { label: 'Customers', value: importResult.customers_imported },
              { label: 'Accounts', value: importResult.accounts_imported },
              { label: 'XRefs', value: importResult.xrefs_imported },
              { label: 'Transactions', value: importResult.transactions_imported },
              { label: 'Cards', value: importResult.cards_imported },
              {
                label: 'Errors',
                value: importResult.error_count,
                warning: importResult.error_count > 0,
              },
            ].map(({ label, value, warning }) => (
              <div
                key={label}
                className={`rounded-lg p-3 ${warning && value > 0 ? 'bg-red-50' : 'bg-gray-50'}`}
              >
                <p className={`text-xl font-bold ${warning && value > 0 ? 'text-red-700' : 'text-gray-900'}`}>
                  {value}
                </p>
                <p className="text-xs text-gray-500">{label}</p>
              </div>
            ))}
          </div>

          {/* Validation errors from 3000-VALIDATE-IMPORT */}
          {importResult.validation_errors.length > 0 && (
            <div>
              <h4 className="font-medium text-red-700 mb-2">
                Validation Errors ({importResult.validation_errors.length})
              </h4>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="bg-red-50 text-left text-red-700">
                      <th className="p-2 font-medium">Record Type</th>
                      <th className="p-2 font-medium">Record ID</th>
                      <th className="p-2 font-medium">Field</th>
                      <th className="p-2 font-medium">Error</th>
                    </tr>
                  </thead>
                  <tbody>
                    {importResult.validation_errors.map((err, i) => (
                      <tr key={i} className="border-t border-red-100">
                        <td className="p-2">
                          <span className="badge text-red-700 bg-red-50 border-red-200">
                            {err.record_type}
                          </span>
                        </td>
                        <td className="p-2 font-mono">{err.record_id}</td>
                        <td className="p-2">{err.field}</td>
                        <td className="p-2">{err.error}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          <p className="text-sm text-gray-500">{importResult.message}</p>
        </div>
      )}
    </div>
  )
}
