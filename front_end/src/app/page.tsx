'use client';

/**
 * Root page — redirects to /authorizations for the authorization module.
 * In the full application this would route to /login or /menu.
 */

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function RootPage() {
  const router = useRouter();

  useEffect(() => {
    router.push('/authorizations');
  }, [router]);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <p className="text-gray-500">Loading CardDemo...</p>
    </div>
  );
}
