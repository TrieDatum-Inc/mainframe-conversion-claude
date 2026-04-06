# CardDemo Mainframe Modernization

Modernization of the IBM CardDemo CICS/COBOL/BMS application to a modern web stack.

## Architecture

```
Browser (Next.js 14, TypeScript, Tailwind CSS)
    |
    | HTTPS REST (JSON)
    |
FastAPI Application Server (Python 3.11+)
    |--- Router (API layer — thin controllers)
    |--- Service Layer (COBOL PROCEDURE DIVISION logic)
    |--- Repository Layer (VSAM/DB2 → SQLAlchemy ORM)
    |
PostgreSQL 15+
    (replaces VSAM KSDS + VSAM AIX + DB2 + IMS)
```

## Modules

| Module | Status | COBOL Programs | Endpoints |
|--------|--------|----------------|-----------|
| Authentication | Complete | COSGN00C | POST /auth/login, POST /auth/logout, GET /auth/me |
| User Management | Schemas ready | COUSR00-03C | (next sprint) |
| Accounts | Planned | COACTVWC, COACTUPC | (future) |
| Cards | Planned | COCRDLIC, COCRDSLC, COCRDUPC | (future) |
| Transactions | Planned | COTRN00-02C | (future) |
| Billing | Planned | COBIL00C | (future) |
| Reports | Planned | CORPT00C | (future) |
| Authorizations | Planned | COPAUS0-2C | (future) |
| Transaction Types | Planned | COTRTLIC, COTRTUPC | (future) |

## Getting Started

### Backend

```bash
cd backend/
docker compose up -d    # Starts PostgreSQL + FastAPI + runs migrations + seeds data
# OR manual:
pip install -r requirements-dev.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend/
cp .env.local.example .env.local
npm install
npm run dev
```

App: http://localhost:3000

### Running Tests

```bash
cd backend/
python3 -m pytest --cov=app -v    # 47 tests
```

## Test Credentials

| User ID | Password | Role | After Login |
|---------|----------|------|-------------|
| ADMIN001 | Admin1234 | Admin | /admin/menu |
| USER0001 | User1234 | Regular | /menu |

## Tech Specs

See `/tech_specs/target-modern-stack/` for full specifications:
- `00-migration-overview.md` — overall strategy
- `01-database-specification.md` — PostgreSQL schema
- `02-api-specification.md` — REST API endpoints
- `03-frontend-specification.md` — Next.js screens
- `04-api-service-architecture.md` — FastAPI architecture
- `05-frontend-architecture.md` — Next.js architecture
- `07-security-specification.md` — JWT, bcrypt, RBAC
