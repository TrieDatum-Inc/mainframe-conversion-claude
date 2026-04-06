/**
 * Next.js middleware — route protection.
 *
 * Replicates COSGN00C's EIBCALEN check:
 *   IF EIBCALEN = 0 → XCTL to COSGN00C
 *
 * In the web equivalent: if no token cookie is present, redirect to /login.
 * Note: JWTs are stored in localStorage (client-side only). Middleware cannot
 * read localStorage, so we use a lightweight session cookie set by the
 * AuthContext to signal authentication state to middleware.
 *
 * The cookie `carddemo_authed` is set to "1" on login and cleared on logout.
 * The actual JWT remains in localStorage (never in cookies for security).
 */

import { NextRequest, NextResponse } from "next/server";

const PUBLIC_PATHS = ["/login"];
const AUTH_COOKIE = "carddemo_authed";

export function middleware(request: NextRequest): NextResponse {
  const { pathname } = request.nextUrl;

  const isPublicPath = PUBLIC_PATHS.some(
    (path) => pathname === path || pathname.startsWith(`${path}/`)
  );

  const isAuthed = request.cookies.has(AUTH_COOKIE);

  if (!isPublicPath && !isAuthed) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("from", pathname);
    return NextResponse.redirect(loginUrl);
  }

  if (isPublicPath && isAuthed) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths EXCEPT:
     * - _next/static (static files)
     * - _next/image (image optimisation)
     * - favicon.ico
     * - public files
     * - api routes (proxied to backend)
     */
    "/((?!_next/static|_next/image|favicon.ico|public/|api/).*)",
  ],
};
