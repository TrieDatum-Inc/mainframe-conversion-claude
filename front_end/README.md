# CardDemo Credit Card UI

Next.js frontend for the Credit Card Management module.

| BMS Mapset | Map | Converted To |
|---|---|---|
| COCRDLI | CCRDLIA | CardListScreen |
| COCRDSL | CCRDSLA | CardDetailScreen |
| COCRDUP | CCRDUPA | CardUpdateScreen |

## Setup
```bash
cd front_end && npm install
cp .env.local.example .env.local
npm run dev
```
App at: http://localhost:3000

## Tests
```bash
npm test
```

## Key Rules Implemented
- Account filter: 11-digit numeric only
- Card filter: 16-digit numeric only  
- Card name: alphabetic + spaces only, auto-uppercased
- Card status: Y or N only
- Expiry month: 1-12; expiry year: 1950-2099
- Expiry day: not editable (hidden EXPDAY)
- Optimistic concurrency: updated_at token → 409 triggers refresh
- Page size = 7 rows; F5=Save highlighted only on confirm phase
