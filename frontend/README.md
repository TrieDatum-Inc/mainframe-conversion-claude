# CardDemo Frontend — Next.js

Next.js 14 web application replacing 21 BMS 3270 terminal screens from the CardDemo CICS application.

## BMS Screens Replaced

| BMS Mapset | Map | Route | Status |
|------------|-----|-------|--------|
| COSGN00 | COSGN0A | /login | Implemented |
| COMEN01 | COMEN1A | /menu | Stub (auth flow working) |
| COADM01 | COADM1A | /admin/menu | Stub (auth flow working) |
| All others | — | various | Future modules |

## Quick Start

```bash
cd frontend/
# Copy environment file
cp .env.local.example .env.local

# Install dependencies
npm install

# Start development server (requires backend running on :8000)
npm run dev
```

Visit http://localhost:3000

## Test Credentials

| User ID | Password | Type | Destination |
|---------|----------|------|-------------|
| ADMIN001 | Admin1234 | Admin | /admin/menu |
| USER0001 | User1234 | Regular | /menu |

## Architecture

```
src/
├── app/                    # Next.js App Router pages
│   ├── layout.tsx          # Root layout
│   ├── page.tsx            # Root → redirects to /login
│   ├── login/page.tsx      # COSGN00 — Login screen
│   ├── menu/page.tsx       # COMEN01 — Main menu (stub)
│   └── admin/menu/page.tsx # COADM01 — Admin menu (stub)
├── components/
│   ├── layout/
│   │   └── AppHeader.tsx   # BMS header rows 1-3 (TRNNAME, PGMNAME, date, time)
│   └── ui/
│       ├── ErrorMessage.tsx # ERRMSG row 23
│       └── LoadingSpinner.tsx
├── stores/
│   └── auth-store.ts       # Zustand store replacing CARDDEMO-COMMAREA
├── lib/
│   ├── api-client.ts       # Typed API client
│   └── utils.ts            # Formatting utilities
├── hooks/
│   └── useAuth.ts          # Auth hook wrapping the store
├── middleware.ts            # Route protection (replaces EIBCALEN=0 check)
└── types/
    └── index.ts            # TypeScript interfaces
```

## BMS Field Mapping

| BMS Attribute | React/HTML Equivalent |
|---------------|----------------------|
| UNPROT | `<input>` (editable) |
| ASKIP | `<span>` or `readOnly` |
| DRK | `<input type="password">` |
| IC | `autoFocus` |
| FSET | React controlled component |
| NUM | `type="number"` or `inputMode="numeric"` |
| BRT | `font-bold` Tailwind class |
| COLOR=RED | `text-red-600` |
| COLOR=GREEN | `text-green-600` |
| COLOR=YELLOW | `text-yellow-500` |
| COLOR=TURQUOISE | `text-cyan-600` |
| COLOR=BLUE | `text-blue-600` |
