import { redirect } from 'next/navigation';

/**
 * Root page — redirect to dashboard.
 * Auth guard in dashboard layout handles unauthenticated redirects to /login.
 */
export default function RootPage() {
  redirect('/dashboard');
}
