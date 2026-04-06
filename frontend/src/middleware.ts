/**
 * Next.js middleware for route protection.
 *
 * COBOL origin: Replaces the EIBCALEN=0 check at the top of every CICS program:
 *   IF EIBCALEN = 0: EXEC CICS XCTL PROGRAM('COSGN00C')
 *
 * In the COBOL system, EIBCALEN=0 indicates no COMMAREA was passed — meaning
 * the user reached the program without going through sign-on. This caused an
 * immediate redirect to the sign-on screen.
 *
 * In the modern system, the middleware checks for a valid JWT token in the
 * request cookies/headers. If absent, the user is redirected to /login.
 * If present, the user_type claim determines which routes are accessible.
 *
 * Route protection matrix (maps CICS security table):
 *   /login           → Public (no auth required)
 *   /menu/*          → Any authenticated user (user_type A or U)
 *   /accounts/*      → Any authenticated user
 *   /cards/*         → Any authenticated user
 *   /transactions/*  → Any authenticated user
 *   /billing/*       → Any authenticated user
 *   /reports/*       → Any authenticated user
 *   /authorizations/*→ Any authenticated user
 *   /admin/*         → Admin only (user_type = 'A')
 */

import { NextRequest, NextResponse } from 'next/server';

/** Routes that don't require authentication */
const PUBLIC_ROUTES = ['/login'];

/** Routes that require admin role */
const ADMIN_ROUTES = ['/admin'];

/**
 * Extract the JWT token from localStorage is not possible in middleware
 * (runs on the edge, no browser APIs). We check the Authorization cookie
 * or the custom auth cookie set by the app.
 *
 * The frontend stores the token in localStorage. For middleware-level
 * protection, we use a cookie that the frontend sets after login.
 * (localStorage is not accessible in middleware — this is a Next.js limitation)
 *
 * Simple implementation: check for auth cookie presence.
 * Full JWT validation is done by the FastAPI backend on every API call.
 */
function getTokenFromRequest(request: NextRequest): string | null {
  // Check for auth cookie (set by frontend after successful login)
  const authCookie = request.cookies.get('carddemo_auth_token');
  if (authCookie?.value) return authCookie.value;

  // Check Authorization header (for programmatic clients)
  const authHeader = request.headers.get('authorization');
  if (authHeader?.startsWith('Bearer ')) {
    return authHeader.slice(7);
  }

  return null;
}

/**
 * Decode JWT payload without verification (verification done by backend).
 * Only used here for routing decisions — not a security boundary.
 */
function decodeTokenPayload(token: string): { sub?: string; user_type?: string; exp?: number } | null {
  try {
    const [, payloadB64] = token.split('.');
    if (!payloadB64) return null;
    const padded = payloadB64 + '=='.slice((payloadB64.length % 4 === 0) ? 0 : 4 - (payloadB64.length % 4));
    const decoded = atob(padded);
    return JSON.parse(decoded);
  } catch {
    return null;
  }
}

export function middleware(request: NextRequest): NextResponse {
  const { pathname } = request.nextUrl;

  // Allow public routes without authentication
  if (PUBLIC_ROUTES.some((route) => pathname.startsWith(route))) {
    return NextResponse.next();
  }

  // Allow Next.js internals and static assets
  if (
    pathname.startsWith('/_next') ||
    pathname.startsWith('/api') ||
    pathname.includes('.') // Static files
  ) {
    return NextResponse.next();
  }

  // Get token — if missing, redirect to login
  const token = getTokenFromRequest(request);
  if (!token) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('from', pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Decode token for role-based routing
  const payload = decodeTokenPayload(token);
  if (!payload) {
    const loginUrl = new URL('/login', request.url);
    return NextResponse.redirect(loginUrl);
  }

  // Check token expiry
  if (payload.exp && payload.exp < Math.floor(Date.now() / 1000)) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('reason', 'session_expired');
    return NextResponse.redirect(loginUrl);
  }

  // Admin route protection — maps CDEMO-USRTYP-ADMIN check in CICS programs
  if (ADMIN_ROUTES.some((route) => pathname.startsWith(route))) {
    if (payload.user_type !== 'A') {
      // Non-admin trying to access admin route — redirect to their menu
      return NextResponse.redirect(new URL('/menu', request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization)
     * - favicon.ico
     */
    '/((?!_next/static|_next/image|favicon.ico).*)',
  ],
};
