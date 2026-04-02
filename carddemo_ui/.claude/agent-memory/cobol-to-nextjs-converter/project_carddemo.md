---
name: CardDemo UI Project Context
description: Core project facts for the CardDemo mainframe-to-Next.js migration
type: project
---

CardDemo is an AWS mainframe modernization demo app. The UI is a Next.js 16 app in `carddemo_ui/`.

**Why:** Converting IBM z/OS CICS/COBOL/BMS screens to a modern web app for demonstration purposes.

**How to apply:** All pages should mirror the COBOL program logic and BMS map field definitions exactly.

Key facts:
- Next.js 16 with App Router, TypeScript strict, Tailwind CSS v4
- FastAPI backend at http://localhost:8000 (JWT Bearer auth)
- Git branch: migration_1, main branch: main
- Tech specs in `/home/mridul/projects/triedatum-inc/one/mainframe-conversion-claude/tech_specs/`
- Dashboard layout at `src/app/(dashboard)/layout.tsx` (route group)
- Auth context in `src/contexts/AuthContext.tsx`, stores token in localStorage
- `params` in Next.js 16 App Router pages is a Promise — must use `use(params)` to unwrap in Client Components
- `PageProps` and `LayoutProps` are globally available type helpers (no import needed)
- Route group `(dashboard)` wraps all authenticated pages with Sidebar layout
- Admin-only pages check `isAdmin` from `useAuth()` and redirect to /dashboard if not admin
- Zod v4 is installed (breaking change from v3: `z.string().email()` syntax unchanged but some refinement APIs differ)
