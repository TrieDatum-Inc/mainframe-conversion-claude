# CardDemo Frontend — Next.js

Modern Next.js frontend migrated from the CardDemo COBOL CICS/BMS mainframe application.

## Migration Overview

This frontend replaces the following mainframe components:

| Legacy Component | Modern Replacement |
|---|---|
| **COSGN0A** (BMS sign-on map) | `src/app/login/page.tsx` — responsive login page |
| **CICS SEND MAP / RECEIVE MAP** | React state + `fetch` API calls |
| **CICS COMMAREA** (session propagation) | `AuthProvider` context with JWT in localStorage |
| **BMS attribute bytes** (field validation) | React Hook Form + Zod schema validation |
| **DFHBMSCA cursor positioning** | `autoFocus` + form error focus management |

### UI Improvements Over BMS

- **Responsive layout**: Card-based design with Tailwind CSS (replaces fixed 80x24 terminal grid)
- **Client-side validation**: Zod schemas validate before submission (BMS only had basic attribute-byte checks)
- **Password masking**: `type="password"` input (BMS screens showed asterisks via MDT)
- **Role-based redirect**: Admin users routed to `/admin`, regular users to `/account` after login
- **Accessible**: Proper labels, focus management, error announcements

## Project Structure

```
front_end/
├── src/
│   ├── app/
│   │   ├── layout.tsx           # Root layout with AuthProvider
│   │   ├── page.tsx             # Home / redirect
│   │   ├── globals.css          # Tailwind base styles
│   │   └── login/
│   │       └── page.tsx         # Login page (replaces COSGN0A BMS map)
│   ├── components/
│   │   ├── auth/
│   │   │   └── AuthProvider.tsx # Auth context (replaces COMMAREA)
│   │   ├── layout/
│   │   │   └── AppHeader.tsx    # Application header with logout
│   │   └── ui/
│   │       └── ErrorMessage.tsx # Reusable error display
│   ├── hooks/
│   │   └── useAuth.ts          # Auth hook for components
│   ├── lib/
│   │   ├── api.ts              # API client with auth headers
│   │   └── auth.ts             # Token storage utilities
│   ├── types/
│   │   └── auth.ts             # TypeScript auth types
│   └── __tests__/
│       └── login.test.tsx      # Login page tests (13 cases)
├── .env.local.example
├── jest.config.js
├── jest.setup.js
├── next.config.js
├── package.json
├── postcss.config.js
├── tailwind.config.ts
└── tsconfig.json
```

## Prerequisites

- Node.js 18+
- npm or yarn
- Backend API running at `http://localhost:8000` (see `backend/README.md`)

## Setup

### 1. Install dependencies

```bash
cd front_end
npm install
```

### 2. Configure environment

```bash
cp .env.local.example .env.local
```

Edit `.env.local` if the backend is running on a different host/port:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Start the development server

```bash
npm run dev
```

The application will be available at `http://localhost:3000`.

### 4. Build for production

```bash
npm run build
npm start
```

## Usage

### Login

1. Navigate to `http://localhost:3000/login`
2. Enter a user ID and password (see test credentials in backend README)
3. Admin users (`user_type = 'A'`) are redirected to `/admin`
4. Regular users (`user_type = 'U'`) are redirected to `/account`

### Logout

Click the **Logout** button in the application header. This:
1. Calls `POST /api/v1/auth/logout` to revoke the JWT server-side
2. Clears the token from localStorage
3. Redirects to `/login`

## Running Tests

```bash
# Run all tests
npm test

# Watch mode (re-runs on file changes)
npm run test:watch

# With coverage report
npm run test:coverage
```

### Test Coverage

The test suite (`src/__tests__/login.test.tsx`) covers:
- Form rendering and field validation
- Successful login with redirect by role (admin vs. regular user)
- Error display for invalid credentials
- Loading state during submission
- User enumeration prevention (generic error messages)

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend API base URL |

## Tech Stack

| Technology | Purpose |
|---|---|
| [Next.js 14](https://nextjs.org/) | React framework with App Router |
| [React Hook Form](https://react-hook-form.com/) | Form state management |
| [Zod](https://zod.dev/) | Schema validation |
| [Zustand](https://zustand-demo.pmnd.rs/) | Lightweight state management |
| [jose](https://github.com/panva/jose) | JWT decoding on the client |
| [Tailwind CSS](https://tailwindcss.com/) | Utility-first CSS |
| [Jest](https://jestjs.io/) + [Testing Library](https://testing-library.com/) | Unit and component testing |
