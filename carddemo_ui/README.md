# CardDemo UI

A modern Next.js web application that replaces the legacy COBOL/CICS BMS 3270 terminal screens of the CardDemo credit card management system. This frontend integrates with the CardDemo FastAPI backend.

## Tech Stack

- **Next.js 14** with App Router
- **TypeScript** (strict mode)
- **Tailwind CSS** for styling
- **Jest + React Testing Library** for unit tests

## Prerequisites

- **Node.js** 18+ and npm
- **CardDemo FastAPI backend** running at `http://localhost:8000` (or configured via env)

## Getting Started

### 1. Install Dependencies

```bash
cd carddemo_ui
npm install
```

### 2. Configure Environment

Copy the example environment file and adjust if needed:

```bash
cp .env.local.example .env.local
```

The default configuration points to `http://localhost:8000`. Edit `.env.local` if your backend runs elsewhere:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Start Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### 4. Login

Use the credentials from the backend seed data:

| User ID | Password  | Role  |
|---------|-----------|-------|
| admin1  | ADMIN123  | Admin |
| user1   | USER1PWD  | User  |

## Available Scripts

| Command           | Description                          |
|-------------------|--------------------------------------|
| `npm run dev`     | Start development server (port 3000) |
| `npm run build`   | Create production build              |
| `npm start`       | Start production server              |
| `npm test`        | Run unit tests                       |
| `npm run lint`    | Run ESLint                           |

## Project Structure

```
carddemo_ui/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── login/              # Login page
│   │   └── (protected)/        # Auth-guarded pages
│   │       ├── dashboard/      # Main menu / dashboard
│   │       ├── accounts/       # Account view & edit
│   │       ├── cards/          # Card list, detail, edit
│   │       ├── transactions/   # Transaction list, detail, add
│   │       ├── authorizations/ # Auth summary, detail, decision
│   │       ├── bill-payment/   # Bill payment
│   │       ├── reports/        # Transaction reports
│   │       └── admin/          # Admin: users, transaction types
│   ├── components/
│   │   ├── ui/                 # Reusable UI components
│   │   ├── layout/             # App shell, header, sidebar
│   │   ├── accounts/           # Account components
│   │   ├── cards/              # Card components
│   │   ├── transactions/       # Transaction components
│   │   ├── authorizations/     # Authorization components
│   │   ├── users/              # User management components
│   │   ├── billing/            # Bill payment components
│   │   ├── reports/            # Report components
│   │   └── transaction-types/  # Transaction type components
│   ├── context/
│   │   └── AuthContext.tsx      # JWT auth context
│   └── lib/
│       ├── api.ts              # API client with JWT injection
│       └── types.ts            # TypeScript types (mirrors backend schemas)
└── __tests__/                  # Unit tests
```

## COBOL Screen to Page Mapping

| COBOL Screen | Description              | UI Route                          |
|-------------|--------------------------|-----------------------------------|
| COSGN00     | Sign-on                  | `/login`                          |
| COMEN01     | Main Menu (User)         | `/dashboard`                      |
| COADM01     | Main Menu (Admin)        | `/dashboard` (admin section)      |
| COACTVW     | Account View             | `/accounts/[id]`                  |
| COACTUP     | Account Update           | `/accounts/[id]/edit`             |
| COCRDLI     | Credit Card List         | `/cards`                          |
| COCRDSL     | Credit Card View         | `/cards/[num]`                    |
| COCRDUP     | Credit Card Update       | `/cards/[num]/edit`               |
| COTRN00     | Transaction List         | `/transactions`                   |
| COTRN01     | Transaction View         | `/transactions/[id]`              |
| COTRN02     | Transaction Add          | `/transactions/new`               |
| CORPT00     | Transaction Reports      | `/reports`                        |
| COBIL00     | Bill Payment             | `/bill-payment`                   |
| COPAU00     | Pending Auth Summary     | `/authorizations`                 |
| COPAU01     | Pending Auth Detail      | `/authorizations/[acctId]`        |
| COPAUA0     | Auth Decision            | `/authorizations` (decision form) |
| COUSR00     | User List                | `/admin/users`                    |
| COUSR01     | User Add                 | `/admin/users/new`                |
| COUSR02     | User Update              | `/admin/users/[id]/edit`          |
| COUSR03     | User Delete              | `/admin/users` (delete button)    |
| COTRTLI     | Transaction Type List    | `/admin/transaction-types`        |
| COTRTUP     | Transaction Type Add     | `/admin/transaction-types/new`    |

## Key Features

- **Role-based navigation**: Admin users see additional menu items (User Management, Transaction Types)
- **JWT authentication**: Token stored in localStorage, auto-injected on API calls
- **Two-step confirm pattern**: Transaction Add, Bill Payment, and Reports use preview-then-confirm flow (mirrors COBOL `confirm='N'`/`'Y'` pattern)
- **Paginated lists**: Cards, Transactions, Users, Transaction Types, Authorization Summaries
- **Error handling**: Field-level validation errors displayed inline, API errors shown as alert banners
- **Responsive design**: Works on desktop, tablet, and mobile viewports

## API Integration

The frontend communicates with the CardDemo FastAPI backend via REST:

| Feature               | Method | Endpoint                              |
|-----------------------|--------|---------------------------------------|
| Login                 | POST   | `/api/auth/login`                     |
| Account View          | GET    | `/api/accounts/{id}`                  |
| Account Update        | PUT    | `/api/accounts/{id}`                  |
| Card List             | GET    | `/api/cards?page=N&page_size=10`      |
| Card View             | GET    | `/api/cards/{num}`                    |
| Card Update           | PUT    | `/api/cards/{num}`                    |
| Transaction List      | GET    | `/api/transactions?page=N`            |
| Transaction View      | GET    | `/api/transactions/{id}`              |
| Transaction Add       | POST   | `/api/transactions`                   |
| Auth Summary          | GET    | `/api/authorizations/summary`         |
| Auth Detail           | GET    | `/api/authorizations/{acctId}/detail` |
| Auth Decision         | POST   | `/api/authorizations/decide`          |
| Bill Payment          | POST   | `/api/bill-payment`                   |
| Reports               | POST   | `/api/reports`                        |
| User List             | GET    | `/api/users`                          |
| User CRUD             | POST/PUT/DELETE | `/api/users/{id}`             |
| Transaction Types     | GET/POST/PUT/DELETE | `/api/transaction-types`  |

## Production Build

```bash
npm run build
npm start
```

The production build uses Next.js standalone output mode for optimized deployment.
