# CardDemo Transaction Processing Frontend

Next.js 14 frontend converted from BMS screen definitions COTRN00 (COTRN0A), COTRN01 (COTRN1A), COTRN02 (COTRN2A).

## BMS Screen to Page Mapping

| BMS Mapset | CICS Transaction | Next.js Route |
|---|---|---|
| COTRN00 / COTRN0A | CT00 | /transactions |
| COTRN01 / COTRN1A | CT01 | /transactions/{tranId} |
| COTRN02 / COTRN2A | CT02 | /transactions/add |

## Setup

```bash
npm install
cp .env.local.example .env.local
# Edit NEXT_PUBLIC_API_URL in .env.local

npm run dev
```

## BMS Field to UI Component Mapping

| BMS Attribute | UI Element |
|---|---|
| ASKIP (protected) | Read-only text display |
| UNPROT (input) | Input field with green text and underline |
| BRT (bright) | Bold/highlighted text |
| IC (initial cursor) | autoFocus attribute |
| HILIGHT=UNDERLINE | CSS underline on input |
| Color RED (ERRMSG) | Red text, dark red background |
| Color GREEN (success) | Green text, dark green background |
| Color TURQUOISE (labels) | Teal label text |
| Color YELLOW (titles) | Yellow heading text |
| Color BLUE (values) | Blue display text |
| PF3=Back | F3 Back button / Link |
| PF4=Clear | F4 Clear button |
| PF5=Browse / Copy Last | F5 button |
| PF7=Backward | F7 Backward pagination button |
| PF8=Forward | F8 Forward pagination button |
