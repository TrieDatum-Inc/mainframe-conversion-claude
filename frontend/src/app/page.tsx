/**
 * Root page — redirects to /login or appropriate menu based on auth state.
 *
 * COBOL origin: In CICS, the application entry point was the COSG transaction
 * which always started at COSGN00C. Here, the root URL either sends
 * unauthenticated users to /login or authenticated users to their menu.
 *
 * This is a Server Component — auth check is done client-side via redirect.
 */

import { redirect } from 'next/navigation';

export default function RootPage() {
  // Always redirect to /login; middleware handles auth-based routing
  // If the user is authenticated, the login page will redirect them to /menu
  redirect('/login');
}
