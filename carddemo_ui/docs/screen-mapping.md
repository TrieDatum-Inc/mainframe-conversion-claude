# BMS Screen to Next.js Route Mapping

This document maps every BMS screen definition to its corresponding Next.js page and FastAPI endpoint.

## Screen Mapping Table

| BMS Map     | BMS MapSet  | COBOL Program | CICS Trans | Next.js Route                          | FastAPI Endpoint                              |
|-------------|-------------|---------------|------------|----------------------------------------|-----------------------------------------------|
| COSGN0A     | COSGN00     | COSGN00C      | CC00       | `/login`                               | `POST /api/v1/auth/login`                     |
| COMEN1A     | COMEN01     | COMEN01C      | CM00       | `/dashboard`                           | `GET /api/v1/admin/menu`                      |
| COADM1A     | COADM01     | COADM01C      | CA00       | `/admin`                               | `GET /api/v1/admin/menu`                      |
| COACTVW     | COACTVW     | COACTVWC      | CA0V       | `/accounts/[id]`                       | `GET /api/v1/accounts/{id}`                   |
| COACTUP     | COACTUP     | COACTUPC      | CA0U       | `/accounts/[id]/edit`                  | `PUT /api/v1/accounts/{id}`                   |
| COBI0A      | COBIL00     | COBIL00C      | CB00       | `/accounts/[id]/payment`               | `POST /api/v1/accounts/{id}/payments`         |
| COCRDLI     | COCRDLI     | COCRDLIC      | CC0L       | `/cards`                               | `GET /api/v1/cards`                           |
| COCRDSL     | COCRDSL     | COCRDSLC      | CC0S       | `/cards/[cardNum]`                     | `GET /api/v1/cards/{card_num}`                |
| COCRDUP     | COCRDUP     | COCRDUPC      | CC0U       | `/cards/[cardNum]/edit`                | `PUT /api/v1/cards/{card_num}`                |
| COTRN00     | COTRN00     | COTRN00C      | CT00       | `/transactions`                        | `GET /api/v1/transactions`                    |
| COTRN01     | COTRN01     | COTRN01C      | CT01       | `/transactions/[id]`                   | `GET /api/v1/transactions/{tran_id}`          |
| COTRN02     | COTRN02     | COTRN02C      | CT02       | `/transactions/new`                    | `POST /api/v1/transactions`                   |
| COUSR00     | COUSR00     | COUSR00C      | CU00       | `/admin/users`                         | `GET /api/v1/admin/users`                     |
| COUSR01     | COUSR01     | COUSR01C      | CU01       | `/admin/users/new`                     | `POST /api/v1/admin/users`                    |
| COUSR02     | COUSR02     | COUSR02C      | CU02       | `/admin/users/[id]/edit`               | `PUT /api/v1/admin/users/{user_id}`           |
| COUSR03     | COUSR03     | COUSR03C      | CU03       | `/admin/users/[id]/edit` (delete btn)  | `DELETE /api/v1/admin/users/{user_id}`        |
| CORPT0A     | CORPT00     | CORPT00C      | CR00       | `/admin/reports`                       | `POST /api/v1/reports/transactions`           |
| COTRTLI     | COTRTLI     | COTRTLIC      | CTLI       | `/admin/transaction-types`             | `GET /api/v1/transaction-types`               |
| COTRTUP     | COTRTUP     | COTRTUPC      | CTTU       | `/admin/transaction-types/[code]`      | `PUT /api/v1/transaction-types/{type_cd}`     |
| COPAU00     | COPAU00     | COPAUS0C      | CPVS       | `/authorizations/accounts/[acctId]`   | `GET /api/v1/authorizations/accounts/{id}`   |
| COPAU01     | COPAU01     | COPAUS1C      | CPVD       | `/authorizations/[authId]`             | `GET /api/v1/authorizations/details/{id}`     |
| —           | —           | COPAUA0C      | CP00       | `/authorizations/new`                  | `POST /api/v1/authorizations`                 |

## Field Attribute Legend (BMS → HTML/CSS)

| BMS Attribute | HTML/CSS Equivalent                           |
|---------------|-----------------------------------------------|
| `UNPROT`      | Editable `<input>` field                      |
| `PROT/ASKIP`  | `readOnly` input or plain text display        |
| `BRT`         | Bold/highlighted styling (font-semibold)      |
| `DRK`         | `type="password"` or `display:none`           |
| `NUM`         | `inputMode="numeric"` on input                |
| `IC`          | `autoFocus` attribute                         |
| `FSET`        | Field always transmitted (tracked in state)   |
| `COLOR=RED`   | Error text in red (text-red-600)              |
| `COLOR=GREEN` | Highlighted text in green                     |
| `COLOR=BLUE`  | Standard label text                           |
| `COLOR=TURQUOISE` | Instructions/prompt text               |

## PF Key Mapping

| CICS PF Key | Next.js Equivalent                            |
|-------------|-----------------------------------------------|
| `ENTER`     | Form submit button / Enter keypress           |
| `PF3`       | Back/Cancel button                            |
| `PF5`       | Refresh / Action toggle (fraud marking)       |
| `PF7`       | "Previous" pagination button                 |
| `PF8`       | "Next" pagination button                     |
| `PF10`      | Confirm/Delete action button                  |
| `CLEAR`     | Reset/Clear form button                       |
