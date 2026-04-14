# Frontend Specification: Next.js Application
# CardDemo Mainframe Modernization

## Document Purpose

This specification defines the complete Next.js web application that replaces all 21 BMS maps from the CardDemo CICS application. Every BMS field, PF-key binding, attribute mapping, navigation flow, and validation rule is captured here to ensure functional equivalence with the original mainframe screens.

---

## 1. BMS Attribute to React/HTML Mapping

The following table governs how every BMS field attribute translates into a React/HTML implementation.

| BMS Attribute | Meaning | React/HTML Equivalent |
|---------------|---------|----------------------|
| UNPROT | Operator-enterable input field | `<input>` element, no `disabled` or `readOnly` |
| ASKIP | Auto-skip; output-only | `<span>` or `<input readOnly disabled>` |
| PROT | Protected; no entry | `<input disabled>` or `<span>` |
| DRK | Dark; content not displayed | `<input type="password">` |
| IC | Initial cursor position | `autoFocus` on the input element |
| FSET | Force retransmit (always send value) | React controlled component; value always in state |
| NUM | Numeric-only input | `<input type="number">` or `inputMode="numeric"` with Zod `z.number()` |
| MUSTFILL | Terminal hardware required field | Zod `.min(1)` validator; HTML `required` |
| JUSTIFY=(RIGHT,ZERO) | Right-align, zero-fill | Input `className="text-right"` with value normalization |
| BRT | Bright/high-intensity | `font-bold` Tailwind class |
| NORM | Normal intensity | Normal weight text |
| HILIGHT=UNDERLINE | Underline decoration | `underline` Tailwind class on the associated label |
| COLOR=RED | Red foreground | `text-red-600` Tailwind class |
| COLOR=GREEN | Green foreground | `text-green-600` Tailwind class |
| COLOR=BLUE | Blue foreground | `text-blue-600` Tailwind class |
| COLOR=YELLOW | Yellow foreground | `text-yellow-500` Tailwind class |
| COLOR=TURQUOISE | Turquoise labels | `text-cyan-600` Tailwind class |
| COLOR=NEUTRAL | Neutral color | `text-gray-700` Tailwind class |
| DFHGREEN (programmatic) | Success message color | `text-green-700` applied to message element |
| DFHRED (programmatic) | Error/warning message color | `text-red-600` applied to message element |
| DFHNEUTR (programmatic) | Neutral/prompt message color | `text-gray-600` applied to message element |
| PICOUT='+ZZZ,ZZZ,ZZZ.99' | Signed, comma-formatted currency | `Intl.NumberFormat` with sign display |

---

## 2. PF Key to UI Action Mapping (Global Conventions)

| BMS PF Key | CardDemo Convention | React UI Implementation |
|------------|---------------------|------------------------|
| ENTER | Primary action (search/submit/confirm) | `<form onSubmit>` or primary `<button type="submit">` |
| PF3 | Back / Return to previous screen | `router.back()` or explicit back button |
| PF4 | Clear all fields | "Clear" button that resets form state |
| PF5 | Save / Confirm delete | "Save" or "Confirm Delete" button |
| PF7 | Page backward | "Previous Page" button |
| PF8 | Page forward | "Next Page" button |
| PF10 | Confirm pending action | "Confirm" button |
| PF12 | Cancel / Exit without save | "Cancel" button navigating to parent |
| PF2 | Add / Navigate to add screen | "Add New" button |
| PF6 | Add (alternative, not activated) | Not rendered |
| F2 | Add new (transaction type) | "Add New" button |

---

## 3. Shared Layout Components

### 3.1 AppHeader Component

Maps to the standard BMS header (rows 1–2 on every map).

**File:** `src/components/layout/AppHeader.tsx`

**Props:**
```typescript
interface AppHeaderProps {
  programName: string;     // PGMNAMEO — current program identifier
  transactionId: string;   // TRNNAMEO — current transaction ID
}
```

**Content displayed:** Application title lines 1 and 2 (populated from API `GET /api/v1/system/date-time`), current date (MM/DD/YY format), current time (HH:MM:SS format), program name, transaction ID.

**Visual structure:** Two-row header bar with title centered, date/time on the right, program/transaction info on the left. Blue text for labels, yellow for title lines.

### 3.2 ErrorMessage Component

Maps to ERRMSG field (row 23 on every map). BRT RED ASKIP.

**File:** `src/components/ui/ErrorMessage.tsx`

**Props:**
```typescript
interface ErrorMessageProps {
  message: string;
  color?: 'red' | 'green' | 'neutral';  // maps to DFHRED/DFHGREEN/DFHNEUTR
}
```

**Behavior:** Displays full-width message bar below the content area. Color variant controls text and background styling. Maps to ERRMSG (ASKIP,BRT,FSET RED).

### 3.3 PageWrapper Component

Common page structure shared by all screens.

**File:** `src/components/layout/PageWrapper.tsx`

Renders: AppHeader + main content area + ErrorMessage + ActionBar (PF key buttons). Provides consistent vertical spacing that reflects the BMS 24-row layout structure.

---

## 4. Screen-by-Screen Specification

---

### 4.1 Login Screen — COSGN00 (BMS map COSGN0A)

**Route:** `/login`
**Page file:** `src/app/login/page.tsx`
**API calls:** `POST /api/v1/auth/login`
**COBOL program:** COSGN00C

#### 4.1.1 Layout Description

Centered login card with the CardDemo decorative banner ("NATIONAL RESERVE NOTE" ASCII art). Header bar shows application title, date, time.

#### 4.1.2 Form Fields

| BMS Field | COBOL Name | React Field | Type | Constraints | Notes |
|-----------|------------|-------------|------|-------------|-------|
| USERID | USERIDI | `userId` | `<input type="text">` | maxLength=8, required | autoFocus (IC attribute); green text |
| PASSWD | PASSWDI | `password` | `<input type="password">` | maxLength=8, required | DRK → type=password; masked display |

#### 4.1.3 Actions

| BMS Key | Button Label | Handler |
|---------|-------------|---------|
| ENTER | "Sign On" (primary submit) | `POST /api/v1/auth/login`; on success store JWT, redirect to `/menu` (user) or `/admin` (admin) |
| PF3 | "Exit" | Navigate to external URL or show exit confirmation |

#### 4.1.4 Validation (Zod schema)

```typescript
const loginSchema = z.object({
  userId: z.string().min(1, 'User ID cannot be empty').max(8),
  password: z.string().min(1, 'Password cannot be empty').max(8),
});
```

#### 4.1.5 Error Display

- Invalid credentials: Display server error message in ERRMSG bar (red, high intensity)
- Empty fields: Inline Zod validation errors below each field

#### 4.1.6 State Management

On successful login: store JWT in `localStorage` or `sessionStorage` (per security spec). Store `userType` (A/U) and `userId` in auth context. Redirect to `/admin/menu` for type A, `/menu` for type U.

---

### 4.2 Main Menu — COMEN01 (BMS map COMEN1A)

**Route:** `/menu`
**Page file:** `src/app/menu/page.tsx`
**API calls:** `GET /api/v1/menus/main`
**COBOL program:** COMEN01C
**Access:** User type U only (admin users go to `/admin/menu`)

#### 4.2.1 Layout Description

Centered menu list with up to 12 numbered options (OPTN001–OPTN012). Numeric input field at bottom for option selection.

#### 4.2.2 Fields

| BMS Field | COBOL Name | React Field | Notes |
|-----------|------------|-------------|-------|
| OPTN001–OPTN012 | OPTN001O–OPTN012O | Static `<li>` items | Read-only menu text; blue color |
| OPTION | OPTIONI | `<input type="number">` | Right-aligned; autoFocus; min=1, max=number of options shown; JUSTIFY=(RIGHT,ZERO) |

#### 4.2.3 Menu Options and Routes

| Option | Label | Route |
|--------|-------|-------|
| 1 | View Account | `/accounts/view` |
| 2 | Update Account | `/accounts/update` |
| 3 | View Credit Card | `/cards/view` |
| 4 | Update Credit Card | `/cards/update` |
| 5 | View Transaction | `/transactions/view` |
| 6 | Add Transaction | `/transactions/add` |
| 7 | List Transactions | `/transactions/list` |
| 8 | Bill Payment | `/billing/payment` |
| 9 | Transaction Reports | `/reports/transactions` |
| 0 | Exit | Logout and redirect to `/login` |

#### 4.2.4 Actions

| BMS Key | Button Label | Handler |
|---------|-------------|---------|
| ENTER | "Continue" | Read selected option number; navigate to corresponding route |
| PF3 | "Exit" | Logout; navigate to `/login` |

#### 4.2.5 Validation

Selected option must be a valid integer matching a displayed menu item. Display error in message bar for out-of-range or non-numeric input.

---

### 4.3 Admin Menu — COADM01 (BMS map COADM1A)

**Route:** `/admin/menu`
**Page file:** `src/app/admin/menu/page.tsx`
**API calls:** `GET /api/v1/menus/admin`
**COBOL program:** COADM01C
**Access:** User type A only (route-guard in middleware.ts)

Structurally identical to COMEN01 but with different menu options and title "Admin Menu".

#### 4.3.1 Admin Menu Options and Routes

| Option | Label | Route |
|--------|-------|-------|
| 1 | List/Add Users | `/admin/users` |
| 2 | Add User | `/admin/users/new` |
| 3 | Update User | `/admin/users/update` |
| 4 | Delete User | `/admin/users/delete` |
| 5 | Manage Transaction Types (List) | `/admin/transaction-types` |
| 6 | Maintain Transaction Type (Edit) | `/admin/transaction-types/edit` |
| 0 | Exit | Logout and redirect to `/login` |

---

### 4.4 Account View — COACTVW (BMS map CACTVWA)

**Route:** `/accounts/view`
**Page file:** `src/app/accounts/view/page.tsx`
**API calls:** `GET /api/v1/accounts/{account_id}`
**COBOL program:** COACTVWC

#### 4.4.1 Layout Description

Account number search field at top. All detail fields below are read-only (ASKIP). Financial amounts displayed with sign and comma formatting (PICOUT='+ZZZ,ZZZ,ZZZ.99').

#### 4.4.2 Form Fields

**Search input:**

| BMS Field | COBOL Name | React Field | Constraints | Notes |
|-----------|------------|-------------|-------------|-------|
| ACCTSID | ACCTSIDO | `accountId` | maxLength=11, pattern=`^\d{11}$`, required | autoFocus (IC); MUSTFILL → required; PICIN=99999999999 → numeric only |

**Account summary (all read-only):**

| BMS Field | COBOL Name | Display Label | Notes |
|-----------|------------|---------------|-------|
| ACSTTUS | ACSTTUSO | Active Y/N | Single character Y/N badge |
| ADTOPEN | ADTOPENO | Opened Date | Formatted date string |
| AEXPDT | AEXPDTO | Expiry Date | Formatted date string |
| AREISDT | AREISDTO | Reissue Date | Formatted date string |
| ACRDLIM | ACRDLIMO | Credit Limit | `+ZZZ,ZZZ,ZZZ.99` format |
| ACSHLIM | ACSHLIMO | Cash Credit Limit | `+ZZZ,ZZZ,ZZZ.99` format |
| ACURBAL | ACURBALO | Current Balance | `+ZZZ,ZZZ,ZZZ.99` format |
| ACRCYCR | ACRCYCRO | Current Cycle Credit | `+ZZZ,ZZZ,ZZZ.99` format |
| ACRCYDB | ACRCYDBO | Current Cycle Debit | `+ZZZ,ZZZ,ZZZ.99` format |
| AADDGRP | AADDGRPO | Account Group | Text |

**Customer details (all read-only):**

| BMS Field | COBOL Name | Display Label | Notes |
|-----------|------------|---------------|-------|
| ACSTNUM | ACSTNUM | Customer ID | |
| ACSTSSN | ACSTSSNO | SSN | Masked: `***-**-XXXX` display |
| ACSTDOB | ACSTDOBO | Date of Birth | |
| ACSTFCO | ACSTFCOO | FICO Score | |
| ACSFNAM | ACSFNAMO | First Name | |
| ACSMNAM | ACSMNAM | Middle Name | |
| ACSLNAM | ACSLNAMO | Last Name | |
| ACSADL1 | ACSADL1O | Address Line 1 | |
| ACSADL2 | ACSADL2O | Address Line 2 | |
| ACSCITY | ACSCITYO | City | |
| ACSSTTE | ACSSSTEO | State | |
| ACSZIPC | ACSZIPCO | ZIP | |
| ACSCTRY | ACSSTRYO | Country | |
| ACSPHN1 | ACSPHN1O | Phone 1 | |
| ACSPHN2 | ACSPHN2O | Phone 2 | |
| ACSGOVT | ACSGOVTO | Govt ID Reference | |
| ACSEFTC | ACSEFTCO | EFT Account ID | |
| ACSPFLG | ACSPFLGO | Primary Card Holder Y/N | |

#### 4.4.3 Actions

| BMS Key | Button Label | Handler |
|---------|-------------|---------|
| ENTER | "View Account" | `GET /api/v1/accounts/{accountId}`; populate all display fields |
| PF3 | "Exit" | `router.back()` |

#### 4.4.4 Navigation to Update

A "Update Account" link/button navigates to `/accounts/update?accountId={current}`. This replaces the implicit navigation from COACTVWC to COACTUPC.

---

### 4.5 Account Update — COACTUP (BMS map CACTUPA)

**Route:** `/accounts/update`
**Page file:** `src/app/accounts/update/page.tsx`
**API calls:** `GET /api/v1/accounts/{account_id}`, `PUT /api/v1/accounts/{account_id}`
**COBOL program:** COACTUPC

#### 4.5.1 Layout Description

Same field layout as Account View but all detail fields are editable (UNPROT). Split date fields (year/month/day) are rendered as three separate inputs with separator labels. Split SSN is rendered as three inputs (3/2/4 digits) with dashes. Split phone as three inputs (area code / exchange / number).

#### 4.5.2 Editable Fields

**Account section:**

| BMS Fields | React Field | Type | Constraints |
|------------|-------------|------|-------------|
| ACCTSID | `accountId` | text | read-only after initial load (not changed in this screen) |
| ACSTTUS | `accountStatus` | text | maxLength=1; must be Y or N |
| OPNYEAR/OPNMON/OPNDAY | `openedDate` (combined) | date inputs | Must form valid calendar date |
| EXPYEAR/EXPMON/EXPDAY | `expiryDate` (combined) | date inputs | Must be valid future date |
| RISYEAR/RISMON/RISDAY | `reissueDate` (combined) | date inputs | Must be valid date |
| ACRDLIM | `creditLimit` | number input | >= 0; max 15 chars |
| ACSHLIM | `cashLimit` | number input | >= 0; <= creditLimit |
| ACURBAL | `currentBalance` | number input | Numeric |
| ACRCYCR | `cycleCreditAmount` | number input | Numeric |
| ACRCYDB | `cycleDebitAmount` | number input | Numeric |
| AADDGRP | `accountGroup` | text | maxLength=10 |

**Customer section:**

| BMS Fields | React Field | Type | Constraints |
|------------|-------------|------|-------------|
| ACSTNUM | `customerId` | text | maxLength=9 |
| ACTSSN1/ACTSSN2/ACTSSN3 | `ssn` (combined) | three numeric inputs | SSN1: 3 digits, SSN2: 2 digits, SSN3: 4 digits |
| DOBYEAR/DOBMON/DOBDAY | `dateOfBirth` (combined) | date inputs | Valid date |
| ACSTFCO | `ficoScore` | number | 300–850 |
| ACSFNAM | `firstName` | text | maxLength=25 |
| ACSMNAM | `middleName` | text | maxLength=25 |
| ACSLNAM | `lastName` | text | maxLength=25 |
| ACSADL1 | `addressLine1` | text | maxLength=50 |
| ACSADL2 | `addressLine2` | text | maxLength=50 |
| ACSCITY | `city` | text | maxLength=50 |
| ACSSTTE | `state` | text | maxLength=2 |
| ACSZIPC | `zipCode` | text | maxLength=5 |
| ACSCTRY | `country` | text | maxLength=3 |
| ACSPH1A/B/C | `phone1` (combined) | three numeric inputs | Area(3)/Exchange(3)/Number(4) |
| ACSPH2A/B/C | `phone2` (combined) | three numeric inputs | Area(3)/Exchange(3)/Number(4) |
| ACSGOVT | `governmentId` | text | maxLength=20 |
| ACSEFTC | `eftAccountId` | text | maxLength=10 |
| ACSPFLG | `primaryCardHolder` | text | Must be Y or N |

#### 4.5.3 Initial Load Behavior

On page mount (or when account ID is provided via query param), `GET /api/v1/accounts/{accountId}` populates all fields. This mirrors the COACTUPC first-entry auto-populate from COMMAREA.

#### 4.5.4 Actions

| BMS Key | Button Label | Handler | Initial Visibility |
|---------|-------------|---------|-------------------|
| ENTER | "Process" | Validate and call `PUT /api/v1/accounts/{id}` | Always visible |
| PF3 | "Exit" | Navigate back without saving | Always visible |
| PF5 | "Save" | Same as ENTER (explicit save) | Hidden until data loaded (mirrors FKEY05 DRK pattern) |
| PF12 | "Cancel" | Reset form to last loaded values | Hidden until data loaded (mirrors FKEY12 DRK pattern) |

**Implementation note for DRK buttons:** FKEY05 and FKEY12 begin with `DRK` attribute (hidden). Implement as React state `showSaveCancel: boolean`, initially `false`, set to `true` after successful data load. Render Save/Cancel buttons conditionally on this state.

#### 4.5.5 Validation (Zod schema, partial)

```typescript
const accountUpdateSchema = z.object({
  accountStatus: z.enum(['Y', 'N']),
  creditLimit: z.number().min(0),
  cashLimit: z.number().min(0),
  ficoScore: z.number().min(300).max(850),
  primaryCardHolder: z.enum(['Y', 'N']),
  // dates validated to form valid calendar dates
});
```

---

### 4.6 Bill Payment — COBIL00 (BMS map COBIL0A)

**Route:** `/billing/payment`
**Page file:** `src/app/billing/payment/page.tsx`
**API calls:** `GET /api/v1/billing/{account_id}/balance`, `POST /api/v1/billing/{account_id}/payment`
**COBOL program:** COBIL00C

#### 4.6.1 Two-Phase Interaction

This screen has two phases matching the COBOL two-phase pattern:

- **Phase 1:** Account ID entry → fetch balance
- **Phase 2:** Display balance → Y/N confirmation → process payment

#### 4.6.2 Fields

| BMS Field | React Field | Phase | Notes |
|-----------|-------------|-------|-------|
| ACTIDIN | `accountId` | 1 | autoFocus (IC); 11-char input; green text |
| CURBAL | `currentBalance` | 2 | Read-only display; populated after Phase 1 lookup; ASKIP |
| CONFIRM | `confirmed` | 2 | Y/N radio buttons or single-char input; FSET |

**Phase 1 state:** Show account ID input. Current balance area hidden or shows placeholder.

**Phase 2 state:** Show account ID (locked, read-only after lookup), current balance displayed (green text), Y/N confirmation visible.

#### 4.6.3 Actions

| BMS Key | Button Label | Phase | Handler |
|---------|-------------|-------|---------|
| ENTER | "Continue" | 1 | `GET /api/v1/billing/{accountId}/balance`; transition to Phase 2 |
| ENTER | "Pay Now" | 2 | If CONFIRM=Y: `POST /api/v1/billing/{accountId}/payment`; success message |
| PF3 | "Back" | Both | `router.back()` |
| PF4 | "Clear" | Both | Reset all fields; return to Phase 1 |

#### 4.6.4 React State

```typescript
interface BillPaymentState {
  phase: 1 | 2;
  accountId: string;
  currentBalance: string;
  confirmed: 'Y' | 'N' | '';
}
```

---

### 4.7 Credit Card List — COCRDLI (BMS map CCRDLIA)

**Route:** `/cards/list`
**Page file:** `src/app/cards/list/page.tsx`
**API calls:** `GET /api/v1/cards?account_id=&card_number=&page=&per_page=7`
**COBOL program:** COCRDLIC

#### 4.7.1 Layout Description

Search filters at top (account number, card number). Paginated table of up to 7 cards. Row selector column for navigation to detail. Page number display. Forward/backward paging.

#### 4.7.2 Search Fields

| BMS Field | React Field | Constraints | Notes |
|-----------|------------|-------------|-------|
| ACCTSID | `accountId` | maxLength=11 | Optional filter; autoFocus (IC) |
| CARDSID | `cardNumber` | maxLength=16 | Optional filter |

#### 4.7.3 List Row Fields (7 rows)

Each row displays:
- Selector: clickable radio or checkbox (replaces CRDSEL1–7 which are PROT by default, made UNPROT when populated)
- Account number (ACCTNO1–7): read-only
- Card number (CRDNUM1–7): read-only
- Active status (CRDSTS1–7): read-only badge Y/N

**CRDSTP fields (hidden paging markers):** Replaced by server-side pagination state; not rendered in React.

#### 4.7.4 Row Selection

The operator types `S` in a CRDSEL field in COBOL. In the modern UI: clicking a row or a "Select" radio button triggers navigation. A "View" button on each row navigates to `/cards/view?cardNumber={crdnum}`. The row selection behavior (selecting one row at a time) is enforced by radio button group semantics.

#### 4.7.5 Actions

| BMS Key | Button Label | Handler |
|---------|-------------|---------|
| ENTER | "Search" | Fetch with filters and page=1 |
| PF3 | "Exit" | `router.back()` |
| PF7 | "Previous Page" | Decrement page; re-fetch |
| PF8 | "Next Page" | Increment page; re-fetch |

---

### 4.8 Credit Card View — COCRDSL (BMS map CCRDSLA)

**Route:** `/cards/view`
**Page file:** `src/app/cards/view/page.tsx`
**API calls:** `GET /api/v1/cards/{card_number}`
**COBOL program:** COCRDSLIC

#### 4.8.1 Fields

| BMS Field | React Field | Input/Output | Notes |
|-----------|------------|--------------|-------|
| ACCTSID | `accountId` | Input | Optional search; autoFocus (IC); UNPROT |
| CARDSID | `cardNumber` | Input | Optional search; UNPROT |
| CRDNAME | `cardName` | Output | Read-only; ASKIP |
| CRDSTCD | `activeStatus` | Output | Y/N badge; ASKIP |
| EXPMON | `expiryMonth` | Output | 2-digit; ASKIP |
| EXPYEAR | `expiryYear` | Output | 4-digit; ASKIP |

#### 4.8.2 Actions

| BMS Key | Button Label | Handler |
|---------|-------------|---------|
| ENTER | "Search Cards" | Fetch card matching accountId/cardNumber |
| PF3 | "Exit" | `router.back()` |

#### 4.8.3 Navigation to Update

"Update Card" button navigates to `/cards/update?accountId={current}&cardNumber={current}`.

---

### 4.9 Credit Card Update — COCRDUP (BMS map CCRDUPA)

**Route:** `/cards/update`
**Page file:** `src/app/cards/update/page.tsx`
**API calls:** `GET /api/v1/cards/{card_number}`, `PUT /api/v1/cards/{card_number}`
**COBOL program:** COCRDUPD

#### 4.9.1 Fields

| BMS Field | React Field | Input/Output | Notes |
|-----------|------------|--------------|-------|
| ACCTSID | `accountId` | Output only | PROT — locked; pre-populated; disabled input |
| CARDSID | `cardNumber` | Input | UNPROT — editable |
| CRDNAME | `cardName` | Input | Required; maxLength=50 |
| CRDSTCD | `activeStatus` | Input | Y or N |
| EXPMON | `expiryMonth` | Input | 01–12 |
| EXPYEAR | `expiryYear` | Input | >= current year; 4-digit |
| EXPDAY | `expiryDay` | Hidden state | DRK PROT FSET → hidden in UI; maintained in React state; not shown to user |

**EXPDAY hidden field:** The DRK/PROT/FSET day component is preserved as internal React state (not rendered as an HTML input). The day value is fetched from the GET response and included in the PUT request payload even though it is not shown to the user.

#### 4.9.2 Actions

| BMS Key | Button Label | Handler | Initial Visibility |
|---------|-------------|---------|-------------------|
| ENTER | "Process" | Validate and submit update | Always |
| PF3 | "Exit" | Navigate back without saving | Always |
| PF5 | "Save" | `PUT /api/v1/cards/{cardNumber}` with payload including hidden expiry day | Hidden until data loaded; mirrors FKEYSC DRK |
| PF12 | "Cancel" | Reset to last fetched values | Hidden until data loaded |

**DRK FKEYSC implementation:** React state `showSaveCancel: boolean` initially `false`. Set to `true` after successful card fetch. Save/Cancel buttons rendered conditionally.

#### 4.9.3 Optimistic Lock

Include `optimistic_lock_version` (mapped from `updated_at` timestamp) in PUT request body. Backend returns 409 Conflict if concurrent modification detected.

#### 4.9.4 Validation

```typescript
const cardUpdateSchema = z.object({
  cardName: z.string().min(1, 'Card name cannot be blank').max(50),
  activeStatus: z.enum(['Y', 'N']),
  expiryMonth: z.string().regex(/^(0[1-9]|1[0-2])$/, 'Month must be 01-12'),
  expiryYear: z.string().regex(/^\d{4}$/).refine(
    y => parseInt(y) >= new Date().getFullYear(),
    'Year must be current year or later'
  ),
});
```

---

### 4.10 Transaction Reports — CORPT00 (BMS map CORPT0A)

**Route:** `/reports/transactions`
**Page file:** `src/app/reports/transactions/page.tsx`
**API calls:** `POST /api/v1/reports/request`
**COBOL program:** CORPT00C

#### 4.10.1 Fields

| BMS Field | React Field | Notes |
|-----------|------------|-------|
| MONTHLY | `reportType === 'monthly'` | Radio button; autoFocus (IC) |
| YEARLY | `reportType === 'yearly'` | Radio button |
| CUSTOM | `reportType === 'custom'` | Radio button |
| SDTMM | `startMonth` | 2-digit NUM; visible when custom selected |
| SDTDD | `startDay` | 2-digit NUM; visible when custom selected |
| SDTYYYY | `startYear` | 4-digit NUM; visible when custom selected |
| EDTMM | `endMonth` | 2-digit NUM; visible when custom selected |
| EDTDD | `endDay` | 2-digit NUM; visible when custom selected |
| EDTYYYY | `endYear` | 4-digit NUM; visible when custom selected |
| CONFIRM | `confirmed` | Y/N; must be Y to submit |

**Implementation note:** The three selector fields (MONTHLY/YEARLY/CUSTOM) are radio buttons with mutual exclusivity enforced by React state. The custom date range fields are conditionally rendered only when `reportType === 'custom'`.

#### 4.10.2 Actions

| BMS Key | Button Label | Handler |
|---------|-------------|---------|
| ENTER | "Submit Report" | Validate; if CONFIRM=Y call `POST /api/v1/reports/request` |
| PF3 | "Back" | `router.back()` |

#### 4.10.3 Validation

```typescript
const reportSchema = z.object({
  reportType: z.enum(['monthly', 'yearly', 'custom']),
  startDate: z.string().optional(),
  endDate: z.string().optional(),
  confirmed: z.enum(['Y', 'N']),
}).refine(data => {
  if (data.reportType === 'custom') {
    return data.startDate && data.endDate;
  }
  return true;
}, { message: 'Custom date range requires start and end dates' });
```

---

### 4.11 Transaction List — COTRN00 (BMS map COTRN0A)

**Route:** `/transactions/list`
**Page file:** `src/app/transactions/list/page.tsx`
**API calls:** `GET /api/v1/transactions?transaction_id=&page=&per_page=10`
**COBOL program:** COTRN00C

#### 4.11.1 Fields

**Search:**

| BMS Field | React Field | Notes |
|-----------|------------|-------|
| TRNIDIN | `transactionIdFilter` | Optional 16-char filter |
| PAGENUM | (derived from pagination state) | Display-only page indicator |

**List rows (10 rows):**

| BMS Fields | React Display | Notes |
|-----------|--------------|-------|
| SEL0001–SEL0010 | Row click or "View" button | Selector column; `S` → navigate to detail |
| TRNID01–TRNID10 | Transaction ID column | ASKIP FSET |
| TDATE01–TDATE10 | Date column | ASKIP FSET |
| TDESC01–TDESC10 | Description column | ASKIP FSET |
| TAMT001–TAMT010 | Amount column | ASKIP FSET |

#### 4.11.2 Row Selection

Clicking a row or clicking "View" button navigates to `/transactions/view?transactionId={TRNID}`. Replaces the COBOL `S` selector input pattern.

#### 4.11.3 Actions

| BMS Key | Button Label | Handler |
|---------|-------------|---------|
| ENTER | "Search" | Fetch with filter; page=1 |
| PF3 | "Back" | `router.back()` |
| PF7 | "Previous Page" | page - 1 |
| PF8 | "Next Page" | page + 1 |

---

### 4.12 Transaction View — COTRN01 (BMS map COTRN1A)

**Route:** `/transactions/view`
**Page file:** `src/app/transactions/view/page.tsx`
**API calls:** `GET /api/v1/transactions/{transaction_id}`
**COBOL program:** COTRN01C

#### 4.12.1 Fields

| BMS Field | React Field | Notes |
|-----------|------------|-------|
| TRNIDIN | `transactionId` | Input; autoFocus (IC); FSET UNPROT |
| TRNID | Transaction ID display | ASKIP read-only |
| CARDNUM | Card number | ASKIP read-only |
| TTYPCD | Type code | ASKIP read-only |
| TCATCD | Category code | ASKIP read-only |
| TRNSRC | Source | ASKIP read-only |
| TDESC | Description | ASKIP read-only |
| TRNAMT | Amount | ASKIP read-only |
| TORIGDT | Original date | ASKIP read-only |
| TPROCDT | Processing date | ASKIP read-only |
| MID | Merchant ID | ASKIP read-only |
| MNAME | Merchant name | ASKIP read-only |
| MCITY | Merchant city | ASKIP read-only |
| MZIP | Merchant ZIP | ASKIP read-only |

**Implementation note on COTRN01C READ UPDATE:** The original COBOL uses READ UPDATE unnecessarily for a display-only operation. The modern API uses `GET` (SELECT without lock). This is a documented bug correction.

#### 4.12.2 Actions

| BMS Key | Button Label | Handler |
|---------|-------------|---------|
| ENTER | "Fetch" | `GET /api/v1/transactions/{transactionId}` |
| PF3 | "Back" | `router.back()` |
| PF4 | "Clear" | Reset all display fields; clear search input |
| PF5 | "Browse Tran." | Navigate to `/transactions/add` |

---

### 4.13 Transaction Add — COTRN02 (BMS map COTRN2A)

**Route:** `/transactions/add`
**Page file:** `src/app/transactions/add/page.tsx`
**API calls:** `POST /api/v1/transactions`, `GET /api/v1/transactions/last` (for PF5 copy)
**COBOL program:** COTRN02C

#### 4.13.1 Fields

| BMS Field | React Field | Type | Constraints | Notes |
|-----------|------------|------|-------------|-------|
| ACTIDIN | `accountId` | text | maxLength=11 | autoFocus (IC); mutually exclusive with CARDNIN |
| CARDNIN | `cardNumber` | text | maxLength=16 | Mutually exclusive with ACTIDIN |
| TTYPCD | `transactionTypeCode` | text | maxLength=2; required | Valid type code |
| TCATCD | `categoryCode` | text | maxLength=4; required | Valid category code |
| TRNSRC | `source` | text | maxLength=10; required | Valid source code |
| TDESC | `description` | text | maxLength=60; required | Non-blank |
| TRNAMT | `amount` | text | format -99999999.99 | Non-zero numeric |
| TORIGDT | `originalDate` | date | YYYY-MM-DD; required | Valid date |
| TPROCDT | `processingDate` | date | YYYY-MM-DD; >= originalDate | Valid date |
| MID | `merchantId` | text | maxLength=9; required | |
| MNAME | `merchantName` | text | maxLength=30; required | Non-blank |
| MCITY | `merchantCity` | text | maxLength=25 | |
| MZIP | `merchantZip` | text | maxLength=10 | |
| CONFIRM | `confirmed` | text | Y or N | Y triggers record insertion |

**Mutual exclusivity of ACTIDIN/CARDNIN:** At least one must be provided. Display an error if both are blank. If both are provided, backend validates the card belongs to the account.

#### 4.13.2 Actions

| BMS Key | Button Label | Handler |
|---------|-------------|---------|
| ENTER | "Continue" | Validate all fields; if CONFIRM=Y: `POST /api/v1/transactions` |
| PF3 | "Back" | `router.back()` |
| PF4 | "Clear" | Reset all fields |
| PF5 | "Copy Last Tran." | `GET /api/v1/transactions/last`; populate all form fields from response |

#### 4.13.3 Copy Last Transaction (PF5)

Calls a dedicated endpoint that returns the most recently added transaction for the current user session. Pre-fills all input fields (excluding confirmation) to facilitate re-entry.

---

### 4.14 User List — COUSR00 (BMS map COUSR0A)

**Route:** `/admin/users`
**Page file:** `src/app/admin/users/page.tsx`
**API calls:** `GET /api/v1/users?user_id=&page=&per_page=10`
**COBOL program:** COUSR00C
**Access:** Admin only

#### 4.14.1 Fields

**Search:**

| BMS Field | React Field | Notes |
|-----------|------------|-------|
| USRIDIN | `userIdFilter` | Optional 8-char filter |
| PAGENUM | (pagination state) | Display-only |

**List rows (10 rows):**

| BMS Fields | React Display | Notes |
|-----------|--------------|-------|
| SEL0001–SEL0010 | Action dropdown per row | U=Update, D=Delete |
| USRID01–USRID10 | User ID column | ASKIP FSET |
| FNAME01–FNAME10 | First name column | ASKIP FSET |
| LNAME01–LNAME10 | Last name column | ASKIP FSET |
| UTYPE01–UTYPE10 | Type column (A/U) | ASKIP FSET |

#### 4.14.2 Row Actions

The BMS selector accepts `U` (update) or `D` (delete). In the modern UI, each row has an action dropdown or two buttons: "Update" (navigates to `/admin/users/update?userId={id}`) and "Delete" (navigates to `/admin/users/delete?userId={id}`).

#### 4.14.3 Actions

| BMS Key | Button Label | Handler |
|---------|-------------|---------|
| ENTER | "Search" | Fetch with filter; page=1 |
| PF3 | "Back" | Navigate to `/admin/menu` |
| PF7 | "Previous Page" | page - 1 |
| PF8 | "Next Page" | page + 1 |

---

### 4.15 Add User — COUSR01 (BMS map COUSR1A)

**Route:** `/admin/users/new`
**Page file:** `src/app/admin/users/new/page.tsx`
**API calls:** `POST /api/v1/users`
**COBOL program:** COUSR01C
**Access:** Admin only

#### 4.15.1 Fields

| BMS Field | React Field | Type | Constraints | Notes |
|-----------|------------|------|-------------|-------|
| FNAME | `firstName` | text | maxLength=20; required | autoFocus (IC) |
| LNAME | `lastName` | text | maxLength=20; required | |
| USERID | `userId` | text | exactly 8 chars; required; unique | |
| PASSWD | `password` | password input | maxLength=8; required; DRK → type=password | Masked display |
| USRTYPE | `userType` | text | A or U; required | |

#### 4.15.2 Actions

| BMS Key | Button Label | Handler |
|---------|-------------|---------|
| ENTER | "Add User" | `POST /api/v1/users`; show success message; clear form |
| PF3 | "Back" | Navigate to `/admin/menu` without creating user |
| PF4 | "Clear" | Reset all fields |
| PF12 | "Exit" | Navigate to `/admin/menu` |

#### 4.15.3 Validation

```typescript
const addUserSchema = z.object({
  firstName: z.string().min(1, 'First Name cannot be empty').max(20),
  lastName: z.string().min(1, 'Last Name cannot be empty').max(20),
  userId: z.string().length(8, 'User ID must be exactly 8 characters'),
  password: z.string().min(1, 'Password cannot be empty').max(8),
  userType: z.enum(['A', 'U'], { errorMap: () => ({ message: 'User Type must be A or U' }) }),
});
```

---

### 4.16 Update User — COUSR02 (BMS map COUSR2A)

**Route:** `/admin/users/update`
**Page file:** `src/app/admin/users/update/page.tsx`
**API calls:** `GET /api/v1/users/{user_id}`, `PUT /api/v1/users/{user_id}`
**COBOL program:** COUSR02C
**Access:** Admin only

#### 4.16.1 Two-Phase Pattern

Phase 1: Enter user ID → ENTER to look up user → display editable fields.
Phase 2: Modify fields → PF5 to save (or PF3 to save-and-exit).

This mirrors the COBOL two-phase ENTER (lookup) then PF5 (save) workflow.

#### 4.16.2 Fields

| BMS Field | React Field | Type | Phase | Notes |
|-----------|------------|------|-------|-------|
| USRIDINI | `userId` | text | 1 | Lookup key; maxLength=8 |
| FNAMEI | `firstName` | text | 2 | Editable; required; maxLength=20 |
| LNAMEI | `lastName` | text | 2 | Editable; required; maxLength=20 |
| PASSWDI | `password` | password | 2 | Editable; DRK → type=password; required |
| USRTYPEI | `userType` | text | 2 | Editable; A or U; required |

**Field-level change detection:** Track original values from lookup. On save, only submit if at least one field differs. If no changes: display "Please modify to update..." message in orange/warning color (maps to DFHRED).

#### 4.16.3 Actions

| BMS Key | Button Label | Handler |
|---------|-------------|---------|
| ENTER | "Look Up" | `GET /api/v1/users/{userId}`; populate editable fields |
| PF3 | "Save & Exit" | If fields changed: `PUT /api/v1/users/{userId}`; then navigate back |
| PF4 | "Clear" | Reset all fields to blank |
| PF5 | "Save" | `PUT /api/v1/users/{userId}` if changed; stay on page |
| PF12 | "Cancel" | Navigate back without saving |

---

### 4.17 Delete User — COUSR03 (BMS map COUSR3A)

**Route:** `/admin/users/delete`
**Page file:** `src/app/admin/users/delete/page.tsx`
**API calls:** `GET /api/v1/users/{user_id}`, `DELETE /api/v1/users/{user_id}`
**COBOL program:** COUSR03C
**Access:** Admin only

#### 4.17.1 Two-Step Delete Pattern

Step 1: Enter/view user ID → ENTER to look up → display name and type for confirmation.
Step 2: PF5 to confirm deletion.

This is the exact preservation of the COBOL two-step delete: lookup then confirm.

#### 4.17.2 Fields

| BMS Field | React Field | Type | Notes |
|-----------|------------|------|-------|
| USRIDINI | `userId` | text | Input; maxLength=8; autoFocus |
| FNAMEI | `firstName` | read-only display | ASKIP — no password shown (unlike COUSR02) |
| LNAMEI | `lastName` | read-only display | ASKIP |
| USRTYPEI | `userType` | read-only display | ASKIP |

**No password field:** COUSR03 deliberately omits the password. COUSR3A BMS map has no PASSWDI field. This is preserved — password is NOT displayed on the delete confirmation screen.

#### 4.17.3 Actions

| BMS Key | Button Label | Handler |
|---------|-------------|---------|
| ENTER | "Look Up" | `GET /api/v1/users/{userId}`; display name/type read-only |
| PF3 | "Back" | Navigate back without deleting |
| PF4 | "Clear" | Reset all fields |
| PF5 | "Confirm Delete" | `DELETE /api/v1/users/{userId}`; display success; clear form |
| PF12 | "Cancel" | Navigate to `/admin/menu` without deleting |

#### 4.17.4 Pre-population from User List

When navigating from `/admin/users` with `userId` query param (analogous to CDEMO-CU03-USR-SELECTED), auto-trigger the lookup on page mount. This matches the COBOL first-entry auto-lookup behavior.

---

### 4.18 Authorization Summary — COPAU00 (BMS map COPAU0A)

**Route:** `/authorizations`
**Page file:** `src/app/authorizations/page.tsx`
**API calls:** `GET /api/v1/authorizations?account_id=&page=&per_page=5`
**COBOL program:** COPAUS0C

#### 4.18.1 Layout Description

Account ID search at top. Account/customer header information. Financial summary panel. Authorization list (5 rows per page). Paging.

#### 4.18.2 Account Summary Fields (all read-only after lookup)

| BMS Field | React Display Label | Notes |
|-----------|---------------------|-------|
| ACCTID | Search input | autoFocus |
| CNAME | Customer Name | |
| CUSTID | Customer ID | |
| ADDR001 | Address Line 1 | |
| ADDR002 | Address Line 2 | |
| ACCSTAT | Account Status | |
| PHONE1 | Phone | |
| APPRCNT | Approved Authorization Count | |
| DECLCNT | Declined Authorization Count | |
| CREDLIM | Credit Limit | |
| CASHLIM | Cash Limit | |
| APPRAMT | Total Approved Amount | |
| CREDBAL | Credit Balance | |
| CASHBAL | Cash Balance | |
| DECLAMT | Total Declined Amount | |

#### 4.18.3 Authorization List Rows (5 rows)

| BMS Fields | React Display | Notes |
|-----------|--------------|-------|
| SEL0001–SEL0005 | Row click or "View" button | S → navigate to detail |
| TRNIDnn | Transaction ID | Blue text |
| PDATEnn | Date (MM/DD/YY) | |
| PTIMEnn | Time (HH:MM:SS) | |
| PTYPEnn | Type code | |
| PAPRVnn | A/D (Approved/Declined) | |
| PSTATnn | Status code | |
| PAMTnnn | Amount | Formatted |

#### 4.18.4 Actions

| BMS Key | Button Label | Handler |
|---------|-------------|---------|
| ENTER | "Search" | `GET /api/v1/authorizations?account_id={accountId}&page=1` |
| PF3 | "Back" | Navigate to `/menu` |
| PF7 | "Previous Page" | page - 1 |
| PF8 | "Next Page" | page + 1 |

---

### 4.19 Authorization Detail — COPAU01 (BMS map COPAU1A)

**Route:** `/authorizations/{auth_id}`
**Page file:** `src/app/authorizations/[authId]/page.tsx`
**API calls:** `GET /api/v1/authorizations/{auth_id}`, `PUT /api/v1/authorizations/{auth_id}/fraud`
**COBOL program:** COPAUS1C

#### 4.19.1 Layout Description

Fully read-only detail view. AUTHMTC (Match Status) and AUTHFRD (Fraud Status) displayed in red to draw attention. All fields are ASKIP.

#### 4.19.2 Fields (all read-only)

| BMS Field | Display Label | Special Styling |
|-----------|--------------|----------------|
| CARDNUM | Card # | Pink/magenta |
| AUTHDT | Auth Date | Pink/magenta |
| AUTHTM | Auth Time | Pink/magenta |
| AUTHRSP | Auth Response Code | Pink/magenta |
| AUTHRSN | Response Reason | Blue; resolved from inline table |
| AUTHCD | Auth Code | Blue |
| AUTHAMT | Amount | Blue |
| POSEMD | POS Entry Mode | Blue |
| AUTHSRC | Source | Blue |
| MCCCD | MCC Code | Blue |
| CRDEXP | Card Exp. Date | Blue |
| AUTHTYP | Auth Type | Blue |
| TRNID | Transaction ID | Blue |
| AUTHMTC | Match Status | **Red text** |
| AUTHFRD | Fraud Status | **Red text**; 'FRAUD' or 'REMOVED' |
| MERNAME | Merchant Name | Blue |
| MERID | Merchant ID | Blue |
| MERCITY | Merchant City | Blue |
| MERST | Merchant State | Blue |
| MERZIP | Merchant ZIP | Blue |

#### 4.19.3 Actions

| BMS Key | Button Label | Handler |
|---------|-------------|---------|
| PF3 | "Back" | Navigate to `/authorizations` (summary list) |
| PF5 | "Mark/Remove Fraud" | `PUT /api/v1/authorizations/{authId}/fraud` with toggle request; refresh display |
| PF8 | "Next Auth" | Navigate to next authorization for the same account |

**Fraud toggle:** `PUT /api/v1/authorizations/{authId}/fraud` with body `{"action": "toggle"}`. On success, re-fetch and update AUTHFRD display field. Implements the COPAUS1C F5 → COPAUS2C LINK pattern.

---

### 4.20 Transaction Type List — COTRTLI (BMS map CTRTLIA)

**Route:** `/admin/transaction-types`
**Page file:** `src/app/admin/transaction-types/page.tsx`
**API calls:** `GET /api/v1/transaction-types?type_code=&description=&page=&per_page=7`
**COBOL program:** COTRTLIC

#### 4.20.1 Fields

| BMS Field | React Field | Notes |
|-----------|------------|-------|
| TRTYPE | `typeCodeFilter` | 2-char optional filter; autoFocus (IC); numeric |
| TRDESC | `descriptionFilter` | 50-char optional LIKE filter |
| PAGENO | (pagination state) | Display-only |

**List rows (7 rows, BMS max; 8th row TRTSELA/TRTTYPA/TRTDSCA is always protected and never rendered):**

| BMS Fields | React Display | Notes |
|-----------|--------------|-------|
| TRTSEL1–7 | Action select per row | D=Delete, U=Update |
| TRTTYP1–7 | Type code | Always read-only (PROT); cannot be edited inline |
| TRTYPD1–7 | Description | Editable when row selected for update (UNPROT); read-only otherwise |

**Dynamic attribute management:** The COBOL program makes TRTYPDn editable (DFHBMFSE) when a row is selected for update. In React: render description as an `<input>` when `selectedRow === n && selectedAction === 'U'`; otherwise render as `<span>`.

#### 4.20.2 Actions

| BMS Key | Button Label | Handler |
|---------|-------------|---------|
| ENTER | "Search / Apply" | Apply filters; or confirm pending U/D action on selected row |
| PF2/F2 | "Add New" | Navigate to `/admin/transaction-types/edit` |
| PF3/F3 | "Exit" | Navigate to `/admin/menu` |
| PF7/F7 | "Page Up" | page - 1 |
| PF8/F8 | "Page Down" | page + 1 |
| PF10/F10 | "Confirm" | Execute pending DELETE (`DELETE /api/v1/transaction-types/{code}`) or UPDATE (`PUT /api/v1/transaction-types/{code}`) |

#### 4.20.3 Inline Edit State Machine

The COBOL program uses a state machine triggered by D/U selection + ENTER + F10. In React:

1. User types D or U in a row's action column → store `{selectedRow, selectedAction}` in state
2. On "Apply" (ENTER): highlight row; show info message ("Delete HIGHLIGHTED row? Press Confirm to save" or "Update HIGHLIGHTED row. Press Confirm to save")
3. On "Confirm" (F10): execute the action via API
4. On success: reset selection; reload list with success message

---

### 4.21 Transaction Type Edit — COTRTUP (BMS map CTRTUPA)

**Route:** `/admin/transaction-types/edit`
**Page file:** `src/app/admin/transaction-types/edit/page.tsx`
**API calls:** `GET /api/v1/transaction-types/{type_code}`, `POST /api/v1/transaction-types`, `PUT /api/v1/transaction-types/{type_code}`, `DELETE /api/v1/transaction-types/{type_code}`
**COBOL program:** COTRTUPC

#### 4.21.1 Fields

| BMS Field | React Field | Notes |
|-----------|------------|-------|
| TRTYPCD | `typeCode` | 2-char numeric; autoFocus (IC); search key |
| TRTYDSC | `description` | 50-char; alphanumeric only |

#### 4.21.2 State Machine

The COBOL program has a 15-state machine (TTUP-CHANGE-ACTION). Map to React UI states:

| COBOL State | React UI State | TRTYPCD | TRTYDSC | Info Message | Visible Buttons |
|-------------|----------------|---------|---------|-------------|----------------|
| TTUP-DETAILS-NOT-FETCHED | `idle` | Editable | Locked | "Enter transaction type to be maintained" | ENTER, Exit |
| TTUP-DETAILS-NOT-FOUND | `not-found` | Editable | Locked | "Press Save to add. Cancel to cancel" | ENTER, Exit, Save, Cancel |
| TTUP-CREATE-NEW-RECORD | `creating` | Locked | Editable | "Enter new transaction type details." | ENTER, Exit, Cancel |
| TTUP-SHOW-DETAILS | `viewing` | Locked | Editable | "Update transaction type details shown." | ENTER, Exit, Delete, Cancel |
| TTUP-CHANGES-OK-NOT-CONFIRMED | `save-pending` | Locked | Locked | "Changes validated. Press Save to save" | ENTER, Exit, Save, Cancel |
| TTUP-CONFIRM-DELETE | `delete-pending` | Locked | Locked | "Delete this record? Press Delete to confirm" | Exit, Delete, Cancel |
| TTUP-DELETE-DONE | `deleted` | Editable | Locked | (reset to idle) | ENTER, Exit |
| TTUP-CHANGES-OKAYED-AND-DONE | `saved` | Locked | Locked | "Changes committed to database" | ENTER, Exit |

#### 4.21.3 Actions

| BMS Key | Button Label | Available In State | Handler |
|---------|-------------|------------------|---------|
| ENTER | "Process" | All except delete-pending | Validate; search/advance state |
| PF3/F3 | "Exit" | Always | Navigate to `/admin/transaction-types` or `/admin/menu` |
| PF4/F4 | "Delete" | viewing, delete-pending | Request delete (viewing → delete-pending); confirm delete (delete-pending → `DELETE /api/v1/transaction-types/{code}`) |
| PF5/F5 | "Save" | not-found, save-pending | Create (not-found → `POST /api/v1/transaction-types`); save confirmed (save-pending → `PUT /api/v1/transaction-types/{code}`) |
| PF12/F12 | "Cancel" | not-found, viewing, save-pending, delete-pending, creating | Reset/cancel action; return to appropriate state |

**F6/PF6 (Add):** Not implemented (BMS defines FKEY06 as DRK but COTRTUPC never activates it). Not rendered.

---

## 5. Navigation Flow Diagram

```
/login
  └── (user) → /menu
        ├── 1 → /accounts/view → /accounts/update
        ├── 2 → /accounts/update
        ├── 3 → /cards/view → /cards/update
        ├── 4 → /cards/list → /cards/view or /cards/update
        ├── 5 → /transactions/view → /transactions/add
        ├── 6 → /transactions/add
        ├── 7 → /transactions/list → /transactions/view
        ├── 8 → /billing/payment
        └── 9 → /reports/transactions

  └── (admin) → /admin/menu
        ├── 1 → /admin/users → /admin/users/update or /admin/users/delete
        ├── 2 → /admin/users/new
        ├── 3 → /admin/users/update
        ├── 4 → /admin/users/delete
        ├── 5 → /admin/transaction-types → /admin/transaction-types/edit
        └── 6 → /admin/transaction-types/edit

/authorizations (accessible from main menu for regular users)
  └── /authorizations/{authId}
```

---

## 6. Form State Management Strategy

### 6.1 React Hook Form + Zod Integration

All forms use `react-hook-form` with `zodResolver`. This maps directly to the BMS FSET pattern: all form values remain in controlled state and are always available for submission (equivalent to FSET forcing retransmission).

```typescript
// Pattern for all forms
const { register, handleSubmit, formState: { errors }, reset, setValue } = useForm({
  resolver: zodResolver(formSchema),
  defaultValues: { /* initial BMS LOW-VALUES or SPACES */ }
});
```

### 6.2 Two-Phase Screen Pattern

For screens with lookup-then-action patterns (COBIL00, COUSR02, COUSR03, COACTUP, COCRDUP):

```typescript
type ScreenPhase = 'lookup' | 'action';

const [phase, setPhase] = useState<ScreenPhase>('lookup');
const [lookupResult, setLookupResult] = useState<T | null>(null);

// Phase 1: lookup only inputs enabled
// Phase 2: action inputs enabled, lookup key locked
```

### 6.3 Pagination State

```typescript
interface PaginationState {
  page: number;
  perPage: number;
  totalPages: number;
  totalCount: number;
}
```

All list screens use this structure. `perPage` matches the BMS screen capacity (5 for auth, 7 for cards and transaction types, 10 for transactions and users).

### 6.4 Dirty-Field Change Detection

For COUSR02C (update user) and COACTUPC (update account) which implement field-level change detection:

```typescript
const [originalValues, setOriginalValues] = useState<T | null>(null);

const hasChanges = (current: T): boolean => {
  if (!originalValues) return false;
  return Object.keys(current).some(k => current[k] !== originalValues[k]);
};
// If !hasChanges: display warning message; do not submit
```

---

## 7. API Client Layer

**File:** `src/lib/api.ts`

The API client is a typed wrapper around `fetch` that handles JWT bearer token injection, error parsing, and response typing. All API calls from React components go through this client.

```typescript
// Pattern
const apiClient = {
  get: async <T>(path: string): Promise<T> => { ... },
  post: async <T>(path: string, body: unknown): Promise<T> => { ... },
  put: async <T>(path: string, body: unknown): Promise<T> => { ... },
  delete: async <T>(path: string): Promise<T> => { ... },
};
```

All responses follow the format `{ data: T }` on success and `{ error_code: string, message: string, details: [] }` on error, matching the API specification.

---

## 8. Authentication and Route Protection

**File:** `src/middleware.ts`

Next.js middleware intercepts all requests to protected routes. Reads JWT from cookie (or Authorization header for API routes). Validates token. Redirects to `/login` if invalid.

Admin-only routes (`/admin/*`) additionally check `userType === 'A'` in the JWT payload. Redirect to `/menu` with error if type is `U`.

```typescript
// Middleware checks
const protectedRoutes = ['/menu', '/admin', '/accounts', '/cards', '/transactions', ...];
const adminOnlyRoutes = ['/admin/*'];
```

---

## 9. Error Handling Conventions

### 9.1 Form-Level Errors

Inline Zod validation errors appear below each field as `<p className="text-red-600 text-sm">` elements. These are generated by `react-hook-form` before any API call.

### 9.2 API Errors

API errors populate the ERRMSG bar at the bottom of the page (red, high-intensity, full-width). This directly matches the BMS ERRMSG field behavior.

Error color variants:
- `red` — Validation errors, not found, system errors (`DFHRED`)
- `green` — Success confirmation messages (`DFHGREEN`)
- `neutral` — Informational prompts ("Press PF5 to save...") (`DFHNEUTR`)

### 9.3 Error Mapping

| COBOL Condition | HTTP Status | React Display |
|-----------------|-------------|--------------|
| USRIDINI blank | 400 | Red ERRMSG: "User ID can NOT be empty..." |
| READ NOTFND | 404 | Red ERRMSG: "User ID NOT found..." |
| REWRITE conflict | 409 | Red ERRMSG: "Record changed. Please review" |
| READ OTHER | 500 | Red ERRMSG: "Unable to lookup User..." |
| Invalid AID key | (N/A) | Red ERRMSG: "Invalid key pressed" |

---

## 10. Component Library

**File:** `src/components/ui/`

| Component | BMS Equivalent | Usage |
|-----------|---------------|-------|
| `FormField` | DFHMDF UNPROT field | Labeled input with error display |
| `ReadOnlyField` | DFHMDF ASKIP field | Label + value display |
| `PasswordField` | DFHMDF DRK UNPROT | Input with type=password masking |
| `ActionBar` | Row 24 function key legend | Horizontal button row at bottom of screen |
| `DataTable` | BMS list rows | Sortable table with pagination |
| `PageNumber` | PAGENUM display field | "Page X of Y" indicator |
| `StatusBadge` | Single-char status fields | Y/N, A/D styled badges |
| `CurrencyDisplay` | PICOUT='+ZZZ,ZZZ,ZZZ.99' | Signed currency formatter |
| `MessageBar` | ERRMSG row 23 | Full-width colored message |
| `InfoMessage` | INFOMSG | Centered informational message |
| `ConfirmDialog` | Y/N CONFIRM fields | Modal dialog for destructive actions |

---

## 11. Responsive Design Notes

The original 3270 terminal screens are fixed-width 80-column layouts. The modern web UI adapts these to responsive layouts:

- Desktop (≥1024px): Multi-column layouts matching the original side-by-side field arrangement (e.g., account view with dates on left, financials on right)
- Tablet (768–1023px): Two-column layout with some field groups stacked
- Mobile (<768px): Single-column stacked layout

All list screens use horizontal scroll on small viewports to preserve column alignment.

---

## 12. TypeScript Types

**File:** `src/types/index.ts`

All TypeScript interfaces are derived from the Pydantic schemas defined in the API specification document (`02-api-specification.md`). Each screen's form state has a corresponding interface.

Key shared types:

```typescript
interface User {
  userId: string;
  firstName: string;
  lastName: string;
  userType: 'A' | 'U';
}

interface Account {
  accountId: string;
  customerId: string;
  accountStatus: 'Y' | 'N';
  creditLimit: number;
  cashLimit: number;
  currentBalance: number;
  // ... all VSAM ACCTDAT fields
}

interface CreditCard {
  cardNumber: string;
  accountId: string;
  cardName: string;
  activeStatus: 'Y' | 'N';
  expiryDate: string;
  expiryDay: number;  // hidden EXPDAY field preserved in type
}

interface Transaction {
  transactionId: string;
  cardNumber: string;
  transactionTypeCode: string;
  categoryCode: string;
  source: string;
  description: string;
  amount: number;
  originalDate: string;
  processingDate: string;
  merchantId: string;
  merchantName: string;
  merchantCity: string;
  merchantZip: string;
}

interface Authorization {
  authId: string;
  accountId: string;
  transactionId: string;
  cardNumber: string;
  authDate: string;
  authTime: string;
  authResponse: string;
  authCode: string;
  amount: number;
  matchStatus: 'P' | 'D' | 'E' | 'M';
  fraudStatus: 'F' | 'R' | null;
  // merchant fields
}

interface TransactionType {
  typeCode: string;
  description: string;
}
```
