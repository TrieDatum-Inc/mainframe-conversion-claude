# API Specification: FastAPI REST Endpoints

## Document Purpose

Defines every FastAPI REST endpoint for the CardDemo modernization, with Pydantic model definitions, business logic mappings from COBOL PROCEDURE DIVISION paragraphs, validation rules, and error response formats.

---

## 1. Standard Conventions

### Base URL
```
/api/v1
```

### Authentication Header
```
Authorization: Bearer <jwt_access_token>
```

### Standard Error Response
```json
{
  "error_code": "USER_NOT_FOUND",
  "message": "User ID NOT found in the system",
  "details": []
}
```

### Pagination Response Envelope
```json
{
  "items": [...],
  "page": 1,
  "page_size": 10,
  "total_count": 125,
  "has_next": true,
  "has_previous": false,
  "first_item_key": "USERID01",
  "last_item_key": "USERID10"
}
```

### HTTP Status Code Mapping

| COBOL Condition | HTTP Status |
|----------------|-------------|
| RESP=NORMAL / success | 200 OK or 201 Created |
| RESP=NOTFND on READ | 404 Not Found |
| Blank required field | 422 Unprocessable Entity |
| RESP=DUPKEY/DUPREC on WRITE | 409 Conflict |
| RESP=OTHER / unknown error | 500 Internal Server Error |
| EIBCALEN=0 (unauthenticated) | 401 Unauthorized |
| Non-admin accessing admin function | 403 Forbidden |
| Invalid input (validation failure) | 422 Unprocessable Entity |

---

## 2. Authentication Module
**COBOL Source**: COSGN00C (Transaction: COSG)

### `POST /api/v1/auth/login`

**COBOL Paragraph Mapping**: MAIN-PARA → READ-USER-SEC-FILE → compare passwords

**Request Body** (`LoginRequest`):
```python
class LoginRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=8, description="USERIDI field from COSGN0A map")
    password: str = Field(..., min_length=1, max_length=72, description="PASSWDI field from COSGN0A map — DRK field, 8 char original")
```

**Response** (`LoginResponse`):
```python
class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    user_id: str
    user_type: str               # 'A' or 'U'
    first_name: str
    last_name: str
    redirect_to: str             # '/admin/menu' for type='A', '/menu' for type='U'
```

**Business Logic** (maps COSGN00C PROCEDURE DIVISION):
1. Validate USERIDI not blank (COSGN00C: `IF USERIDI = SPACES`)
2. Validate PASSWDI not blank
3. Read `users` table by `user_id` (replaces `EXEC CICS READ DATASET(USRSEC)`)
4. If not found: return 401 with message "User ID NOT found..."
5. Verify `bcrypt.verify(password, stored_hash)` (replaces `IF PASSWDI = SEC-USR-PWD`)
6. If mismatch: return 401 with message "Invalid Password..."
7. Determine redirect: if `user_type='A'` → `/admin/menu` else `/menu` (replaces XCTL logic)
8. Generate JWT with claims: `sub=user_id`, `user_type=user_type`, `exp=now+3600`
9. Return `LoginResponse`

**Error Responses**:
| Condition | error_code | message |
|-----------|-----------|---------|
| user_id blank | USERID_REQUIRED | "User ID can NOT be empty" |
| password blank | PASSWORD_REQUIRED | "Password can NOT be empty" |
| User not found | USER_NOT_FOUND | "User ID NOT found in the system" |
| Wrong password | INVALID_CREDENTIALS | "Invalid credentials provided" |

---

### `POST /api/v1/auth/logout`

Invalidates the JWT token (add to deny-list or use short TTL pattern).

**Response**: `204 No Content`

---

## 3. User Management Module
**COBOL Source**: COUSR00C, COUSR01C, COUSR02C, COUSR03C
**Access**: Admin only (`user_type='A'` JWT claim required)

### Pydantic Models

```python
class UserBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=20)
    last_name: str = Field(..., min_length=1, max_length=20)
    user_type: Literal['A', 'U'] = Field(..., description="A=Admin, U=User")

class UserCreateRequest(UserBase):
    """Maps COUSR01C PROCESS-ENTER-KEY: all 5 fields required"""
    user_id: str = Field(..., min_length=1, max_length=8, pattern=r'^[A-Za-z0-9]{1,8}$')
    password: str = Field(..., min_length=1, max_length=72)  # original was 8 char; extended

class UserUpdateRequest(BaseModel):
    """Maps COUSR02C UPDATE-USER-INFO: all 4 editable fields"""
    first_name: str = Field(..., min_length=1, max_length=20)
    last_name: str = Field(..., min_length=1, max_length=20)
    password: Optional[str] = Field(None, min_length=1, max_length=72)  # blank = no change
    user_type: Literal['A', 'U']

class UserResponse(UserBase):
    user_id: str
    created_at: datetime
    updated_at: datetime
    # NOTE: password_hash is NEVER included in any response

class UserListResponse(BaseModel):
    items: List[UserResponse]
    page: int
    page_size: int
    total_count: int
    has_next: bool
    has_previous: bool
    first_item_key: Optional[str]
    last_item_key: Optional[str]
```

### `GET /api/v1/users`
**COBOL Source**: COUSR00C POPULATE-USER-DATA (STARTBR/READNEXT/READPREV pattern)

**Query Parameters**:
- `user_id_filter` (optional, max 8 chars): maps to USRIDINI → STARTBR RIDFLD
- `page` (default 1)
- `page_size` (default 10, max 10): COUSR00C shows exactly 10 rows per page

**Business Logic**:
1. If `user_id_filter` provided: `WHERE user_id >= filter ORDER BY user_id ASC` (replaces STARTBR with filter key)
2. Else: `ORDER BY user_id ASC` (replaces STARTBR with LOW-VALUES)
3. Paginate; set `has_next` from look-ahead count (replaces look-ahead READNEXT + CDEMO-CU00-NEXT-PAGE-FLG)
4. Return user list (user_id, first_name, last_name, user_type — NO password)

**Response**: `UserListResponse`

---

### `POST /api/v1/users`
**COBOL Source**: COUSR01C PROCESS-ENTER-KEY → WRITE-USER-SEC-FILE

**Request Body**: `UserCreateRequest`

**Business Logic** (maps COUSR01C validation order: FNAME → LNAME → USERID → PASSWD → USRTYPE):
1. Validate `first_name` not blank (→ 422 "First Name can NOT be empty...")
2. Validate `last_name` not blank (→ 422 "Last Name can NOT be empty...")
3. Validate `user_id` not blank (→ 422 "User ID can NOT be empty...")
4. Validate `password` not blank (→ 422 "Password can NOT be empty...")
5. Validate `user_type` in ('A', 'U') (→ 422 "User Type can NOT be empty...")
6. Check `user_id` uniqueness: `SELECT 1 FROM users WHERE user_id = ?`
7. If exists: return 409 "User ID already exist..." (maps DUPKEY/DUPREC)
8. Hash password with bcrypt
9. INSERT into `users`
10. Return 201 `UserResponse` (no password field)

---

### `GET /api/v1/users/{user_id}`
**COBOL Source**: COUSR02C PROCESS-ENTER-KEY → READ-USER-SEC-FILE (also used by COUSR03C)

**Response**: `UserResponse`

**Business Logic**:
1. SELECT from `users` WHERE user_id = ?
2. If not found: 404 "User ID NOT found..."
3. Return user (no password)

---

### `PUT /api/v1/users/{user_id}`
**COBOL Source**: COUSR02C UPDATE-USER-INFO → UPDATE-USER-SEC-FILE

**Request Body**: `UserUpdateRequest`

**Business Logic** (maps COUSR02C field-level change detection):
1. GET current record (COUSR02C calls READ-USER-SEC-FILE before UPDATE)
2. If not found: 404 "User ID NOT found..."
3. Validate `first_name` not blank (→ 422)
4. Validate `last_name` not blank (→ 422)
5. Validate `user_type` in ('A', 'U') (→ 422)
6. Compare each field to current value (maps WS-USR-MODIFIED flag):
   - `first_name` changed? → mark modified
   - `last_name` changed? → mark modified
   - `password` provided and non-blank? → hash and mark modified
   - `user_type` changed? → mark modified
7. If no fields modified: return 422 "Please modify to update..." (maps USR-MODIFIED-NO path)
8. UPDATE `users` SET modified fields, updated_at = NOW()
9. Return 200 `UserResponse`

---

### `DELETE /api/v1/users/{user_id}`
**COBOL Source**: COUSR03C DELETE-USER-INFO → DELETE-USER-SEC-FILE

**Business Logic** (maps COUSR03C two-step: GET + DELETE):
1. SELECT from `users` WHERE user_id = ? (maps READ-USER-SEC-FILE before DELETE)
2. If not found: 404 "User ID NOT found..."
3. Return user details in response body for confirmation (maps COUSR3A display of name/type)
4. Execute DELETE from `users` WHERE user_id = ?
5. If delete fails (concurrent delete): 404 "User ID NOT found..."
6. Return 200 `{"message": "User [ID] has been deleted successfully"}`

**Note**: COUSR03C original bug ("Unable to Update User" on delete failure) is corrected here to "Unable to delete user".

---

## 4. Account Module
**COBOL Source**: COACTVWC, COACTUPC

### Pydantic Models

```python
class AccountViewResponse(BaseModel):
    """Maps COACTVWC screen fields — all display-only"""
    account_id: int                          # ACCTSID 11-digit
    active_status: str                       # ACSTTUS Y/N
    open_date: Optional[date]                # ADTOPEN single field
    expiration_date: Optional[date]          # AEXPDT
    reissue_date: Optional[date]             # AREISDT
    credit_limit: Decimal                    # ACRDLIM +ZZZ,ZZZ,ZZZ.99
    cash_credit_limit: Decimal               # ACSHLIM
    current_balance: Decimal                 # ACURBAL
    curr_cycle_credit: Decimal               # ACRCYCR
    curr_cycle_debit: Decimal                # ACRCYDB
    group_id: Optional[str]                  # AADDGRP
    customer: CustomerDetailResponse         # customer section rows 11-20

class CustomerDetailResponse(BaseModel):
    customer_id: int                         # ACSTNUM
    ssn_masked: str                          # ACSTSSN — masked: XXX-XX-1234
    date_of_birth: Optional[date]            # ACSTDOB
    fico_score: Optional[int]                # ACSTFCO
    first_name: str                          # ACSFNAM
    middle_name: Optional[str]               # ACSMNAM
    last_name: str                           # ACSLNAM
    address_line_1: Optional[str]            # ACSADL1
    address_line_2: Optional[str]            # ACSADL2
    city: Optional[str]                      # ACSCITY
    state_code: Optional[str]                # ACSSTTE
    zip_code: Optional[str]                  # ACSZIPC
    country_code: Optional[str]              # ACSCTRY
    phone_1: Optional[str]                   # ACSPHN1 single field (view) vs ACSPH1A/B/C (update)
    phone_2: Optional[str]                   # ACSPHN2
    government_id_ref: Optional[str]         # ACSGOVT
    eft_account_id: Optional[str]            # ACSEFTC
    primary_card_holder: str                 # ACSPFLG Y/N

class AccountUpdateRequest(BaseModel):
    """Maps COACTUPC editable fields — all 15+ validations preserved"""
    active_status: Literal['Y', 'N']
    open_date: date
    expiration_date: date
    reissue_date: date
    credit_limit: Decimal = Field(..., ge=0, decimal_places=2)
    cash_credit_limit: Decimal = Field(..., ge=0, decimal_places=2)
    current_balance: Decimal = Field(..., decimal_places=2)
    curr_cycle_credit: Decimal = Field(..., ge=0, decimal_places=2)
    curr_cycle_debit: Decimal = Field(..., ge=0, decimal_places=2)
    group_id: Optional[str] = Field(None, max_length=10)
    customer: CustomerUpdateRequest

class CustomerUpdateRequest(BaseModel):
    customer_id: int
    first_name: str = Field(..., min_length=1, max_length=25, pattern=r'^[A-Za-z\s\-\']+$')  # alpha only
    middle_name: Optional[str] = Field(None, max_length=25, pattern=r'^[A-Za-z\s\-\']*$')
    last_name: str = Field(..., min_length=1, max_length=25, pattern=r'^[A-Za-z\s\-\']+$')   # alpha only
    address_line_1: Optional[str] = Field(None, max_length=50)
    address_line_2: Optional[str] = Field(None, max_length=50)
    city: Optional[str] = Field(None, max_length=50)
    state_code: Optional[str] = Field(None, max_length=2)
    zip_code: Optional[str] = Field(None, max_length=10)
    country_code: Optional[str] = Field(None, max_length=3)
    phone_1: Optional[str] = Field(None, pattern=r'^\d{3}-\d{3}-\d{4}$')  # NNN-NNN-NNNN
    phone_2: Optional[str] = Field(None, pattern=r'^\d{3}-\d{3}-\d{4}$')
    ssn_part1: str = Field(..., pattern=r'^\d{3}$')    # ACTSSN1 — 3 digits
    ssn_part2: str = Field(..., pattern=r'^\d{2}$')    # ACTSSN2 — 2 digits
    ssn_part3: str = Field(..., pattern=r'^\d{4}$')    # ACTSSN3 — 4 digits
    date_of_birth: date
    fico_score: Optional[int] = Field(None, ge=300, le=850)
    government_id_ref: Optional[str] = Field(None, max_length=20)
    eft_account_id: Optional[str] = Field(None, max_length=10)
    primary_card_holder: Literal['Y', 'N']
```

### `GET /api/v1/accounts/{account_id}`
**COBOL Source**: COACTVWC MAIN-PARA → READ-ACCT-BY-ACCT-ID → READ-CUST-BY-CUST-ID → READ-CARD-BY-ACCT-AIX

**Business Logic**:
1. Validate `account_id` is 11-digit non-zero numeric (maps COACTVWC/COACTUPC validation)
2. SELECT from `accounts` WHERE account_id = ? (READ ACCTDAT by key)
3. If not found: 404
4. SELECT from `account_customer_xref` JOIN `customers` WHERE account_id = ? (READ CUSTDAT via account)
5. Return `AccountViewResponse` with all financial fields and customer detail

---

### `PUT /api/v1/accounts/{account_id}`
**COBOL Source**: COACTUPC UPDATE-ACCOUNT-INFO — 15+ validation rules

**Request Body**: `AccountUpdateRequest`

**Business Logic** (preserves all COACTUPC validations):
1. Read current account record (READ UPDATE equivalent — but use optimistic lock via `updated_at`)
2. If not found: 404
3. Validate `active_status` = 'Y' or 'N'
4. Validate `open_date` via `datetime.strptime` (replaces CSUTLDTC call)
5. Validate `expiration_date` is a valid future date
6. Validate `reissue_date` is a valid date
7. Validate `credit_limit >= 0` (signed numeric)
8. Validate `cash_credit_limit >= 0 AND <= credit_limit`
9. Validate `current_balance` is numeric
10. Validate customer `first_name` / `middle_name` / `last_name` alpha-only (INSPECT CONVERTING equivalent)
11. Validate SSN: part1 not in ('000', '666') and not in range '900'-'999' (replaces COACTUPC SSN validation)
12. Validate DOB via `datetime.strptime`
13. Validate FICO 300–850
14. Validate phone format NNN-NNN-NNNN
15. Validate `primary_card_holder` = 'Y' or 'N'
16. Check if any field changed (replaces WS-DATACHANGED-FLAG); if none → 422 "No changes detected"
17. UPDATE `accounts` and `customers` in transaction
18. Return 200 `AccountViewResponse`

---

## 5. Billing Module
**COBOL Source**: COBIL00C

### Pydantic Models

```python
class BillingBalanceResponse(BaseModel):
    account_id: int
    current_balance: Decimal             # CURBAL displayed on COBIL0A map

class BillPaymentRequest(BaseModel):
    account_id: int
    confirm: Literal['Y'] = Field(..., description="Must be Y to execute payment (CONFIRMI field)")

class BillPaymentResponse(BaseModel):
    account_id: int
    previous_balance: Decimal
    new_balance: Decimal                 # Always 0 after payment (COBIL00C sets ACCT-CURR-BAL = 0)
    transaction_id: str
    message: str
```

### `GET /api/v1/billing/{account_id}/balance`
**COBOL Source**: COBIL00C Phase 1 (account lookup and display)

**Business Logic**:
1. Validate `account_id` not blank
2. SELECT `current_balance` FROM `accounts` WHERE account_id = ?
3. If not found: 404
4. Return `BillingBalanceResponse`

---

### `POST /api/v1/billing/{account_id}/payment`
**COBOL Source**: COBIL00C Phase 2 (CONFIRMI='Y' processing)

**Request Body**: `BillPaymentRequest`

**Business Logic** (maps COBIL00C DELETE-ACCT-PAYMENT / WRITE-TRAN-FILE):
1. Read account with SELECT FOR UPDATE (pessimistic lock to prevent double payment)
2. If not found: 404
3. Capture `previous_balance = account.current_balance`
4. Generate new `transaction_id` via PostgreSQL sequence
5. INSERT into `transactions`:
   - type_code = '02' (TRAN-TYPE-CD = 2)
   - transaction_category_code = '0002' (TRAN-CAT-CD = 2)
   - transaction_source = 'POS TERM' (hardcoded in COBIL00C)
   - description = 'BILL PAYMENT - ONLINE' (hardcoded)
   - merchant_id = '999999999' (hardcoded)
   - amount = `previous_balance` (payment amount)
6. UPDATE `accounts` SET current_balance = 0 (COBIL00C: ACCT-CURR-BAL = ZEROS)
7. Return `BillPaymentResponse`

---

## 6. Credit Card Module
**COBOL Source**: COCRDLIC, COCRDSLC, COCRDUPC

### Pydantic Models

```python
class CardListItem(BaseModel):
    card_number: str        # CRDNUMn — last 4 shown in UI
    account_id: int         # ACCTNOn
    active_status: str      # CRDSTSn

class CardListResponse(BaseModel):
    items: List[CardListItem]
    page: int
    page_size: int
    total_count: int
    has_next: bool
    has_previous: bool

class CardDetailResponse(BaseModel):
    card_number: str                 # CARDSID
    account_id: int                  # ACCTSID (protected on update screen)
    card_embossed_name: Optional[str] # CRDNAME
    active_status: str               # CRDSTCD Y/N
    expiration_month: int            # EXPMON 1-12
    expiration_year: int             # EXPYEAR 4-digit
    expiration_day: Optional[int]    # EXPDAY hidden field on COCRDUP map

class CardUpdateRequest(BaseModel):
    """Maps COCRDUPC editable fields only"""
    card_number: str = Field(..., min_length=16, max_length=16)
    card_embossed_name: str = Field(..., min_length=1, max_length=50)
    active_status: Literal['Y', 'N']
    expiration_month: int = Field(..., ge=1, le=12)        # EXPMON validation
    expiration_year: int = Field(..., ge=1950, le=2099)    # EXPYEAR validation
    expiration_day: Optional[int] = Field(None, ge=1, le=31)  # EXPDAY hidden field
    optimistic_lock_version: datetime = Field(..., description="updated_at from GET response — replaces CCUP-OLD-DETAILS snapshot")
```

### `GET /api/v1/cards`
**COBOL Source**: COCRDLIC POPULATE-USER-DATA (7 rows per page, STARTBR/READNEXT/READPREV)

**Query Parameters**:
- `account_id` (optional): filter by account
- `card_number` (optional): exact filter
- `page` (default 1), `page_size` (default 7, max 7)

**Business Logic**:
1. Apply optional filters (account_id and/or card_number — applied post-browse in COCRDLIC, moved to WHERE clause here)
2. Paginate 7 per page
3. Return `CardListResponse`

---

### `GET /api/v1/cards/{card_number}`
**COBOL Source**: COCRDSLC / COCRDUPC PROCESS-ENTER-KEY

**Business Logic**:
1. Validate `card_number` 16 digits
2. SELECT from `credit_cards` WHERE card_number = ?
3. If not found: 404
4. Return `CardDetailResponse`

---

### `PUT /api/v1/cards/{card_number}`
**COBOL Source**: COCRDUPC UPDATE-CARD (7-state machine)

**Request Body**: `CardUpdateRequest`

**Business Logic** (maps COCRDUPC validations):
1. Read current card record
2. If not found: 404
3. Check `optimistic_lock_version` == `card.updated_at` (replaces CCUP-OLD-DETAILS snapshot comparison)
4. If mismatch: 409 Conflict "Record changed by another user" (replaces COCRDUPC SYNCPOINT ROLLBACK on mismatch)
5. Validate `card_embossed_name` alpha-only (INSPECT CONVERTING)
6. Validate `expiration_month` 1–12
7. Validate `expiration_year` 1950–2099
8. UPDATE `credit_cards` SET updated fields
9. Return 200 `CardDetailResponse`

---

## 7. Transaction Module
**COBOL Source**: COTRN00C, COTRN01C, COTRN02C

### Pydantic Models

```python
class TransactionListItem(BaseModel):
    transaction_id: str
    original_date: date
    description: Optional[str]
    amount: Decimal

class TransactionDetailResponse(BaseModel):
    transaction_id: str              # TRNID
    card_number: str                 # CARDNUM
    transaction_type_code: str       # TTYPCD
    transaction_category_code: Optional[str]  # TCATCD
    transaction_source: Optional[str]         # TRNSRC
    description: Optional[str]               # TDESC
    amount: Decimal                          # TRNAMT
    original_date: Optional[date]            # TORIGDT
    processed_date: Optional[date]           # TPROCDT
    merchant_id: Optional[str]              # MID
    merchant_name: Optional[str]            # MNAME
    merchant_city: Optional[str]            # MCITY
    merchant_zip: Optional[str]             # MZIP

class TransactionCreateRequest(BaseModel):
    """Maps COTRN02C — account_id XOR card_number required"""
    account_id: Optional[int] = Field(None, description="ACTIDIN — mutually exclusive with card_number")
    card_number: Optional[str] = Field(None, min_length=16, max_length=16, description="CARDNIN")
    transaction_type_code: str = Field(..., min_length=1, max_length=2)
    transaction_category_code: Optional[str] = Field(None, max_length=4)
    transaction_source: Optional[str] = Field(None, max_length=10)
    description: str = Field(..., min_length=1, max_length=60)
    amount: Decimal = Field(..., description="Format: -99999999.99; must not be zero")
    original_date: date = Field(..., description="Format YYYY-MM-DD; validated via CSUTLDTC equivalent")
    processed_date: date = Field(..., description="Must be >= original_date")
    merchant_id: str = Field(..., min_length=1, max_length=9)
    merchant_name: str = Field(..., min_length=1, max_length=30)
    merchant_city: Optional[str] = Field(None, max_length=25)
    merchant_zip: Optional[str] = Field(None, max_length=10)
    confirm: Literal['Y'] = Field(..., description="CONFIRMI — must be Y to insert")

    @model_validator(mode='after')
    def validate_account_or_card(self) -> 'TransactionCreateRequest':
        if not self.account_id and not self.card_number:
            raise ValueError("Either account_id or card_number must be provided")
        if self.amount == 0:
            raise ValueError("Amount must not be zero")
        if self.processed_date < self.original_date:
            raise ValueError("Processed date must be >= original date")
        return self
```

### `GET /api/v1/transactions`
**COBOL Source**: COTRN00C (10 rows per page, STARTBR/READNEXT/READPREV)

**Query Parameters**:
- `tran_id_filter` (optional, 16 chars): maps TRNIDINI → STARTBR filter
- `page` (default 1), `page_size` (default 10, max 10)

**Response**: Paginated list with `transaction_id`, `original_date`, `description`, `amount`

---

### `GET /api/v1/transactions/{transaction_id}`
**COBOL Source**: COTRN01C PROCESS-ENTER-KEY → READ-TRANS-FILE

**Business Logic**:
1. Validate `transaction_id` not blank
2. SELECT from `transactions` WHERE transaction_id = ? (NO FOR UPDATE — bug fix: COTRN01C used READ UPDATE for display-only)
3. If not found: 404
4. Return `TransactionDetailResponse`

---

### `POST /api/v1/transactions`
**COBOL Source**: COTRN02C WRITE-PROCESSING

**Request Body**: `TransactionCreateRequest`

**Business Logic**:
1. Validate at least one of `account_id` or `card_number` provided
2. If `card_number` provided: look up account_id via `card_account_xref` (COTRN02C reads CCXREF)
3. If `account_id` provided: look up card(s) via `account_customer_xref` (COTRN02C reads CXACAIX AIX)
4. Validate account exists
5. Validate `transaction_type_code` exists in `transaction_types`
6. Validate `original_date` via Python datetime (replaces CSUTLDTC call)
7. Validate `processed_date >= original_date`
8. Validate `amount != 0`
9. Generate `transaction_id` via PostgreSQL sequence (replaces STARTBR+READPREV+ADD1 race condition)
10. INSERT into `transactions`
11. Return 201 `TransactionDetailResponse`

---

## 8. Report Module
**COBOL Source**: CORPT00C

### Pydantic Models

```python
class ReportRequestCreate(BaseModel):
    report_type: Literal['M', 'Y', 'C']   # MONTHLYI/YEARLYI/CUSTOMI
    start_date: Optional[date] = None      # SDTMM/SDTDD/SDTYYYY — required if type='C'
    end_date: Optional[date] = None        # EDTMM/EDTDD/EDTYYYY — required if type='C'
    confirm: Literal['Y']                  # CONFIRMI — must be Y

    @model_validator(mode='after')
    def validate_custom_dates(self) -> 'ReportRequestCreate':
        if self.report_type == 'C':
            if not self.start_date or not self.end_date:
                raise ValueError("Start and end dates required for custom report")
            if self.end_date < self.start_date:
                raise ValueError("End date must be >= start date")
        return self

class ReportRequestResponse(BaseModel):
    request_id: int
    report_type: str
    start_date: Optional[date]
    end_date: Optional[date]
    status: str
    requested_at: datetime
    message: str
```

### `POST /api/v1/reports/request`
**COBOL Source**: CORPT00C SUBMIT-REPORT-REQUEST (replaces WIRTE-JOBSUB-TDQ)

**Business Logic**:
1. Validate `confirm == 'Y'`
2. Validate dates if `report_type == 'C'`
3. If `report_type == 'M'`: derive start/end from current month
4. If `report_type == 'Y'`: derive start/end from current year
5. If `end_date` blank (as in CORPT00C): default to last day of prior month
6. INSERT into `report_requests` with status='PENDING'
7. Submit background task
8. Return 202 Accepted with `ReportRequestResponse`

---

## 9. Authorization Module
**COBOL Source**: COPAUS0C, COPAUS1C, COPAUS2C

### Pydantic Models

```python
class AuthorizationSummaryInfo(BaseModel):
    """Maps COPAU00 account/customer summary section"""
    account_id: int
    customer_name: str           # CNAMEO
    customer_id: int             # CUSTIDO
    address_line_1: str          # ADDR001O
    address_line_2: str          # ADDR002O
    account_status: str          # ACCSTATO
    phone: str                   # PHONE1O
    approval_count: int          # APPRCNTO
    decline_count: int           # DECLCNTO
    credit_limit: Decimal        # CREDLIMO
    cash_limit: Decimal          # CASHLIMO
    approved_amount: Decimal     # APPRAMTO
    credit_balance: Decimal      # CREDBALO
    cash_balance: Decimal        # CASHBALO
    declined_amount: Decimal     # DECLAMTO

class AuthorizationListItem(BaseModel):
    """Maps COPAU00 list row fields"""
    auth_id: int
    transaction_id: str          # TRNIDnnO
    auth_date: date              # PDATEnnO MM/DD/YY
    auth_time: time              # PTIMEnnO HH:MM:SS
    auth_type: str               # PTYPEnnO
    approval_status: str         # PAPRVnnO A/D
    match_status: str            # PSTATnnO P/D/E/M
    amount: Decimal              # PAMTnnnO

class AuthorizationDetailResponse(BaseModel):
    """Maps COPAU01 all display fields"""
    auth_id: int
    transaction_id: str
    card_number: str             # CARDNUMO
    auth_date: date              # AUTHDTO
    auth_time: time              # AUTHTMO
    auth_response_code: str      # AUTHRSPO
    decline_reason: Optional[str] # AUTHRSNO — from 10-entry inline table
    auth_code: Optional[str]     # AUTHCDO
    amount: Decimal              # AUTHAMTO
    pos_entry_mode: Optional[str] # POSEMDO
    auth_source: Optional[str]   # AUTHSRCO
    mcc_code: Optional[str]      # MCCCDO
    card_expiry: Optional[str]   # CRDEXPO
    auth_type: Optional[str]     # AUTHTYPO
    match_status: str            # AUTHMTCO P/D/E/M
    fraud_status: str            # AUTHFRDO FRAUD/REMOVED/NONE
    merchant_name: Optional[str] # MERNAMEO
    merchant_id: Optional[str]   # MERIDO
    merchant_city: Optional[str] # MERCITYO
    merchant_state: Optional[str] # MERSTO
    merchant_zip: Optional[str]  # MERZIPO

class FraudToggleRequest(BaseModel):
    """Maps COPAUS1C PF5 fraud toggle (PA-FRAUD-CONFIRMED 'F' ↔ PA-FRAUD-REMOVED 'R')"""
    current_fraud_status: str = Field(..., description="Current status from detail page: N/F/R")
```

### `GET /api/v1/authorizations`
**COBOL Source**: COPAUS0C (5 rows per page, IMS GU/GNP pattern)

**Query Parameters**:
- `account_id` (required): maps ACCTIDI search field
- `page` (default 1), `page_size` (default 5, max 5)

**Business Logic**:
1. Read `authorization_summary` by account_id (replaces IMS GU PAUTSUM0)
2. Read `authorization_detail` for account_id ordered by `processed_at DESC` (replaces IMS GNP PAUTDTL1 with inverted key)
3. Paginate 5 per page (maps COPAUS0C 5 rows per screen)
4. Return summary info + list items

---

### `GET /api/v1/authorizations/{auth_id}`
**COBOL Source**: COPAUS1C POPULATE-DETAIL-SCREEN

**Business Logic**:
1. SELECT from `authorization_detail` WHERE auth_id = ?
2. Resolve `decline_reason` from inline table (COPAUS1C WS-DECLINE-REASONS SEARCH ALL)
3. Format `fraud_status`: 'F' → 'FRAUD', 'R' → 'REMOVED', 'N' → '' (empty)
4. Return `AuthorizationDetailResponse`

---

### `PUT /api/v1/authorizations/{auth_id}/fraud`
**COBOL Source**: COPAUS1C PF5 → COPAUS2C LINK (fraud toggle)

**Request Body**: `FraudToggleRequest`

**Business Logic** (maps COPAUS1C/COPAUS2C two-phase commit):
1. Read current `authorization_detail` record
2. If not found: 404
3. Toggle fraud_status: 'N'/'R' → 'F', 'F' → 'R'
4. UPDATE `authorization_detail.fraud_status` (replaces IMS REPL)
5. INSERT into `auth_fraud_log` (replaces DB2 INSERT AUTHFRDS; handle duplicate via UPSERT)
6. Commit both atomically (replaces EXEC CICS SYNCPOINT / SYNCPOINT ROLLBACK)
7. If any step fails: rollback both (replicates COPAUS2C SYNCPOINT ROLLBACK)
8. Return 200 `AuthorizationDetailResponse` with updated fraud_status

---

## 10. Transaction Type Module
**COBOL Source**: COTRTLIC, COTRTUPC

### Pydantic Models

```python
class TransactionTypeResponse(BaseModel):
    type_code: str
    description: str
    updated_at: datetime

class TransactionTypeCreateRequest(BaseModel):
    """Maps COTRTUPC TTUP-CREATE-NEW-RECORD state"""
    type_code: str = Field(..., min_length=1, max_length=2, pattern=r'^[0-9]{1,2}$')
    description: str = Field(..., min_length=1, max_length=50, pattern=r'^[A-Za-z0-9 ]+$')

    @field_validator('type_code')
    @classmethod
    def validate_nonzero(cls, v: str) -> str:
        if int(v) == 0:
            raise ValueError("Tran Type code must not be zero")
        return v

class TransactionTypeUpdateRequest(BaseModel):
    """Maps COTRTUPC TTUP-CHANGES-OK-NOT-CONFIRMED state"""
    description: str = Field(..., min_length=1, max_length=50, pattern=r'^[A-Za-z0-9 ]+$')
    optimistic_lock_version: datetime = Field(..., description="updated_at from GET — replaces COTRTLIC no-change detection")
```

### `GET /api/v1/transaction-types`
**COBOL Source**: COTRTLIC (7 rows per page, DB2 cursor C-TR-TYPE-FORWARD)

**Query Parameters**:
- `type_code_filter` (optional, 2 digits): maps TRTYPE field
- `description_filter` (optional, 50 chars): maps TRDESC field → wrapped as %filter% LIKE
- `page` (default 1), `page_size` (default 7, max 7)

**Business Logic**:
1. Build WHERE clause: `type_code >= type_code_filter` (forward cursor >= start key)
2. Apply LIKE if description_filter provided: `description ILIKE '%filter%'`
3. ORDER BY type_code ASC
4. Paginate 7 per page

---

### `POST /api/v1/transaction-types`
**COBOL Source**: COTRTUPC 9600-WRITE-PROCESSING (INSERT)

**Request Body**: `TransactionTypeCreateRequest`

**Business Logic**:
1. Validate type_code numeric nonzero
2. Validate description alphanumeric only (no special chars)
3. Check uniqueness: 409 if type_code already exists
4. INSERT into `transaction_types`
5. Return 201 `TransactionTypeResponse`

---

### `PUT /api/v1/transaction-types/{type_code}`
**COBOL Source**: COTRTUPC 9600-WRITE-PROCESSING (UPDATE)

**Request Body**: `TransactionTypeUpdateRequest`

**Business Logic**:
1. Read current record (replaces 9000-READ-TRANTYPE)
2. If not found: 404
3. Check optimistic lock: if `updated_at != optimistic_lock_version` → 409 "Record changed by someone else"
4. Validate description alphanumeric
5. Compare new description to current (maps COTRTLIC no-change detection)
6. If no change: 422 "No change detected with respect to database values"
7. UPDATE `transaction_types`
8. Return 200 `TransactionTypeResponse`

---

### `DELETE /api/v1/transaction-types/{type_code}`
**COBOL Source**: COTRTUPC 9800-DELETE-PROCESSING

**Business Logic**:
1. Read current record
2. If not found: 404
3. Attempt DELETE
4. If FK violation (transactions reference this type_code): 409 "Please delete associated child records first" (maps SQLCODE -532)
5. Return 204 No Content on success

---

## 11. System / Compatibility Module

### `GET /api/v1/system/date-time`
**COBOL Source**: CODATE01 (MQ date service replacement)

**Response**:
```json
{
  "current_date": "2025-04-06",
  "current_time": "14:30:22",
  "formatted_date": "04/06/25"
}
```

### `GET /api/v1/account-inquiry/{account_id}`
**COBOL Source**: COACCT01 (MQ account inquiry replacement)

**Response**: Account summary (replaces MQ CSV reply format; note: ZIP code BUG FIXED — included in response)

---

## 12. Admin Task Endpoints

All batch program replacements are admin-only endpoints that submit background tasks.

```
POST /api/v1/admin/tasks/account-export      (CBACT01C)
POST /api/v1/admin/tasks/account-copy        (CBACT02C)
POST /api/v1/admin/tasks/transaction-verify  (CBTRN01C)
POST /api/v1/admin/tasks/transaction-post    (CBTRN02C)
POST /api/v1/admin/tasks/statement-generate  (CBSTM03A + CBSTM03B)
POST /api/v1/admin/tasks/auth-populate       (CBPAUP0C)
GET  /api/v1/admin/tasks/{task_id}/status    (task status check)
```

**Common Response** (`TaskSubmissionResponse`):
```python
class TaskSubmissionResponse(BaseModel):
    task_id: str
    task_type: str
    status: Literal['SUBMITTED']
    submitted_at: datetime
    status_url: str
```

---

## 13. Menu / Navigation Endpoints

### `GET /api/v1/menu`
**COBOL Source**: COMEN01C menu option list

**Response**: List of menu options filtered by user role (admin options suppressed for non-admin users — maps COMEN01C COPAUS0C INQUIRE PROGRAM logic)

### `GET /api/v1/admin/menu`
**COBOL Source**: COADM01C admin menu options

**Response**: Admin menu options (admin-only endpoint)
