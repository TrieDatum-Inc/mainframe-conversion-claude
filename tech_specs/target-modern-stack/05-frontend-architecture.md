# Frontend Architecture Specification
# CardDemo Mainframe Modernization

## Document Purpose

This document defines the complete Next.js 14 App Router project structure, component architecture, state management strategy, authentication provider, and API client layer for the CardDemo modernization. It complements the screen-level detail in `03-frontend-specification.md` with project-level architectural decisions.

---

## 1. Technology Stack

| Technology | Version | Purpose | COBOL/CICS Equivalent |
|------------|---------|---------|----------------------|
| Next.js | 14+ | React framework with App Router | CICS transaction routing |
| TypeScript | 5+ | Type safety | COBOL data definitions and PIC clauses |
| Tailwind CSS | 3+ | Utility-first styling | BMS color/attribute styling |
| React Hook Form | 7+ | Form state management | BMS FSET field retransmission |
| Zod | 3+ | Client-side validation | BMS VALIDN + program-level validation |
| SWR or TanStack Query | — | Server state / data fetching | CICS pseudo-conversational COMMAREA |
| Zustand | 4+ | Global client state (auth) | CARDDEMO-COMMAREA user context |
| next-auth or custom JWT | — | Auth token management | CICS user token |

---

## 2. Complete Directory Structure

```
front_end/
├── package.json
├── next.config.js
├── tsconfig.json
├── tailwind.config.ts
├── postcss.config.js
├── .env.local.example
├── README.md
│
├── public/
│   └── favicon.ico
│
└── src/
    ├── app/                           # Next.js App Router pages
    │   ├── layout.tsx                 # Root layout: AuthProvider + QueryProvider
    │   ├── page.tsx                   # Root redirect: → /login or /menu
    │   ├── login/
    │   │   └── page.tsx               # COSGN00 — Login screen
    │   ├── menu/
    │   │   └── page.tsx               # COMEN01 — Main menu (user)
    │   ├── accounts/
    │   │   ├── view/
    │   │   │   └── page.tsx           # COACTVW — Account view
    │   │   └── update/
    │   │       └── page.tsx           # COACTUP — Account update
    │   ├── cards/
    │   │   ├── list/
    │   │   │   └── page.tsx           # COCRDLI — Card list
    │   │   ├── view/
    │   │   │   └── page.tsx           # COCRDSL — Card view
    │   │   └── update/
    │   │       └── page.tsx           # COCRDUP — Card update
    │   ├── transactions/
    │   │   ├── list/
    │   │   │   └── page.tsx           # COTRN00 — Transaction list
    │   │   ├── view/
    │   │   │   └── page.tsx           # COTRN01 — Transaction view
    │   │   └── add/
    │   │       └── page.tsx           # COTRN02 — Transaction add
    │   ├── billing/
    │   │   └── payment/
    │   │       └── page.tsx           # COBIL00 — Bill payment
    │   ├── reports/
    │   │   └── transactions/
    │   │       └── page.tsx           # CORPT00 — Transaction reports
    │   ├── authorizations/
    │   │   ├── page.tsx               # COPAU00 — Authorization summary
    │   │   └── [authId]/
    │   │       └── page.tsx           # COPAU01 — Authorization detail
    │   └── admin/
    │       ├── menu/
    │       │   └── page.tsx           # COADM01 — Admin menu
    │       ├── users/
    │       │   ├── page.tsx           # COUSR00 — User list
    │       │   ├── new/
    │       │   │   └── page.tsx       # COUSR01 — Add user
    │       │   ├── update/
    │       │   │   └── page.tsx       # COUSR02 — Update user
    │       │   └── delete/
    │       │       └── page.tsx       # COUSR03 — Delete user
    │       └── transaction-types/
    │           ├── page.tsx           # COTRTLI — Transaction type list
    │           └── edit/
    │               └── page.tsx       # COTRTUP — Transaction type edit
    │
    ├── components/
    │   ├── layout/
    │   │   ├── AppHeader.tsx          # Standard BMS header (rows 1-2)
    │   │   ├── PageWrapper.tsx        # Full-page container with header + message bar
    │   │   └── ActionBar.tsx          # PF key button row (row 24 equivalent)
    │   │
    │   ├── ui/                        # Reusable primitive components
    │   │   ├── FormField.tsx          # Label + input + error — DFHMDF UNPROT
    │   │   ├── ReadOnlyField.tsx      # Label + value — DFHMDF ASKIP
    │   │   ├── PasswordField.tsx      # Masked input — DFHMDF DRK UNPROT
    │   │   ├── MessageBar.tsx         # ERRMSG row 23 (red/green/neutral)
    │   │   ├── InfoMessage.tsx        # INFOMSG centered informational message
    │   │   ├── DataTable.tsx          # BMS list rows with column headers
    │   │   ├── Pagination.tsx         # Page controls (PF7/PF8 equivalents)
    │   │   ├── StatusBadge.tsx        # Y/N A/D status indicators
    │   │   ├── CurrencyDisplay.tsx    # PICOUT '+ZZZ,ZZZ,ZZZ.99' formatter
    │   │   ├── ConfirmDialog.tsx      # Y/N confirmation pattern
    │   │   ├── LoadingSpinner.tsx     # Loading state indicator
    │   │   └── SectionDivider.tsx     # Visual separator (maps to BMS literal rows)
    │   │
    │   ├── forms/                     # Feature-specific form components
    │   │   ├── AccountViewForm.tsx    # Account search + display fields
    │   │   ├── AccountUpdateForm.tsx  # Full account + customer edit form
    │   │   ├── CardSearchForm.tsx     # Card list filters
    │   │   ├── CardDetailForm.tsx     # Card view/update fields
    │   │   ├── TransactionForm.tsx    # Transaction add form
    │   │   ├── UserForm.tsx           # Add/update user fields
    │   │   ├── UserDeleteForm.tsx     # Delete user lookup + confirm
    │   │   ├── BillPaymentForm.tsx    # Two-phase billing form
    │   │   ├── ReportRequestForm.tsx  # Report type + date range form
    │   │   └── TransactionTypeForm.tsx # Type code + description form
    │   │
    │   └── lists/                     # List/table components
    │       ├── UserList.tsx           # COUSR00 10-row user list
    │       ├── TransactionList.tsx    # COTRN00 10-row transaction list
    │       ├── CardList.tsx           # COCRDLI 7-row card list
    │       ├── AuthorizationList.tsx  # COPAU00 5-row authorization list
    │       └── TransactionTypeList.tsx # COTRTLI 7-row type list
    │
    ├── lib/
    │   ├── api.ts                     # Typed API client — all HTTP calls
    │   ├── api-types.ts               # TypeScript interfaces matching Pydantic schemas
    │   └── utils.ts                   # Formatting, date handling, currency
    │
    ├── hooks/
    │   ├── useAuth.ts                 # Auth state — replaces CARDDEMO-COMMAREA user fields
    │   ├── usePagination.ts           # Page state management — replaces COBOL page COMMAREA
    │   ├── useFormWithChanges.ts      # Dirty-field detection — replaces WS-USR-MODIFIED flag
    │   └── useApiError.ts             # API error → MessageBar state
    │
    ├── store/
    │   └── authStore.ts               # Zustand store for JWT + user context
    │
    ├── middleware.ts                  # Route protection — replaces CICS security
    │
    ├── types/
    │   └── index.ts                   # All TypeScript interfaces
    │
    └── styles/
        └── globals.css                # Global styles + Tailwind base
```

---

## 3. Configuration Files

### 3.1 Next.js Configuration

**File:** `next.config.js`

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  // API URL from environment — points to FastAPI backend
  env: {
    API_BASE_URL: process.env.API_BASE_URL || 'http://localhost:8000',
  },
  // Strict mode for development
  reactStrictMode: true,
};

module.exports = nextConfig;
```

### 3.2 TypeScript Configuration

**File:** `tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

### 3.3 Tailwind Configuration

**File:** `tailwind.config.ts`

```typescript
import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      // BMS color mapping
      colors: {
        bms: {
          blue: '#3b82f6',        // BLUE fields (labels, read-only)
          yellow: '#eab308',      // YELLOW (title lines)
          turquoise: '#06b6d4',   // TURQUOISE (field labels/prompts)
          green: '#22c55e',       // GREEN (input fields)
          red: '#ef4444',         // RED (error messages, DFHRED)
          neutral: '#6b7280',     // NEUTRAL (default text)
          pink: '#ec4899',        // PINK (authorization detail fields)
          success: '#16a34a',     // DFHGREEN (success messages)
        },
      },
      fontFamily: {
        // Monospace for fields that must align (list screens)
        mono: ['Courier New', 'Courier', 'monospace'],
      },
    },
  },
  plugins: [],
};

export default config;
```

### 3.4 Package Dependencies

**File:** `package.json` (dependencies section)

```json
{
  "dependencies": {
    "next": "^14.2.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "typescript": "^5.4.0",
    "@hookform/resolvers": "^3.3.0",
    "react-hook-form": "^7.51.0",
    "zod": "^3.22.0",
    "zustand": "^4.5.0",
    "swr": "^2.2.0",
    "jose": "^5.2.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.2.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "tailwindcss": "^3.4.0",
    "@testing-library/react": "^15.0.0",
    "@testing-library/user-event": "^14.5.0",
    "jest": "^29.7.0",
    "jest-environment-jsdom": "^29.7.0",
    "@jest/globals": "^29.7.0"
  }
}
```

---

## 4. Root Layout

**File:** `src/app/layout.tsx`

```typescript
import type { Metadata } from 'next';
import { AuthProvider } from '@/store/authStore';
import '@/styles/globals.css';

export const metadata: Metadata = {
  title: 'CardDemo — Credit Card Management',
  description: 'Modernized CardDemo mainframe application',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-gray-50 min-h-screen font-sans">
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
```

---

## 5. Authentication State Management

### 5.1 Auth Store

**File:** `src/store/authStore.tsx`

The Zustand store replaces the CARDDEMO-COMMAREA user context that is passed through every CICS program:

```
COBOL COMMAREA fields → Zustand store:
  CDEMO-USERID (X08)    → authStore.userId
  CDEMO-USRTYP (X01)   → authStore.userType ('A' or 'U')
  WS-TRANID (X04)      → (derived from route, not stored)
  CDEMO-FROM-PROGRAM   → (browser history via router.back())
  CDEMO-TO-PROGRAM     → (Next.js router.push())
```

```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  token: string | null;
  userId: string | null;
  userType: 'A' | 'U' | null;
  isAuthenticated: boolean;
  login: (token: string, userId: string, userType: 'A' | 'U') => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      userId: null,
      userType: null,
      isAuthenticated: false,
      login: (token, userId, userType) =>
        set({ token, userId, userType, isAuthenticated: true }),
      logout: () =>
        set({ token: null, userId: null, userType: null, isAuthenticated: false }),
    }),
    {
      name: 'carddemo-auth',
      // Store token in sessionStorage for security (session-scoped, like CICS)
      storage: typeof window !== 'undefined'
        ? { getItem: (k) => sessionStorage.getItem(k), setItem: (k, v) => sessionStorage.setItem(k, v), removeItem: (k) => sessionStorage.removeItem(k) }
        : undefined,
    }
  )
);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
```

### 5.2 Auth Hook

**File:** `src/hooks/useAuth.ts`

```typescript
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';

export function useAuth() {
  const { token, userId, userType, isAuthenticated, login, logout } = useAuthStore();
  const router = useRouter();

  const handleLogin = async (loginToken: string, loginUserId: string, loginUserType: 'A' | 'U') => {
    login(loginToken, loginUserId, loginUserType);
    // COADM01C routing: admin → admin menu; COMEN01C: user → main menu
    if (loginUserType === 'A') {
      router.push('/admin/menu');
    } else {
      router.push('/menu');
    }
  };

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  return { token, userId, userType, isAuthenticated, handleLogin, handleLogout };
}
```

---

## 6. Route Protection Middleware

**File:** `src/middleware.ts`

```typescript
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { joseJwtVerify } from 'jose';

const PUBLIC_ROUTES = ['/login'];
const ADMIN_ROUTES = ['/admin'];

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Allow public routes
  if (PUBLIC_ROUTES.some(route => pathname.startsWith(route))) {
    return NextResponse.next();
  }

  // Check for auth token (stored in sessionStorage via client; use cookie for SSR middleware)
  const token = request.cookies.get('carddemo-token')?.value;

  if (!token) {
    // No token → redirect to login (replaces CICS EIBCALEN=0 → XCTL COSGN00C)
    return NextResponse.redirect(new URL('/login', request.url));
  }

  try {
    const secret = new TextEncoder().encode(process.env.JWT_SECRET_KEY);
    const { payload } = await joseJwtVerify(token, secret);
    const userType = payload.user_type as string;

    // Admin route guard (replaces COBOL IF CDEMO-USRTYP NOT = 'A' THEN error)
    if (ADMIN_ROUTES.some(route => pathname.startsWith(route)) && userType !== 'A') {
      return NextResponse.redirect(new URL('/menu', request.url));
    }

    return NextResponse.next();
  } catch {
    // Invalid token → redirect to login
    return NextResponse.redirect(new URL('/login', request.url));
  }
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|api).*)'],
};
```

---

## 7. API Client Layer

**File:** `src/lib/api.ts`

The API client is the single interface between the React frontend and the FastAPI backend. All HTTP calls go through this module.

```typescript
import { useAuthStore } from '@/store/authStore';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';

class ApiError extends Error {
  constructor(
    public statusCode: number,
    public errorCode: string,
    message: string,
    public details: unknown[] = [],
  ) {
    super(message);
  }
}

async function fetchWithAuth<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = useAuthStore.getState().token;

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(
      response.status,
      body.error_code ?? 'UNKNOWN_ERROR',
      body.message ?? `HTTP ${response.status}`,
      body.details ?? [],
    );
  }

  if (response.status === 204) return undefined as T;
  return response.json();
}

// Typed API client — maps to FastAPI endpoint modules
export const api = {
  // Auth — COSGN00C
  auth: {
    login: (userId: string, password: string) =>
      fetchWithAuth<LoginResponse>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ user_id: userId, password }),
      }),
    logout: () => fetchWithAuth<void>('/auth/logout', { method: 'POST' }),
  },

  // Users — COUSR00C/01C/02C/03C
  users: {
    list: (params: { user_id?: string; page?: number; per_page?: number }) =>
      fetchWithAuth<UserListResponse>(`/users?${new URLSearchParams(params as Record<string, string>)}`),
    get: (userId: string) =>
      fetchWithAuth<UserResponse>(`/users/${userId}`),
    create: (data: UserCreateRequest) =>
      fetchWithAuth<UserResponse>('/users', { method: 'POST', body: JSON.stringify(data) }),
    update: (userId: string, data: UserUpdateRequest) =>
      fetchWithAuth<UserResponse>(`/users/${userId}`, { method: 'PUT', body: JSON.stringify(data) }),
    delete: (userId: string) =>
      fetchWithAuth<void>(`/users/${userId}`, { method: 'DELETE' }),
  },

  // Accounts — COACTVWC/COACTUPC
  accounts: {
    get: (accountId: string) =>
      fetchWithAuth<AccountViewResponse>(`/accounts/${accountId}`),
    update: (accountId: string, data: AccountUpdateRequest) =>
      fetchWithAuth<AccountViewResponse>(`/accounts/${accountId}`, {
        method: 'PUT', body: JSON.stringify(data),
      }),
  },

  // Credit cards — COCRDLIC/COCRDSLIC/COCRDUPD
  cards: {
    list: (params: CardListParams) =>
      fetchWithAuth<CardListResponse>(`/cards?${new URLSearchParams(params as Record<string, string>)}`),
    get: (cardNumber: string) =>
      fetchWithAuth<CardResponse>(`/cards/${cardNumber}`),
    update: (cardNumber: string, data: CardUpdateRequest) =>
      fetchWithAuth<CardResponse>(`/cards/${cardNumber}`, {
        method: 'PUT', body: JSON.stringify(data),
      }),
  },

  // Transactions — COTRN00C/01C/02C
  transactions: {
    list: (params: TransactionListParams) =>
      fetchWithAuth<TransactionListResponse>(`/transactions?${new URLSearchParams(params as Record<string, string>)}`),
    get: (transactionId: string) =>
      fetchWithAuth<TransactionResponse>(`/transactions/${transactionId}`),
    getLast: () =>
      fetchWithAuth<TransactionResponse>('/transactions/last'),
    create: (data: TransactionCreateRequest) =>
      fetchWithAuth<TransactionResponse>('/transactions', {
        method: 'POST', body: JSON.stringify(data),
      }),
  },

  // Transaction types — COTRTLIC/COTRTUPC
  transactionTypes: {
    list: (params: TransactionTypeListParams) =>
      fetchWithAuth<TransactionTypeListResponse>(`/transaction-types?${new URLSearchParams(params as Record<string, string>)}`),
    get: (typeCode: string) =>
      fetchWithAuth<TransactionTypeResponse>(`/transaction-types/${typeCode}`),
    create: (data: TransactionTypeCreateRequest) =>
      fetchWithAuth<TransactionTypeResponse>('/transaction-types', {
        method: 'POST', body: JSON.stringify(data),
      }),
    update: (typeCode: string, data: TransactionTypeUpdateRequest) =>
      fetchWithAuth<TransactionTypeResponse>(`/transaction-types/${typeCode}`, {
        method: 'PUT', body: JSON.stringify(data),
      }),
    delete: (typeCode: string) =>
      fetchWithAuth<void>(`/transaction-types/${typeCode}`, { method: 'DELETE' }),
  },

  // Authorizations — COPAUS0C/1C/2C
  authorizations: {
    list: (params: AuthorizationListParams) =>
      fetchWithAuth<AuthorizationListResponse>(`/authorizations?${new URLSearchParams(params as Record<string, string>)}`),
    get: (authId: string) =>
      fetchWithAuth<AuthorizationResponse>(`/authorizations/${authId}`),
    toggleFraud: (authId: string) =>
      fetchWithAuth<AuthorizationResponse>(`/authorizations/${authId}/fraud`, {
        method: 'PUT', body: JSON.stringify({ action: 'toggle' }),
      }),
  },

  // Billing — COBIL00C
  billing: {
    getBalance: (accountId: string) =>
      fetchWithAuth<BalanceResponse>(`/billing/${accountId}/balance`),
    processPayment: (accountId: string, data: PaymentRequest) =>
      fetchWithAuth<PaymentResponse>(`/billing/${accountId}/payment`, {
        method: 'POST', body: JSON.stringify(data),
      }),
  },

  // Reports — CORPT00C
  reports: {
    request: (data: ReportRequestCreate) =>
      fetchWithAuth<ReportResponse>('/reports/request', {
        method: 'POST', body: JSON.stringify(data),
      }),
  },

  // System — CSDAT01Y equivalent
  system: {
    getDateTime: () =>
      fetchWithAuth<SystemDateTimeResponse>('/system/date-time'),
  },
};

export { ApiError };
```

---

## 8. API Types

**File:** `src/lib/api-types.ts`

All TypeScript interfaces are derived from the Pydantic schemas in `02-api-specification.md`.

```typescript
// Auth
export interface LoginResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  user_type: 'A' | 'U';
  redirect_to: string;
}

// Pagination envelope — replaces COBOL page COMMAREA
export interface PaginatedResponse<T> {
  items: T[];
  total_count: number;
  page: number;
  per_page: number;
  total_pages: number;
}

// Users
export interface UserResponse {
  user_id: string;
  first_name: string;
  last_name: string;
  user_type: 'A' | 'U';
}

export interface UserCreateRequest {
  user_id: string;
  first_name: string;
  last_name: string;
  password: string;
  user_type: 'A' | 'U';
}

export interface UserUpdateRequest {
  first_name: string;
  last_name: string;
  password: string;
  user_type: 'A' | 'U';
}

export type UserListResponse = PaginatedResponse<UserResponse>;

// Accounts
export interface AccountViewResponse {
  account_id: string;
  account_status: 'Y' | 'N';
  opened_date: string;
  expiry_date: string;
  reissue_date: string;
  credit_limit: number;
  cash_credit_limit: number;
  current_balance: number;
  cycle_credit_amount: number;
  cycle_debit_amount: number;
  account_group: string;
  customer: CustomerDetailResponse;
}

export interface CustomerDetailResponse {
  customer_id: string;
  ssn_masked: string;
  date_of_birth: string;
  fico_score: number;
  first_name: string;
  middle_name: string;
  last_name: string;
  address_line_1: string;
  address_line_2: string;
  city: string;
  state: string;
  zip_code: string;
  country: string;
  phone_1: string;
  phone_2: string;
  government_id_ref: string;
  eft_account_id: string;
  primary_card_holder: 'Y' | 'N';
}

// Cards
export interface CardResponse {
  card_number: string;
  account_id: string;
  card_name: string;
  active_status: 'Y' | 'N';
  expiry_month: string;
  expiry_year: string;
  expiry_day: number;  // Hidden EXPDAY field — preserved in type
  optimistic_lock_version: string;
}

export interface CardUpdateRequest {
  card_name: string;
  active_status: 'Y' | 'N';
  expiry_month: string;
  expiry_year: string;
  expiry_day: number;
  optimistic_lock_version: string;
}

export type CardListResponse = PaginatedResponse<CardResponse>;

// Transactions
export interface TransactionResponse {
  transaction_id: string;
  card_number: string;
  transaction_type_code: string;
  category_code: string;
  source: string;
  description: string;
  amount: number;
  original_date: string;
  processing_date: string;
  merchant_id: string;
  merchant_name: string;
  merchant_city: string;
  merchant_zip: string;
}

export interface TransactionCreateRequest {
  account_id?: string;
  card_number?: string;
  transaction_type_code: string;
  category_code: string;
  source: string;
  description: string;
  amount: number;
  original_date: string;
  processing_date: string;
  merchant_id: string;
  merchant_name: string;
  merchant_city?: string;
  merchant_zip?: string;
}

export type TransactionListResponse = PaginatedResponse<TransactionResponse>;

// Transaction types
export interface TransactionTypeResponse {
  type_code: string;
  description: string;
}

export type TransactionTypeListResponse = PaginatedResponse<TransactionTypeResponse>;

// Authorizations
export interface AuthorizationResponse {
  auth_id: string;
  account_id: string;
  card_number: string;
  auth_date: string;
  auth_time: string;
  auth_response_code: string;
  auth_reason: string;
  auth_code: string;
  amount: number;
  pos_entry_mode: string;
  source: string;
  mcc_code: string;
  card_expiry: string;
  auth_type: string;
  transaction_id: string;
  match_status: 'P' | 'D' | 'E' | 'M';
  fraud_status: 'FRAUD' | 'REMOVED' | null;
  merchant_name: string;
  merchant_id: string;
  merchant_city: string;
  merchant_state: string;
  merchant_zip: string;
}

export type AuthorizationListResponse = PaginatedResponse<AuthorizationResponse>;

// Billing
export interface BalanceResponse {
  account_id: string;
  current_balance: number;
  formatted_balance: string;
}

export interface PaymentRequest {
  confirmed: 'Y' | 'N';
}

export interface PaymentResponse {
  account_id: string;
  payment_amount: number;
  new_balance: number;
  message: string;
}

// System
export interface SystemDateTimeResponse {
  date: string;
  time: string;
  formatted_date: string;
  formatted_time: string;
}

// List params
export interface CardListParams {
  account_id?: string;
  card_number?: string;
  page?: number;
  per_page?: number;
}

export interface TransactionListParams {
  transaction_id?: string;
  page?: number;
  per_page?: number;
}

export interface AuthorizationListParams {
  account_id?: string;
  page?: number;
  per_page?: number;
}

export interface TransactionTypeListParams {
  type_code?: string;
  description?: string;
  page?: number;
  per_page?: number;
}
```

---

## 9. Custom Hooks

### 9.1 Pagination Hook

**File:** `src/hooks/usePagination.ts`

```typescript
import { useState } from 'react';

interface PaginationState {
  page: number;
  perPage: number;
}

/**
 * Replaces COBOL pagination COMMAREA fields:
 * - CDEMO-PAGE-NUM
 * - CDEMO-NEXT-PAGE-FLG (WS-CA-FIRST-PAGE / WS-CA-LAST-PAGE)
 *
 * COBOL: PERFORM PROCESS-PAGE-FORWARD: MOVE WS-CA-CURSOR-CARD-NUM TO DFHBMEOF; STARTBR
 * Modern: page + 1 passed as query param; server returns total_pages
 */
export function usePagination(initialPerPage: number = 10) {
  const [state, setState] = useState<PaginationState>({ page: 1, perPage: initialPerPage });

  const goToNextPage = (totalPages: number) => {
    if (state.page < totalPages) {
      setState(prev => ({ ...prev, page: prev.page + 1 }));
    }
  };

  const goToPrevPage = () => {
    if (state.page > 1) {
      setState(prev => ({ ...prev, page: prev.page - 1 }));
    }
  };

  const resetPage = () => {
    setState(prev => ({ ...prev, page: 1 }));
  };

  return {
    page: state.page,
    perPage: state.perPage,
    goToNextPage,
    goToPrevPage,
    resetPage,
  };
}
```

### 9.2 Form With Changes Hook

**File:** `src/hooks/useFormWithChanges.ts`

```typescript
import { useRef } from 'react';

/**
 * Detects field-level changes — replaces COBOL WS-USR-MODIFIED / WS-DATACHANGED-FLAG patterns.
 *
 * COBOL (COUSR02C UPDATE-USER-INFO, lines 219-234):
 *   IF FNAMEI NOT = SEC-USR-FNAME: SET USR-MODIFIED-YES
 *   IF LNAMEI NOT = SEC-USR-LNAME: SET USR-MODIFIED-YES
 *   ...
 *   IF USR-MODIFIED-YES: PERFORM UPDATE-USER-SEC-FILE
 *   ELSE: 'Please modify to update...' in DFHRED
 *
 * Modern: compare current form values against snapshot from last successful GET.
 */
export function useFormWithChanges<T extends Record<string, unknown>>() {
  const originalValues = useRef<T | null>(null);

  const setOriginal = (values: T) => {
    originalValues.current = { ...values };
  };

  const hasChanges = (current: T): boolean => {
    if (!originalValues.current) return true;
    return Object.keys(current).some(
      key => current[key] !== originalValues.current![key]
    );
  };

  return { setOriginal, hasChanges };
}
```

### 9.3 API Error Hook

**File:** `src/hooks/useApiError.ts`

```typescript
import { useState, useCallback } from 'react';
import { ApiError } from '@/lib/api';

type MessageColor = 'red' | 'green' | 'neutral';

interface ErrorState {
  message: string;
  color: MessageColor;
}

/**
 * Manages ERRMSG bar state — maps COBOL WS-MESSAGE + ERRMSGC color attribute.
 *
 * COBOL pattern:
 *   MOVE 'error text' TO WS-MESSAGE
 *   SET ERR-FLG-ON
 *   MOVE DFHRED TO ERRMSGC
 *   PERFORM SEND-SCREEN
 *
 * Modern: setError() populates the MessageBar component.
 */
export function useApiError() {
  const [errorState, setErrorState] = useState<ErrorState | null>(null);

  const setError = useCallback((message: string, color: MessageColor = 'red') => {
    setErrorState({ message, color });
  }, []);

  const setSuccess = useCallback((message: string) => {
    setErrorState({ message, color: 'green' });
  }, []);

  const setInfo = useCallback((message: string) => {
    setErrorState({ message, color: 'neutral' });
  }, []);

  const clearError = useCallback(() => {
    setErrorState(null);
  }, []);

  const handleApiError = useCallback((error: unknown) => {
    if (error instanceof ApiError) {
      setError(error.message);
    } else {
      setError('An unexpected error occurred. Please try again.');
    }
  }, [setError]);

  return { errorState, setError, setSuccess, setInfo, clearError, handleApiError };
}
```

---

## 10. Core UI Components

### 10.1 PageWrapper

**File:** `src/components/layout/PageWrapper.tsx`

```typescript
import { AppHeader } from './AppHeader';
import { MessageBar } from '@/components/ui/MessageBar';

interface PageWrapperProps {
  programName: string;
  transactionId: string;
  title: string;
  children: React.ReactNode;
  message?: { text: string; color: 'red' | 'green' | 'neutral' } | null;
  actionBar?: React.ReactNode;
}

/**
 * Standard page container mapping to the BMS 24-row layout:
 * Rows 1-2: AppHeader
 * Rows 3-22: children (main content)
 * Row 23: MessageBar (ERRMSG)
 * Row 24: ActionBar (PF keys)
 */
export function PageWrapper({ programName, transactionId, title, children, message, actionBar }: PageWrapperProps) {
  return (
    <div className="min-h-screen flex flex-col">
      <AppHeader programName={programName} transactionId={transactionId} />
      <main className="flex-1 p-6">
        <h1 className="text-xl font-semibold text-gray-700 text-center mb-6">{title}</h1>
        {children}
      </main>
      {message && <MessageBar message={message.text} color={message.color} />}
      {actionBar && (
        <div className="border-t border-gray-200 p-3 bg-gray-50">
          {actionBar}
        </div>
      )}
    </div>
  );
}
```

### 10.2 ActionBar

**File:** `src/components/layout/ActionBar.tsx`

```typescript
interface ActionButton {
  label: string;        // e.g., "F3=Exit", "F5=Save"
  onClick: () => void;
  variant?: 'primary' | 'secondary' | 'danger';
  hidden?: boolean;     // Maps to DRK attribute — conditionally hidden
  disabled?: boolean;
}

interface ActionBarProps {
  buttons: ActionButton[];
}

/**
 * Row 24 PF key legend — maps BMS function key labels to buttons.
 *
 * DRK buttons (hidden=true): FKEY05/FKEY12/FKEYSC on COACTUP/COCRDUP are initially DRK.
 * When hidden=false, the button becomes visible (like changing attribute to NORM/BRT).
 */
export function ActionBar({ buttons }: ActionBarProps) {
  return (
    <div className="flex gap-2 flex-wrap">
      {buttons
        .filter(btn => !btn.hidden)
        .map((btn) => (
          <button
            key={btn.label}
            onClick={btn.onClick}
            disabled={btn.disabled}
            className={`px-3 py-1 text-sm font-medium rounded ${
              btn.variant === 'primary' ? 'bg-blue-600 text-white hover:bg-blue-700' :
              btn.variant === 'danger' ? 'bg-red-600 text-white hover:bg-red-700' :
              'bg-gray-200 text-gray-700 hover:bg-gray-300'
            } disabled:opacity-50`}
          >
            {btn.label}
          </button>
        ))}
    </div>
  );
}
```

### 10.3 MessageBar

**File:** `src/components/ui/MessageBar.tsx`

```typescript
interface MessageBarProps {
  message: string;
  color: 'red' | 'green' | 'neutral';
}

/**
 * ERRMSG field equivalent — row 23, ASKIP BRT FSET.
 * Color maps to BMS attribute bytes:
 *   red    → DFHRED
 *   green  → DFHGREEN
 *   neutral → DFHNEUTR
 */
export function MessageBar({ message, color }: MessageBarProps) {
  if (!message) return null;

  const colorClass = {
    red: 'bg-red-50 text-red-700 border-red-300',
    green: 'bg-green-50 text-green-700 border-green-300',
    neutral: 'bg-gray-50 text-gray-700 border-gray-300',
  }[color];

  return (
    <div className={`w-full px-4 py-2 border text-sm font-medium ${colorClass}`}>
      {message}
    </div>
  );
}
```

### 10.4 DataTable

**File:** `src/components/ui/DataTable.tsx`

```typescript
interface Column<T> {
  key: keyof T | string;
  header: string;
  render?: (row: T) => React.ReactNode;
  className?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  onRowAction?: (row: T, action: string) => void;
  emptyMessage?: string;
}

/**
 * BMS list rows — maps to COTRN00/COUSR00/COCRDLI repeating row groups.
 * Each BMS row with SELn + data fields → TableRow with action buttons.
 */
export function DataTable<T extends { [key: string]: unknown }>({
  columns, data, onRowAction, emptyMessage = 'No records found.',
}: DataTableProps<T>) {
  if (data.length === 0) {
    return <p className="text-center text-gray-500 py-8">{emptyMessage}</p>;
  }

  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b border-gray-300">
          {columns.map(col => (
            <th key={String(col.key)} className={`text-left py-2 px-2 text-gray-600 ${col.className ?? ''}`}>
              {col.header}
            </th>
          ))}
          {onRowAction && <th className="text-left py-2 px-2">Actions</th>}
        </tr>
      </thead>
      <tbody>
        {data.map((row, idx) => (
          <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
            {columns.map(col => (
              <td key={String(col.key)} className={`py-2 px-2 ${col.className ?? ''}`}>
                {col.render ? col.render(row) : String(row[col.key as keyof T] ?? '')}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

### 10.5 CurrencyDisplay

**File:** `src/components/ui/CurrencyDisplay.tsx`

```typescript
interface CurrencyDisplayProps {
  value: number;
  /** PICOUT='+ZZZ,ZZZ,ZZZ.99' — show explicit + for positive */
  showSign?: boolean;
}

/**
 * Maps COBOL PICOUT='+ZZZ,ZZZ,ZZZ.99' — signed, comma-formatted currency.
 * Positive: '+1,234,567.89'
 * Negative: '-1,234,567.89'
 */
export function CurrencyDisplay({ value, showSign = true }: CurrencyDisplayProps) {
  const formatted = new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Math.abs(value));

  const sign = value >= 0 ? (showSign ? '+' : '') : '-';
  const displayValue = `${sign}${formatted}`;

  return (
    <span className={value < 0 ? 'text-red-600' : 'text-gray-900'}>
      {displayValue}
    </span>
  );
}
```

---

## 11. Form Patterns

### 11.1 Split Date Fields Pattern

Applies to: Account Update (COACTUP OPNYEAR/OPNMON/OPNDAY), Date of Birth (DOBYEAR/DOBMON/DOBDAY), Start/End dates (CORPT00 SDTYYYY/SDTMM/SDTDD).

```typescript
// Component for split date entry — maps to BMS UNPROT split date fields
interface SplitDateInputProps {
  label: string;
  yearName: string;
  monthName: string;
  dayName: string;
  register: UseFormRegister<any>;
  errors: FieldErrors;
}

export function SplitDateInput({ label, yearName, monthName, dayName, register, errors }: SplitDateInputProps) {
  return (
    <div className="flex items-center gap-1">
      <label className="text-cyan-600 text-sm mr-2">{label}</label>
      <input {...register(yearName)} placeholder="YYYY" maxLength={4} className="w-16 border underline" />
      <span className="text-gray-400">-</span>
      <input {...register(monthName)} placeholder="MM" maxLength={2} className="w-10 border underline" />
      <span className="text-gray-400">-</span>
      <input {...register(dayName)} placeholder="DD" maxLength={2} className="w-10 border underline" />
    </div>
  );
}
```

### 11.2 Split SSN Pattern

Applies to: Account Update (COACTUP ACTSSN1/2/3).

```typescript
// Three-part SSN — maps to ACTSSN1(3)/ACTSSN2(2)/ACTSSN3(4)
export function SplitSsnInput({ register, errors }: { register: any, errors: any }) {
  return (
    <div className="flex items-center gap-1">
      <input {...register('ssn1')} maxLength={3} placeholder="XXX" className="w-12 border" type="password" />
      <span>-</span>
      <input {...register('ssn2')} maxLength={2} placeholder="XX" className="w-10 border" type="password" />
      <span>-</span>
      <input {...register('ssn3')} maxLength={4} placeholder="XXXX" className="w-14 border" type="password" />
    </div>
  );
}
```

### 11.3 Split Phone Pattern

Applies to: Account Update (COACTUP ACSPH1A/B/C, ACSPH2A/B/C).

```typescript
// Three-part phone — maps to ACSPHnA(3)/ACSPHnB(3)/ACSPHnC(4)
export function SplitPhoneInput({ label, prefix, register }: { label: string; prefix: string; register: any }) {
  return (
    <div className="flex items-center gap-1">
      <label className="text-cyan-600 text-sm mr-2">{label}</label>
      <span>(</span>
      <input {...register(`${prefix}A`)} maxLength={3} className="w-10 border text-center" />
      <span>)</span>
      <input {...register(`${prefix}B`)} maxLength={3} className="w-10 border text-center" />
      <span>-</span>
      <input {...register(`${prefix}C`)} maxLength={4} className="w-12 border text-center" />
    </div>
  );
}
```

---

## 12. Navigation Flow Implementation

### 12.1 Root Page Redirect

**File:** `src/app/page.tsx`

```typescript
import { redirect } from 'next/navigation';

export default function RootPage() {
  // Middleware handles auth check; this just redirects to login as default
  redirect('/login');
}
```

### 12.2 Pre-populated Navigation

When navigating from a list screen to a detail screen with a pre-selected record (maps to COBOL COMMAREA CDEMO-CU03-USR-SELECTED pattern), use URL query parameters:

```typescript
// From User List (COUSR00) → Delete User (COUSR03)
router.push(`/admin/users/delete?userId=${selectedUserId}`);

// From Card List (COCRDLI) → Card Update (COCRDUP)
router.push(`/cards/update?cardNumber=${selectedCardNumber}&accountId=${selectedAccountId}`);

// From Transaction List (COTRN00) → Transaction View (COTRN01)
router.push(`/transactions/view?transactionId=${selectedTransactionId}`);
```

---

## 13. Testing Strategy

### 13.1 Test Setup

**File:** `src/__tests__/setup.ts`

```typescript
import '@testing-library/jest-dom';

// Mock API client for all tests
jest.mock('@/lib/api', () => ({
  api: {
    auth: { login: jest.fn(), logout: jest.fn() },
    users: { list: jest.fn(), get: jest.fn(), create: jest.fn(), update: jest.fn(), delete: jest.fn() },
    // ... other mocks
  },
}));
```

### 13.2 Critical Test Cases

| BMS Behavior | Frontend Test |
|-------------|--------------|
| COSGN00 DRK password field hides input | `test('password field type is password')` |
| COUSR03 no password field on delete screen | `test('delete user form does not have password field')` |
| COACTUP FKEY05 initially DRK | `test('Save button hidden before account is loaded')` |
| COCRDUP EXPDAY preserved in submission | `test('expiry day included in update request even though hidden')` |
| COBIL00 two-phase: balance shown after lookup | `test('balance displayed after account ID submitted')` |
| COUSR02 no-change detection | `test('save with unchanged fields shows modify warning')` |
| COTRTLI 7-row max (8th row never active) | `test('transaction type list never shows more than 7 rows')` |
| CORPT00 custom dates required when custom selected | `test('custom date fields required when custom report type chosen')` |
| COPAU01 AUTHMTC and AUTHFRD in red | `test('match status and fraud status displayed in red')` |

### 13.3 Jest Configuration

**File:** `jest.config.ts`

```typescript
import type { Config } from 'jest';
import nextJest from 'next/jest.js';

const createJestConfig = nextJest({ dir: './' });

const config: Config = {
  coverageProvider: 'v8',
  testEnvironment: 'jsdom',
  setupFilesAfterFramework: ['<rootDir>/src/__tests__/setup.ts'],
};

export default createJestConfig(config);
```
