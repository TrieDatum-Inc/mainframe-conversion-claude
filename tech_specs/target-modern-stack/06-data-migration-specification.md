# Data Migration Specification: Mainframe to PostgreSQL

## Document Purpose

Defines the complete data extraction, transformation, and loading (ETL) strategy for migrating all CardDemo data stores — VSAM KSDS files, DB2 tables, and IMS databases — into the PostgreSQL schema described in `01-database-specification.md`. Covers COBOL data type unpacking, EBCDIC conversion, password re-hashing, PCI-DSS considerations, referential integrity validation, and the phased migration execution plan.

---

## 1. Source Data Inventory

### 1.1 VSAM KSDS Files

| CICS File Name | Dataset Path | Record Length | Key Length | Key Offset | Record Count (est.) | PostgreSQL Target |
|----------------|-------------|---------------|-----------|-----------|---------------------|-------------------|
| USRSEC | AWS.M2.CARDDEMO.USRSEC.VSAM.KSDS | 300 bytes | 8 bytes | 0 | ~100 | `users` |
| ACCTDAT | AWS.M2.CARDDEMO.ACCTDATA.VSAM.KSDS | 300 bytes | 11 bytes | 0 | ~50,000 | `accounts` |
| CUSTDAT | AWS.M2.CARDDEMO.CUSTDATA.VSAM.KSDS | 500 bytes | 9 bytes | 0 | ~50,000 | `customers` |
| CARDDAT | AWS.M2.CARDDEMO.CARDDATA.VSAM.KSDS | 150 bytes | 16 bytes | 0 | ~75,000 | `credit_cards` |
| CCXREF | AWS.M2.CARDDEMO.CARDXREF.VSAM.KSDS | 50 bytes | 16 bytes | 0 | ~75,000 | `card_account_xref` |
| TRANSACT | AWS.M2.CARDDEMO.TRANSACT.VSAM.KSDS | 350 bytes | 16 bytes | 0 | ~2,000,000 | `transactions` |

**Notes**:
- CARDAIX and CXACAIX are alternate index paths over CARDDAT and CCXREF respectively; they are not separately migrated — PostgreSQL indexes replace them
- All VSAM files are EBCDIC-encoded on z/OS; extraction must perform EBCDIC-to-UTF-8 conversion

### 1.2 DB2 Tables

| DB2 Table | Schema | PostgreSQL Target |
|-----------|--------|-------------------|
| TRNTYPE | CARDDEMO | `transaction_types` |
| TRNTYCAT | CARDDEMO | `transaction_type_categories` |
| AUTHFRDS | — | `fraud_flags` |

### 1.3 IMS Databases

| IMS DBD | Segment | Access | PostgreSQL Target |
|---------|---------|--------|-------------------|
| PAUTHDTL | Auth detail segment | DL/I GU/GN | `pending_authorizations` |
| PAUTHSUM | Auth summary segment | DL/I GU/GN | (derived from `pending_authorizations` with aggregate view) |

---

## 2. COBOL Data Type to PostgreSQL Type Mapping

### 2.1 Fundamental Type Mapping

| COBOL Clause | USAGE | Internal Format | PostgreSQL Type | Extraction Rule |
|--------------|-------|-----------------|-----------------|-----------------|
| `PIC X(n)` | DISPLAY | EBCDIC characters | `VARCHAR(n)` | EBCDIC decode; right-trim spaces |
| `PIC 9(n)` | DISPLAY | EBCDIC zoned decimal | `INTEGER` or `BIGINT` | EBCDIC decode; parse integer |
| `PIC 9(n)V9(m)` | DISPLAY | EBCDIC zoned decimal | `NUMERIC(n+m, m)` | EBCDIC decode; insert implied decimal |
| `PIC S9(n)V9(m)` | COMP-3 | Packed decimal (BCD) | `NUMERIC(n+m, m)` | Unpack BCD; apply sign nibble |
| `PIC S9(n)` | COMP-3 | Packed decimal | `NUMERIC(n, 0)` | Unpack BCD; apply sign nibble |
| `PIC S9(n)` | COMP | Binary (big-endian) | `INTEGER` or `BIGINT` | Read big-endian binary |
| `PIC S9(9)` | COMP | 4-byte binary | `INTEGER` | `struct.unpack('>i', bytes)` |
| `PIC S9(18)` | COMP | 8-byte binary | `BIGINT` | `struct.unpack('>q', bytes)` |
| `PIC X(1)` flag | DISPLAY | Single EBCDIC char | `CHAR(1)` | EBCDIC decode; validate against CHECK constraint values |
| `PIC 9(8)` date CCYYMMDD | DISPLAY | EBCDIC zoned decimal | `DATE` | Parse as `datetime.strptime(val, '%Y%m%d').date()` |
| `PIC X(10)` date YYYY-MM-DD | DISPLAY | EBCDIC characters | `DATE` | `datetime.strptime(val, '%Y-%m-%d').date()` |
| `PIC 9(4)` year | DISPLAY | EBCDIC zoned decimal | Part of `DATE` | Combine with month/day fields |
| `PIC 9(2)` month/day | DISPLAY | EBCDIC zoned decimal | Part of `DATE` | Combine with year field |
| `FILLER` | any | Padding | — | Discard |

### 2.2 COMP-3 (Packed Decimal) Unpacking Algorithm

COMP-3 stores two decimal digits per byte, with the last nibble being a sign indicator:
- `C` (0x0C) or `F` (0x0F) = positive
- `D` (0x0D) = negative
- `A`, `B`, `E` = positive (alternate representations)

```python
def unpack_comp3(raw_bytes: bytes, decimal_places: int = 0) -> Decimal:
    """
    Unpack a COMP-3 (packed decimal) field from raw bytes.
    
    COBOL origin: All S9(n)V9(m) COMP-3 fields in CVACT01Y, CVTRA01Y-07Y,
    and CVCRD01Y copybooks (balances, amounts, credit limits).
    """
    hex_str = raw_bytes.hex().upper()
    digits = hex_str[:-1]          # All but last nibble = digit string
    sign_nibble = hex_str[-1]      # Last nibble = sign
    
    value = Decimal(digits)
    if sign_nibble in ('D',):
        value = -value
    
    if decimal_places > 0:
        value = value / Decimal(10 ** decimal_places)
    
    return value
```

**Field-specific application**:

| COBOL Field | PIC | Bytes | Decimal Places | COMP-3 Unpack Call |
|------------|-----|-------|----------------|-------------------|
| ACCT-CURR-BAL | S9(10)V99 COMP-3 | 7 | 2 | `unpack_comp3(raw[offset:offset+7], 2)` |
| ACCT-CREDIT-LIMIT | S9(10)V99 COMP-3 | 7 | 2 | `unpack_comp3(raw[offset:offset+7], 2)` |
| ACCT-CASH-CREDIT-LIMIT | S9(10)V99 COMP-3 | 7 | 2 | `unpack_comp3(raw[offset:offset+7], 2)` |
| ACCT-CURR-CYC-CREDIT | S9(10)V99 COMP-3 | 7 | 2 | `unpack_comp3(raw[offset:offset+7], 2)` |
| ACCT-CURR-CYC-DEBIT | S9(10)V99 COMP-3 | 7 | 2 | `unpack_comp3(raw[offset:offset+7], 2)` |
| TRAN-AMT | S9(10)V99 COMP-3 | 7 | 2 | `unpack_comp3(raw[offset:offset+7], 2)` |
| CUST-FICO-CREDIT-SCORE | 9(3)V9 COMP-3 | 3 | 1 | `unpack_comp3(raw[offset:offset+3], 1)` |

### 2.3 Zoned Decimal (DISPLAY) Extraction

COBOL `PIC 9(n)` fields in DISPLAY format use EBCDIC zoned decimal encoding where each digit is one EBCDIC byte:

- Digits 0-9 map to EBCDIC F0-F9
- For signed fields, the last digit's zone nibble encodes the sign (C/F=positive, D=negative)

```python
import codecs

def decode_zoned_decimal(raw_bytes: bytes, decimal_places: int = 0) -> Decimal:
    """
    Decode a COBOL zoned decimal (DISPLAY numeric) field.
    Used for PIC 9(n) and PIC 9(n)V9(m) DISPLAY fields.
    """
    text = raw_bytes.decode('cp037')   # EBCDIC code page 037 (US)
    text = text.strip()
    if not text:
        return Decimal(0)
    
    value = Decimal(text)
    if decimal_places > 0:
        value = value / Decimal(10 ** decimal_places)
    return value

def decode_ebcdic_string(raw_bytes: bytes) -> str:
    """
    Decode an EBCDIC character field to UTF-8 string.
    Right-strip trailing spaces.
    COBOL origin: All PIC X(n) DISPLAY fields.
    """
    return raw_bytes.decode('cp037').rstrip()
```

### 2.4 Date Format Normalization

| COBOL Format | Example Value | Extraction |
|-------------|--------------|-----------|
| `PIC 9(8)` CCYYMMDD (YYYYMMDD) | `20231215` | `datetime.strptime(str(val).zfill(8), '%Y%m%d').date()` |
| `PIC X(10)` YYYY-MM-DD | `2023-12-15` | `datetime.strptime(val, '%Y-%m-%d').date()` |
| Split: OPNYEAR(4) + OPNMON(2) + OPNDAY(2) | `2023`, `12`, `15` | Concatenate then parse; handle `0000-00-00` as NULL |
| `PIC 9(4)` year + `PIC 9(2)` month + `PIC 9(2)` day | Separate fields | Combine: `date(year, month, day)`; guard against month=0, day=0 |

**Null date handling**: COBOL programs use `0000-00-00` or `00000000` to represent "no date set." These must be converted to SQL `NULL` rather than inserted as invalid dates.

```python
def parse_cobol_date(value: str) -> Optional[date]:
    """Convert COBOL date strings to Python date, returning None for zero dates."""
    cleaned = value.strip().replace('-', '')
    if cleaned in ('', '00000000', '0' * len(cleaned)):
        return None
    try:
        return datetime.strptime(cleaned, '%Y%m%d').date()
    except ValueError:
        return None
```

### 2.5 IMS Inverted Timestamp Key (PAUTHDTL)

The IMS PAUTHDTL database uses an inverted timestamp as part of its key to achieve reverse chronological ordering via ascending key scans:

**COBOL key construction** (COPAUA0C):
```
AUTH-TIME = 999999999 - CURRENT-TIMESTAMP-INTEGER
```

**PostgreSQL migration**:
```python
def uninvert_timestamp(inverted_value: int, base_epoch: int = 999999999) -> datetime:
    """
    Reverse the IMS key inversion to recover actual timestamp.
    COBOL origin: COPAUA0C key construction for PAUTHDTL IMS database.
    The actual ORDER BY becomes ORDER BY processed_at DESC in PostgreSQL.
    """
    actual_seconds_from_epoch = base_epoch - inverted_value
    return datetime.fromtimestamp(actual_seconds_from_epoch, tz=timezone.utc)
```

---

## 3. VSAM File Record Layouts and Extraction Maps

### 3.1 USRSEC Record Layout (users table)

**Copybook**: CSUSR01Y  
**Record length**: 300 bytes

| Offset | Length | COBOL Field | COBOL PIC | USAGE | PostgreSQL Column | Transform |
|--------|--------|------------|-----------|-------|------------------|-----------|
| 0 | 8 | SEC-USR-ID | X(8) | DISPLAY | `user_id` | EBCDIC decode; right-trim |
| 8 | 8 | SEC-USR-PWD | X(8) | DISPLAY | `password_hash` | **See Section 5.1: password migration** |
| 16 | 20 | SEC-USR-FNAME | X(20) | DISPLAY | `first_name` | EBCDIC decode; right-trim |
| 36 | 20 | SEC-USR-LNAME | X(20) | DISPLAY | `last_name` | EBCDIC decode; right-trim |
| 56 | 1 | SEC-USR-TYPE | X(1) | DISPLAY | `user_type` | EBCDIC decode; validate IN ('A','U') |
| 57 | 23 | SEC-USR-FILLER | X(23) | DISPLAY | — | Discard (unused padding) |
| 80 | 220 | (remaining) | X(220) | DISPLAY | — | Discard |

### 3.2 ACCTDAT Record Layout (accounts table)

**Copybook**: CVACT01Y  
**Record length**: 300 bytes

| Offset | Length | COBOL Field | COBOL PIC | USAGE | PostgreSQL Column | Transform |
|--------|--------|------------|-----------|-------|------------------|-----------|
| 0 | 11 | ACCT-ID | 9(11) | DISPLAY | `account_id` | Zoned decimal decode → BIGINT |
| 11 | 1 | ACCT-ACTIVE-STATUS | X(1) | DISPLAY | `active_status` | EBCDIC decode; validate IN ('Y','N') |
| 12 | 7 | ACCT-CURR-BAL | S9(10)V99 | COMP-3 | `current_balance` | `unpack_comp3(7 bytes, 2)` |
| 19 | 7 | ACCT-CREDIT-LIMIT | S9(10)V99 | COMP-3 | `credit_limit` | `unpack_comp3(7 bytes, 2)` |
| 26 | 7 | ACCT-CASH-CREDIT-LIMIT | S9(10)V99 | COMP-3 | `cash_credit_limit` | `unpack_comp3(7 bytes, 2)` |
| 33 | 10 | ACCT-OPEN-DATE | X(10) | DISPLAY | `open_date` | `parse_cobol_date` (YYYY-MM-DD format) |
| 43 | 10 | ACCT-EXPIRAION-DATE | X(10) | DISPLAY | `expiration_date` | `parse_cobol_date` |
| 53 | 10 | ACCT-REISSUE-DATE | X(10) | DISPLAY | `reissue_date` | `parse_cobol_date` |
| 63 | 7 | ACCT-CURR-CYC-CREDIT | S9(10)V99 | COMP-3 | `curr_cycle_credit` | `unpack_comp3(7 bytes, 2)` |
| 70 | 7 | ACCT-CURR-CYC-DEBIT | S9(10)V99 | COMP-3 | `curr_cycle_debit` | `unpack_comp3(7 bytes, 2)` |
| 77 | 10 | ACCT-ADDR-ZIP | X(10) | DISPLAY | `zip_code` | EBCDIC decode; right-trim |
| 87 | 10 | ACCT-GROUP-ID | X(10) | DISPLAY | `group_id` | EBCDIC decode; right-trim |
| 97 | 203 | (padding/filler) | — | — | — | Discard |

**Note on ACCT-EXPIRAION-DATE**: The COBOL source contains a typo (`EXPIRAION` instead of `EXPIRATION`). The PostgreSQL column is named `expiration_date` (corrected). Document this discrepancy in migration logs.

### 3.3 CUSTDAT Record Layout (customers table)

**Copybook**: CUSTREC / CVCUS01Y  
**Record length**: 500 bytes

| Offset | Length | COBOL Field | COBOL PIC | USAGE | PostgreSQL Column | Transform |
|--------|--------|------------|-----------|-------|------------------|-----------|
| 0 | 9 | CUST-ID | 9(9) | DISPLAY | `customer_id` | Zoned decimal decode → BIGINT |
| 9 | 25 | CUST-FIRST-NAME | X(25) | DISPLAY | `first_name` | EBCDIC decode; right-trim |
| 34 | 25 | CUST-MIDDLE-NAME | X(25) | DISPLAY | `middle_name` | EBCDIC decode; right-trim; NULL if empty |
| 59 | 25 | CUST-LAST-NAME | X(25) | DISPLAY | `last_name` | EBCDIC decode; right-trim |
| 84 | 25 | CUST-ADDR-LINE-1 | X(25) | DISPLAY | `address_line_1` | EBCDIC decode; right-trim |
| 109 | 25 | CUST-ADDR-LINE-2 | X(25) | DISPLAY | `address_line_2` | EBCDIC decode; right-trim; NULL if empty |
| 134 | 25 | CUST-ADDR-LINE-3 | X(25) | DISPLAY | `address_line_3` | EBCDIC decode; right-trim; NULL if empty |
| 159 | 3 | CUST-ADDR-STATE-CD | X(3) | DISPLAY | `state_code` | EBCDIC decode; right-trim |
| 162 | 10 | CUST-ADDR-COUNTRY-CD | X(10) | DISPLAY | `country_code` | EBCDIC decode; right-trim |
| 172 | 10 | CUST-ADDR-ZIP | X(10) | DISPLAY | `zip_code` | EBCDIC decode; right-trim |
| 182 | 15 | CUST-PHONE-NUM-1 | X(15) | DISPLAY | `phone_number_1` | EBCDIC decode; right-trim |
| 197 | 15 | CUST-PHONE-NUM-2 | X(15) | DISPLAY | `phone_number_2` | EBCDIC decode; right-trim; NULL if empty |
| 212 | 10 | CUST-SSN | X(10) | DISPLAY | `ssn_encrypted` | **See Section 5.2: SSN encryption** |
| 222 | 10 | CUST-GOVT-ISSUED-ID | X(10) | DISPLAY | `govt_issued_id` | EBCDIC decode; right-trim |
| 232 | 8 | CUST-DOB-YYYY-MM-DD | X(8) | DISPLAY | `date_of_birth` | `parse_cobol_date` (YYYYMMDD) |
| 240 | 3 | CUST-EFT-ACCOUNT-ID | X(3) | DISPLAY | `eft_account_id` | EBCDIC decode; right-trim |
| 243 | 1 | CUST-PRI-CARD-HOLDER-IND | X(1) | DISPLAY | `primary_card_holder_ind` | EBCDIC decode; validate IN ('Y','N') |
| 244 | 3 | CUST-FICO-CREDIT-SCORE | 9(3)V9 | COMP-3 | `fico_score` | `unpack_comp3(3 bytes, 1)` → NUMERIC(4,1) |
| 247 | 11 | CUST-ACCT-ID | 9(11) | DISPLAY | `account_id` | FK to `accounts`; zoned decimal decode |
| 258 | 242 | (padding) | — | — | — | Discard |

### 3.4 CARDDAT Record Layout (credit_cards table)

**Copybook**: CVCRD01Y  
**Record length**: 150 bytes

| Offset | Length | COBOL Field | COBOL PIC | USAGE | PostgreSQL Column | Transform |
|--------|--------|------------|-----------|-------|------------------|-----------|
| 0 | 16 | CARD-NUM | X(16) | DISPLAY | `card_number` | EBCDIC decode; **PCI-DSS: store as masked or tokenized** |
| 16 | 11 | CARD-ACCT-ID | 9(11) | DISPLAY | `account_id` | Zoned decimal decode → BIGINT; FK to `accounts` |
| 27 | 3 | CARD-CVV-CD | X(3) | DISPLAY | — | **PCI-DSS: DO NOT migrate CVV; discard** |
| 30 | 4 | CARD-EMBOSSED-NAME | X(4) | DISPLAY | `embossed_name` | EBCDIC decode; right-trim |
| 34 | 8 | CARD-EXPIRAION-DATE | X(8) | DISPLAY | `expiration_date` | Split MM/YY or MMYYYY; parse to DATE |
| 42 | 1 | CARD-ACTIVE-STATUS | X(1) | DISPLAY | `active_status` | EBCDIC decode; validate IN ('Y','N') |
| 43 | 107 | (padding) | — | — | — | Discard |

**Critical PCI-DSS notes for CARDDAT**:
- `CARD-CVV-CD`: Must NOT be stored in the modern database. CVV must be discarded during extraction. PCI DSS Requirement 3.2.1 prohibits storing CVV after authorization.
- `CARD-NUM`: Full PAN (Primary Account Number) must be stored masked (first 6 + last 4 visible, middle masked) or replaced with a token from a PCI-compliant tokenization vault. The migration script must hash or tokenize the card number before insertion.

### 3.5 CCXREF Record Layout (card_account_xref table)

**Copybook**: CCXREF / CVCRD01Y (xref portion)  
**Record length**: 50 bytes

| Offset | Length | COBOL Field | COBOL PIC | USAGE | PostgreSQL Column | Transform |
|--------|--------|------------|-----------|-------|------------------|-----------|
| 0 | 16 | XREF-CARD-NUM | X(16) | DISPLAY | `card_number` | EBCDIC decode; PCI masking |
| 16 | 11 | XREF-ACCT-ID | 9(11) | DISPLAY | `account_id` | Zoned decimal decode |
| 27 | 9 | XREF-CUST-ID | 9(9) | DISPLAY | `customer_id` | Zoned decimal decode |
| 36 | 14 | (filler) | — | — | — | Discard |

### 3.6 TRANSACT Record Layout (transactions table)

**Copybook**: CVTRA01Y–CVTRA07Y (7 variants; CVTRA05Y is the primary layout)  
**Record length**: 350 bytes

| Offset | Length | COBOL Field | COBOL PIC | USAGE | PostgreSQL Column | Transform |
|--------|--------|------------|-----------|-------|------------------|-----------|
| 0 | 16 | TRAN-ID | X(16) | DISPLAY | `transaction_id` | EBCDIC decode; right-trim |
| 16 | 2 | TRAN-TYPE-CD | X(2) | DISPLAY | `transaction_type_code` | EBCDIC decode; FK to `transaction_types` |
| 18 | 4 | TRAN-CAT-CD | 9(4) | DISPLAY | `transaction_category_code` | Zoned decimal decode |
| 22 | 11 | TRAN-SOURCE-ACCT-ID | 9(11) | DISPLAY | `source_account_id` | Zoned decimal decode; FK to `accounts` |
| 33 | 16 | TRAN-SOURCE-CARD-NUM | X(16) | DISPLAY | `source_card_number` | EBCDIC decode; PCI masking |
| 49 | 7 | TRAN-AMT | S9(10)V99 | COMP-3 | `transaction_amount` | `unpack_comp3(7 bytes, 2)` |
| 56 | 50 | TRAN-MERCHANT-NAME | X(50) | DISPLAY | `merchant_name` | EBCDIC decode; right-trim |
| 106 | 9 | TRAN-MERCHANT-ID | 9(9) | DISPLAY | `merchant_id` | Zoned decimal decode |
| 115 | 50 | TRAN-MERCHANT-CITY | X(50) | DISPLAY | `merchant_city` | EBCDIC decode; right-trim |
| 165 | 2 | TRAN-MERCHANT-ZIP | X(2) | DISPLAY | `merchant_zip` | EBCDIC decode; right-trim |
| 167 | 10 | TRAN-ORIG-DATE | X(10) | DISPLAY | `original_date` | `parse_cobol_date` (YYYY-MM-DD) |
| 177 | 10 | TRAN-PROC-DATE | X(10) | DISPLAY | `processed_date` | `parse_cobol_date` (YYYY-MM-DD) |
| 187 | 163 | (remaining) | — | — | — | Discard padding |

---

## 4. DB2 and IMS Extraction

### 4.1 DB2 Table Extraction

DB2 tables are accessible via standard JDBC/ODBC or via `db2look` export utilities. No EBCDIC conversion is needed for data extracted via DB2 client tools (the DB2 client handles character set conversion automatically).

**TRNTYPE extraction**:
```sql
-- Run on source DB2 system:
SELECT TR_TYPE, TR_TYPE_DESC FROM CARDDEMO.TRNTYPE ORDER BY TR_TYPE;
```
Maps directly to `transaction_types(transaction_type_code, description)`.

**TRNTYCAT extraction**:
```sql
SELECT * FROM CARDDEMO.TRNTYCAT ORDER BY 1;
```
Maps directly to `transaction_type_categories`.

**AUTHFRDS extraction**:
```sql
SELECT CARD_NUM, AUTH_TIMESTAMP, AUTH_AMOUNT, MERCHANT_ID, FRAUD_FLAG
FROM AUTHFRDS
ORDER BY AUTH_TIMESTAMP;
```
Maps to `fraud_flags` table; card numbers require PCI masking.

### 4.2 IMS HISAM Extraction

IMS databases require extraction via IMS unload utilities. The batch programs `PAUDBUNL` (program spec in `tech_specs/programs/authorization/PAUDBUNL.md`) and `DBUNLDGS` already exist for this purpose.

**Extraction approach**:
1. Run `UNLDPADB.JCL` (which calls `PAUDBUNL`) to produce a sequential flat file of PAUTHDTL records
2. Run `UNLDGSAM.JCL` (which calls `DBUNLDGS`) for GSAM data if applicable
3. Parse the sequential output files using the segment layouts from `CIPAUDTY` and `CIPAUSMY` copybooks

**PAUTHDTL segment layout** (from CIPAUDTY copybook):

| Field | PIC | USAGE | PostgreSQL Column | Transform |
|-------|-----|-------|------------------|-----------|
| PAUTH-CARD-NUM | X(16) | DISPLAY | `card_number` | PCI masking |
| PAUTH-TIMESTAMP-INV | 9(9) | COMP | `processed_at` | `uninvert_timestamp()` |
| PAUTH-AMOUNT | S9(10)V99 | COMP-3 | `authorization_amount` | `unpack_comp3` |
| PAUTH-MERCHANT | X(50) | DISPLAY | `merchant_name` | EBCDIC decode |
| PAUTH-RESPONSE | X(2) | DISPLAY | `response_code` | EBCDIC decode |
| PAUTH-DECLINE-REASON | X(50) | DISPLAY | `decline_reason` | EBCDIC decode; NULL if blank |

**PAUTHSUM**: Not migrated as a separate table. It is derived as an aggregation view over `pending_authorizations`:
```sql
CREATE VIEW pending_auth_summary AS
SELECT card_number, COUNT(*) AS auth_count, SUM(authorization_amount) AS total_amount
FROM pending_authorizations
GROUP BY card_number;
```

---

## 5. Sensitive Data Handling

### 5.1 Password Migration Strategy

**Source**: `SEC-USR-PWD X(8)` in USRSEC VSAM — stored as **plain text EBCDIC**

**Security problem**: The COSGN00C program performs a direct byte-comparison of entered password vs. stored password with no hashing. This is a critical security vulnerability documented in the system's Known Issues (section 12 of overall-system-specification.md).

**Migration options** (in order of preference):

#### Option A: Forced Reset (Recommended)
1. Extract user records (user ID, names, type) but do NOT migrate passwords
2. Generate a temporary password for each user (e.g., `Temp!{user_id}` or a random 12-char token)
3. Hash each temporary password with bcrypt (`cost factor 12`)
4. Set `password_reset_required = TRUE` on all migrated users
5. On first login in the modern system, force a password change before allowing access
6. Notify users via email/out-of-band communication of their temporary password

#### Option B: Migrate and Hash (Fallback if forced reset is not operationally feasible)
1. Extract `SEC-USR-PWD` as plain text (EBCDIC-decoded)
2. Hash each plain-text password with bcrypt: `passlib.hash.bcrypt.using(rounds=12).hash(plain_text_password)`
3. Store hash in `users.password_hash`
4. Set `password_reset_required = FALSE`

**bcrypt implementation**:
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

def hash_plain_text_password(plain_text: str) -> str:
    """
    Hash a plain-text COBOL password for PostgreSQL storage.
    Source: SEC-USR-PWD X(8) from USRSEC VSAM.
    """
    return pwd_context.hash(plain_text)
```

**Recommendation**: Use Option A for all production migrations. Option B is acceptable only for development/test migrations where the original test credentials need to be preserved for developer access.

### 5.2 SSN Encryption

**Source**: `CUST-SSN X(10)` in CUSTDAT VSAM — stored as **plain text EBCDIC**

**PCI/privacy requirement**: SSNs are PII (Personally Identifiable Information) subject to various state and federal privacy laws. They must not be stored in plain text in a modern system.

**Migration approach**:
1. Extract SSN as plain text from VSAM
2. Normalize: strip non-digit characters, validate 9-digit format
3. Encrypt using AES-256 (symmetric, application-managed key) or store in a secrets vault
4. Store the encrypted ciphertext in `customers.ssn_encrypted VARCHAR(255)`
5. Store last 4 digits in `customers.ssn_last_four CHAR(4)` for display/lookup purposes only

```python
from cryptography.fernet import Fernet

def encrypt_ssn(plain_ssn: str, encryption_key: bytes) -> str:
    """
    Encrypt SSN before PostgreSQL insertion.
    Source: CUST-SSN X(10) from CUSTDAT VSAM.
    Key must be managed via AWS KMS, HashiCorp Vault, or equivalent.
    """
    f = Fernet(encryption_key)
    normalized = ''.join(filter(str.isdigit, plain_ssn))
    return f.encrypt(normalized.encode()).decode()
```

**Key management**: The encryption key must NOT be stored in the application code or database. It must be retrieved at runtime from a secrets management system (AWS Secrets Manager, HashiCorp Vault, or equivalent).

### 5.3 Credit Card Number PCI-DSS Treatment

**Source**: `CARD-NUM X(16)` in CARDDAT and `TRAN-SOURCE-CARD-NUM X(16)` in TRANSACT

**PCI DSS Requirement 3.3**: Only the first 6 and last 4 digits of a PAN may be displayed. The full PAN must not be stored unless there is a legitimate business need and it is protected with strong cryptography.

**Migration approach (mask and store)**:
1. Extract full 16-digit card number from VSAM
2. Store a masked version: `{first6}XXXXXX{last4}` in `credit_cards.card_number_masked`
3. Generate a non-reversible token using SHA-256 HMAC with a secret: `HMAC-SHA256(secret, card_number)` → store as `card_number_token CHAR(64)` for lookup without storing the PAN
4. If full PAN is required for business operations, use a PCI-compliant tokenization vault (CardVault, Voltage, etc.) and store only the vault token

**CVV discard**:
```python
# CRITICAL: CVV is read from CARDDAT.CARD-CVV-CD but NEVER inserted into any table
# PCI DSS 3.2.1: CVV must not be stored after authorization
card_cvv = None  # Explicitly discard; never assign to any output structure
```

---

## 6. Referential Integrity Validation

All records must be validated for referential integrity before insertion. The migration script must run checks in the following dependency order:

### 6.1 Load Order (Dependency Graph)

```
Phase 1 (no dependencies):
  transaction_types         (from DB2 TRNTYPE)
  transaction_type_categories (from DB2 TRNTYCAT)

Phase 2 (depends on Phase 1):
  customers                 (from CUSTDAT VSAM)
  accounts                  (from ACCTDAT VSAM)

Phase 3 (depends on Phase 2):
  credit_cards              (from CARDDAT VSAM — FK to accounts)
  card_account_xref         (from CCXREF VSAM — FK to accounts, customers)

Phase 4 (depends on Phase 3):
  transactions              (from TRANSACT VSAM — FK to accounts, transaction_types)
  pending_authorizations    (from IMS PAUTHDTL)

Phase 5 (depends on Phase 4):
  fraud_flags               (from DB2 AUTHFRDS — FK to pending_authorizations)

Final:
  users                     (from USRSEC VSAM — no FK dependencies)
```

### 6.2 Validation Rules Per Table

**users**:
- `user_id` must be non-blank and max 8 characters
- `user_type` must be IN ('A', 'U')
- Duplicate `user_id` values → reject duplicate; log; skip

**accounts**:
- `account_id` must be > 0
- `credit_limit` >= 0, `cash_credit_limit` <= `credit_limit`
- `active_status` IN ('Y', 'N')
- `open_date` must not be NULL (if zero-date, set to migration run date and flag record)

**customers**:
- `customer_id` must be > 0
- `account_id` FK must exist in `accounts`; if not found → reject; log orphan record
- `ssn` if present must be exactly 9 digits after stripping non-digits

**credit_cards**:
- `account_id` FK must exist in `accounts`
- `card_number` (16 chars) must pass Luhn algorithm check; if fails → log warning but still migrate (VSAM may have test data)
- `active_status` IN ('Y', 'N')

**transactions**:
- `source_account_id` FK must exist in `accounts`; if not found → reject; log
- `transaction_type_code` FK must exist in `transaction_types`; if not found → set to NULL and log
- `transaction_amount` must not be NULL; if unpack fails → reject; log
- `original_date` must be parseable; if invalid → set to NULL and log

**pending_authorizations**:
- `card_number` FK must exist in `credit_cards`; if not found → migrate but flag as orphan
- `processed_at` must be successfully derived from inverted timestamp; if fails → reject; log

### 6.3 Error Handling During Migration

Each migration run produces a structured rejection log:

```
migration_rejections.csv
  record_type, source_key, rejection_reason, raw_hex, timestamp
```

Rejection categories:
| Code | Description |
|------|-------------|
| `INVALID_FK` | Foreign key not found in dependency table |
| `INVALID_TYPE` | Field value fails CHECK constraint |
| `UNPACK_ERROR` | COMP-3 or zoned decimal decoding failed |
| `DATE_INVALID` | Date field contains invalid value |
| `PCI_DISCARD` | Record discarded due to PCI requirement (CVV, full PAN) |
| `DUPLICATE_KEY` | Duplicate primary key encountered |
| `ENCODING_ERROR` | EBCDIC decoding failed (invalid code point) |

---

## 7. Migration Script Architecture

### 7.1 Python ETL Framework

The migration is implemented as a Python package using:
- `python-cobol` or custom byte-level parsing for VSAM binary extraction
- `ibm_db` for DB2 extraction (if JDBC not available)
- `psycopg2` for PostgreSQL insertion (with `COPY` for bulk loads)
- `passlib[bcrypt]` for password hashing
- `cryptography` for SSN encryption

### 7.2 Migration Script Structure

```
migration/
├── __init__.py
├── config.py                    # Source/target DB connection params, encryption keys
├── extractors/
│   ├── __init__.py
│   ├── vsam_extractor.py        # VSAM file reader + EBCDIC decoder
│   ├── db2_extractor.py         # DB2 SELECT statements
│   └── ims_extractor.py         # IMS sequential unload file parser
├── transformers/
│   ├── __init__.py
│   ├── cobol_types.py           # unpack_comp3, decode_zoned_decimal, etc.
│   ├── date_transformer.py      # parse_cobol_date, split-date assembly
│   ├── security_transformer.py  # password hashing, SSN encryption, PCI masking
│   └── validators.py            # referential integrity, field-level validation
├── loaders/
│   ├── __init__.py
│   ├── postgres_loader.py       # Bulk COPY + INSERT with conflict handling
│   └── rejection_logger.py     # Structured rejection log writer
├── runners/
│   ├── __init__.py
│   ├── phase1_runner.py         # reference data (transaction types)
│   ├── phase2_runner.py         # customers and accounts
│   ├── phase3_runner.py         # cards and xref
│   ├── phase4_runner.py         # transactions and pending auths
│   ├── phase5_runner.py         # fraud flags
│   └── users_runner.py          # user accounts (independent phase)
└── main.py                      # Orchestrator: runs phases in order; summary report
```

### 7.3 Bulk Load Strategy

For large tables (TRANSACT: ~2M records), use PostgreSQL `COPY FROM STDIN` via `psycopg2.copy_expert` rather than individual `INSERT` statements:

```python
import io
import csv

def bulk_load_transactions(conn, records: list[dict]) -> int:
    """
    Bulk load transaction records using PostgreSQL COPY protocol.
    ~100x faster than individual INSERTs for large datasets.
    """
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter='\t', quotechar='"')
    for rec in records:
        writer.writerow([
            rec['transaction_id'],
            rec['transaction_type_code'] or r'\N',
            rec['transaction_category_code'] or r'\N',
            rec['source_account_id'],
            rec['source_card_number'],
            rec['transaction_amount'],
            rec['merchant_name'] or r'\N',
            rec['merchant_id'] or r'\N',
            rec['original_date'] or r'\N',
            rec['processed_date'] or r'\N',
        ])
    buf.seek(0)
    with conn.cursor() as cur:
        cur.copy_expert(
            "COPY transactions (transaction_id, transaction_type_code, ...) FROM STDIN WITH (FORMAT CSV, DELIMITER E'\\t', NULL '\\N')",
            buf
        )
    return len(records)
```

**Batch size**: Process TRANSACT in batches of 10,000 records to limit memory usage. Commit after each batch.

---

## 8. Migration Execution Plan

### 8.1 Pre-Migration Checklist

| Step | Action | Owner |
|------|--------|-------|
| P1 | Freeze CICS and batch activity on source system (maintenance window) | Operations |
| P2 | Take full VSAM backup of all files | Operations |
| P3 | Run DB2 `RUNSTATS` on all tables; verify row counts | DBA |
| P4 | Verify PostgreSQL target schema created and empty (`01-database-specification.md` DDL applied) | DBA |
| P5 | Deploy migration Python package to migration host | Developer |
| P6 | Configure `config.py` with correct connection strings, encryption key reference | Developer |
| P7 | Retrieve encryption key from secrets vault; inject as environment variable `MIGRATION_ENCRYPTION_KEY` | Security |
| P8 | Run migration on test data subset (100 accounts, 1000 transactions); verify output | Developer |
| P9 | Sign-off on test run validation report | Architect |

### 8.2 Migration Phases

#### Phase 0: Dry Run (No database writes)
- Run the migration script with `--dry-run` flag
- Parse all records, log all validation errors, generate rejection report
- **Pass criteria**: Rejection rate < 0.1% for each table; no ENCODING_ERROR in USRSEC or ACCTDAT

#### Phase 1: Reference Data (estimated: < 1 minute)
1. Extract TRNTYPE from DB2 → insert into `transaction_types`
2. Extract TRNTYCAT from DB2 → insert into `transaction_type_categories`
3. Verify counts match source

#### Phase 2: Core Master Data (estimated: 5–10 minutes)
1. Extract CUSTDAT VSAM → transform → load `customers` (COMP-3, SSN encryption)
2. Extract ACCTDAT VSAM → transform → load `accounts` (COMP-3, date normalization)
3. Verify FK relationships: all `customers.account_id` values exist in `accounts`

#### Phase 3: Card Data (estimated: 2–5 minutes)
1. Extract CARDDAT VSAM → transform → load `credit_cards` (PCI masking, CVV discard)
2. Extract CCXREF VSAM → transform → load `card_account_xref`
3. Verify all card FKs resolve to `accounts`

#### Phase 4: Transactional Data (estimated: 30–60 minutes for 2M records)
1. Extract TRANSACT VSAM in batches → transform → bulk load `transactions`
2. Extract IMS PAUTHDTL unload → transform (uninvert timestamps) → load `pending_authorizations`
3. Verify transaction count matches VSAM IDCAMS LISTCAT record count

#### Phase 5: Derived/Enriched Data (estimated: < 5 minutes)
1. Extract AUTHFRDS from DB2 → transform → load `fraud_flags`

#### Users (parallel to all phases, estimated: < 1 minute)
1. Extract USRSEC VSAM → transform (password strategy per Section 5.1) → load `users`

#### Sequence generation
After loading `transactions`, set the `transaction_id_seq` sequence to MAX(transaction_id) + 1:
```sql
-- After migration:
SELECT SETVAL('transaction_id_seq', (SELECT MAX(CAST(transaction_id AS BIGINT)) FROM transactions) + 1);
```

### 8.3 Post-Migration Validation

| Check | SQL | Expected Result |
|-------|-----|-----------------|
| User count | `SELECT COUNT(*) FROM users` | Matches USRSEC IDCAMS LISTCAT count |
| Account count | `SELECT COUNT(*) FROM accounts` | Matches ACCTDAT IDCAMS LISTCAT count |
| Customer count | `SELECT COUNT(*) FROM customers` | Matches CUSTDAT IDCAMS LISTCAT count |
| Card count | `SELECT COUNT(*) FROM credit_cards` | Matches CARDDAT IDCAMS LISTCAT count |
| Transaction count | `SELECT COUNT(*) FROM transactions` | Matches TRANSACT IDCAMS LISTCAT count |
| Orphan accounts | `SELECT COUNT(*) FROM customers c WHERE NOT EXISTS (SELECT 1 FROM accounts a WHERE a.account_id = c.account_id)` | 0 (or documented exceptions) |
| Orphan cards | `SELECT COUNT(*) FROM credit_cards cc WHERE NOT EXISTS (SELECT 1 FROM accounts a WHERE a.account_id = cc.account_id)` | 0 |
| FK violation check | `SELECT COUNT(*) FROM transactions t WHERE NOT EXISTS (SELECT 1 FROM accounts a WHERE a.account_id = t.source_account_id)` | 0 |
| Password hash format | `SELECT COUNT(*) FROM users WHERE password_hash NOT LIKE '$2b$%'` | 0 (all bcrypt) |
| CVV not present | Verify `credit_cards` table has no `cvv` column | Schema check |

### 8.4 Rollback Strategy

If migration validation fails:
1. Truncate all target tables in reverse dependency order (Phase 5 → Phase 1)
2. Restore from pre-migration PostgreSQL backup (if any data was previously present)
3. Investigate rejection logs; fix transformation errors
4. Re-run from Phase 0 (dry run)

Rollback is non-destructive to the source mainframe system since the VSAM files are never modified by the migration process (read-only extraction).

### 8.5 Cutover Procedure

1. Complete all migration phases; pass all validation checks
2. Run application smoke tests against PostgreSQL (sign-in, account lookup, transaction view)
3. Coordinate cutover timing with operations (off-hours preferred)
4. Update DNS / load balancer to route traffic to the modern application
5. Keep mainframe in read-only mode for 72-hour parallel observation period
6. Monitor application error rates; revert to mainframe if error rate exceeds SLA threshold
7. After 72-hour parallel period with no critical issues: formally decommission CICS region

---

## 9. Seed Data for Development/Testing

The following minimum seed data sets are required for each table in the development environment. These replace the VSAM-extracted data for local development.

### 9.1 users Seed Data

Minimum 10 rows; mix of admin ('A') and regular ('U') user types.

```sql
-- Seed data: passwords are bcrypt hash of the plaintext shown in comment
INSERT INTO users (user_id, first_name, last_name, password_hash, user_type) VALUES
('ADMIN001', 'Alice',   'Admin',    '$2b$12$...hash_of_Admin001!...', 'A'),  -- pw: Admin001!
('ADMIN002', 'Bob',     'Manager',  '$2b$12$...hash_of_Admin002!...', 'A'),  -- pw: Admin002!
('USER0001', 'Charlie', 'Smith',    '$2b$12$...hash_of_User0001!..', 'U'),
('USER0002', 'Diana',   'Jones',    '$2b$12$...hash_of_User0002!..', 'U'),
('USER0003', 'Edward',  'Brown',    '$2b$12$...hash_of_User0003!..', 'U'),
('USER0004', 'Fiona',   'Davis',    '$2b$12$...hash_of_User0004!..', 'U'),
('USER0005', 'George',  'Wilson',   '$2b$12$...hash_of_User0005!..', 'U'),
('USER0006', 'Helen',   'Martinez', '$2b$12$...hash_of_User0006!..', 'U'),
('USER0007', 'Ivan',    'Taylor',   '$2b$12$...hash_of_User0007!..', 'U'),
('USER0008', 'Julia',   'Anderson', '$2b$12$...hash_of_User0008!..', 'U');
```

**Note**: The actual bcrypt hash values must be generated by the seed script (not hardcoded). The `sql/seed_data.sql` generation script must call `bcrypt.hash(password)` for each row. Plaintext passwords are only used during seed script generation and must not appear in committed code.

### 9.2 accounts Seed Data (10 rows minimum)

```sql
INSERT INTO accounts (account_id, active_status, current_balance, credit_limit, cash_credit_limit, open_date, expiration_date, curr_cycle_credit, curr_cycle_debit, zip_code, group_id) VALUES
(00000000001, 'Y', 1250.75, 5000.00, 1000.00, '2020-01-15', '2025-01-31', 200.00, 1450.75, '10001', 'GRP001'),
(00000000002, 'Y', 0.00,   10000.00, 2000.00, '2019-06-01', '2024-06-30', 0.00, 0.00, '90210', 'GRP001'),
(00000000003, 'Y', 3500.00, 7500.00, 1500.00, '2021-03-10', '2026-03-31', 500.00, 4000.00, '60601', 'GRP002'),
(00000000004, 'N', 0.00,    2500.00, 500.00,  '2018-12-01', '2023-12-31', 0.00, 0.00, '77001', 'GRP002'),
(00000000005, 'Y', 750.25,  3000.00, 600.00,  '2022-07-20', '2027-07-31', 100.00, 850.25, '30301', 'GRP003'),
(00000000006, 'Y', 4999.99, 5000.00, 1000.00, '2017-11-05', '2022-11-30', 0.00, 4999.99, '94102', 'GRP003'),
(00000000007, 'Y', 100.00, 15000.00, 3000.00, '2023-01-01', '2028-01-31', 1000.00, 1100.00, '02101', 'GRP001'),
(00000000008, 'Y', 2100.50, 8000.00, 1600.00, '2020-09-15', '2025-09-30', 300.00, 2400.50, '33101', 'GRP004'),
(00000000009, 'Y', 0.00,   20000.00, 4000.00, '2016-04-22', '2021-04-30', 0.00, 0.00, '98101', 'GRP004'),
(00000000010, 'Y', 599.99,  4000.00, 800.00,  '2021-10-30', '2026-10-31', 50.00, 649.99, '85001', 'GRP005');
```

### 9.3 transaction_types Seed Data (matches TRNTYPE DB2 source)

```sql
INSERT INTO transaction_types (transaction_type_code, description) VALUES
('PR', 'Purchase Regular'),
('RR', 'Return Regular'),
('CI', 'Cash In'),
('CO', 'Cash Out'),
('FE', 'Fee'),
('IN', 'Interest Charge'),
('PA', 'Payment'),
('AT', 'ATM Withdrawal'),
('TP', 'Transfer Payment'),
('CR', 'Credit Adjustment');
```

---

## 10. EBCDIC Code Page Reference

All z/OS VSAM files use IBM EBCDIC code page 037 (US English) unless the system is configured for a different national language. Python's `codecs` module supports this via `'cp037'` codec.

**Character class verification** (apply to extracted strings as sanity checks):
- Alphabetic characters (A-Z, a-z): EBCDIC ranges C1-E9, 81-A9
- Digits (0-9): EBCDIC F0-F9
- Space: EBCDIC 40
- Special characters used in COBOL data: `-` (60), `.` (4B), `/` (61), `+` (4E)

**Practical verification test**:
```python
assert 'ADMIN001'.encode('cp037').hex() == 'c1c4d4c9d5f0f0f1'
assert ''.join([chr(b) for b in bytes.fromhex('c1c4d4c9d5f0f0f1').decode('cp037')]) == 'ADMIN001'
```

If VSAM files were transferred to the migration host using FTP in text mode, EBCDIC conversion may have already occurred (ASCII on migration host). In that case, use `'ascii'` or `'utf-8'` codec instead of `'cp037'`. Verify by inspecting first-record bytes against known key values before running the full migration.

---

*Specification covers migration of 44 COBOL programs' data from 6 VSAM files, 3 DB2 tables, and 2 IMS databases. All sensitive data handling requirements (PCI-DSS, SSN encryption, password hashing) are mandatory and must not be relaxed for any environment including development.*
