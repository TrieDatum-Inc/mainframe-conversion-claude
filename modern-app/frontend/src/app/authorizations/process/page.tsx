"use client";

/**
 * Authorization Processing Page
 *
 * Provides a form to submit new authorization requests.
 * Replaces the IMS+MQ COPAUA0C processing flow.
 *
 * Route: /authorizations/process
 */

import Link from "next/link";
import { AuthProcessForm } from "@/components/Authorizations/AuthProcessForm";

export default function ProcessAuthorizationPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-2xl mx-auto flex items-center justify-between">
          <div>
            <p className="text-xs text-gray-400 font-mono">CP00 / COPAUA0C</p>
            <h1 className="text-lg font-semibold text-gray-900">Authorization Engine</h1>
          </div>
          <Link
            href="/authorizations"
            className="text-sm text-blue-600 hover:text-blue-800 transition-colors"
          >
            &larr; View Authorizations
          </Link>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-6 py-6">
        <AuthProcessForm />
      </div>
    </div>
  );
}
