---
name: Project Architecture Decisions
description: Established folder structure, naming conventions, and architectural choices for this mainframe modernization project
type: project
---

## Repository Structure
- `fast_api/` — FastAPI backend (Poetry project)
  - `fast_api/sql/` — DDL and seed SQL files
  - `fast_api/src/app/` — application source
  - `fast_api/tests/unit/` — service + validator unit tests (no DB needed)
  - `fast_api/tests/integration/` — API endpoint tests (mocked service)
- `front_end/` — Next.js frontend (App Router)
  - `front_end/src/app/` — pages
  - `front_end/src/components/ui/` — base UI components
  - `front_end/src/components/forms/` — form components
  - `front_end/src/hooks/` — custom React hooks
  - `front_end/__tests__/` — Jest unit tests

## Naming Conventions
- Python: snake_case throughout, following COBOL field names (e.g. acct_id, cust_first_name)
- TypeScript: snake_case for API types to match backend; camelCase only for React component props
- Database: snake_case table/column names matching COBOL field names
- Branch naming: `feature/<module-name>-module`

## Architecture Layers (FastAPI)
- **Routers**: HTTP only — input validation, status codes, exception mapping
- **Services**: ALL business logic — COBOL paragraph/section equivalents
- **Repositories**: Data access only — one repository class per aggregate root
- **Schemas**: Pydantic models with COBOL-equivalent validators
- **Models**: SQLAlchemy ORM, one file per VSAM file/copybook

## Testing Strategy
- Unit tests use mock repository (AsyncMock(spec=AccountRepository))
- Integration tests use httpx AsyncClient + patched service methods
- No real DB required for any test (repository is the DB boundary)
- Test file naming: test_<module_name>_service.py, test_<module_name>_api.py, test_validators.py

## Why: Motivation
This repo converts AWS CardDemo COBOL/CICS mainframe application to FastAPI + PostgreSQL + Next.js.
Each COBOL program maps to: one router file + one service file + relevant schema methods.
