# CardDemo Batch Processing Frontend

Next.js frontend for the CardDemo Batch Processing Module.

## Pages

- `/` — Dashboard overview of all batch operations
- `/transactions/posting` — CBTRN02C: Transaction posting form
- `/transactions/report` — CBTRN03C: Report generator with date range
- `/interest` — CBACT04C: Interest calculation with run date
- `/data/export-import` — CBEXPORT/CBIMPORT: Export/import panel

## Setup

```bash
cp .env.local.example .env.local
# Set NEXT_PUBLIC_API_URL=http://localhost:8000
npm install
npm run dev
```
