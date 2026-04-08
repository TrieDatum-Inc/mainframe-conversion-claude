/**
 * Root page — redirects to /login or /dashboard based on auth state.
 */
import { redirect } from 'next/navigation';

export default function RootPage() {
  // Server-side: always redirect to login; client-side auth check
  // happens in the layout/middleware
  redirect('/login');
}
