# Security Specification: Authentication, Authorization, and Data Protection

## Document Purpose

Defines the complete security architecture for the CardDemo modernization, replacing the mainframe's VSAM-based plain-text password authentication and implicit CICS session management with JWT-based authentication, bcrypt password hashing, role-based access control (RBAC), and defense-in-depth data protection. Addresses all known security issues documented in the overall system specification.

---

## 1. Security Issues in the Legacy System

The following security deficiencies in the COBOL source are explicitly documented in `overall-system-specification.md` section 12 and must be corrected in the modern system:

| Issue | COBOL Location | Legacy Behavior | Modern Correction |
|-------|---------------|-----------------|-------------------|
| Plain-text password storage | USRSEC VSAM, COSGN00C | SEC-USR-PWD X(8) stored and compared as plain text | bcrypt hash; password never stored in plain text |
| No session timeout | All CICS programs | No idle timeout; sessions persist until terminal disconnect | JWT `exp` claim with configurable TTL (default: 3600 seconds) |
| No password masking at rest | USRSEC VSAM | Password readable by any program with VSAM READ access | `password_hash` in PostgreSQL; hash is one-way |
| Unnecessary UPDATE lock | COTRN01C | READ TRANSACT with UPDATE for display-only; holds exclusive lock, creates denial-of-service risk | `GET /api/v1/transactions/{id}` uses SELECT (no lock); no UPDATE lock for read operations |
| Transaction ID race condition | COTRN02C | STARTBR + READPREV + increment → duplicate IDs under concurrent load | PostgreSQL sequence `NEXTVAL('transaction_id_seq')` — atomic, conflict-free |
| ZIP code dropped from MQ reply | COACCT01 | ACCT-ADDR-ZIP read but not included in MQ reply message | ZIP code always included in account API response |
| Missing COMMIT | COBTUPDT | DB2 DML with no COMMIT; changes lost on abnormal end | SQLAlchemy session management with explicit commit/rollback |
| Error continues after ABEND | COBTUPDT | 9999-ABEND sets RC=4 but does not STOP RUN | FastAPI exception handlers terminate request; proper HTTP 500 returned |
| Plain-text SSN storage | CUSTDAT VSAM | CUST-SSN stored as plain-text EBCDIC in VSAM | AES-256 encryption at rest; last 4 digits for display |
| Full PAN storage | CARDDAT, TRANSACT | Full 16-digit card number in VSAM | PCI-compliant masked storage + tokenization |
| CVV persistence | CARDDAT | CARD-CVV-CD X(3) in VSAM record | CVV never stored; discarded during migration and rejected by API |

---

## 2. Authentication Architecture

### 2.1 JWT Token Design

The COBOL system's state management mechanism is the CARDDEMO-COMMAREA passed between programs via CICS RETURN/XCTL. The modern system replaces this with stateless JWT tokens.

**COMMAREA field → JWT claim mapping**:

| CARDDEMO-COMMAREA Field | COBOL PIC | JWT Claim | Type | Notes |
|------------------------|-----------|-----------|------|-------|
| CDEMO-USER-ID | X(8) | `sub` | string | Standard JWT subject |
| CDEMO-USER-TYPE | X(1) | `user_type` | string | 'A' or 'U' |
| CDEMO-FROM-PROGRAM | X(8) | — | — | Replaced by frontend router history |
| CDEMO-TO-PROGRAM | X(8) | — | — | Replaced by Next.js navigation |
| CDEMO-PGM-REENTER | 88-level | — | — | Replaced by HTTP statelessness |
| (system date) | CSDAT01Y | `iat`, `exp` | int | JWT standard claims |

**JWT payload structure**:
```json
{
  "sub": "ADMIN001",
  "user_type": "A",
  "iat": 1700000000,
  "exp": 1700003600,
  "iss": "carddemo-api",
  "jti": "uuid4-unique-token-id"
}
```

**Token configuration**:

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Algorithm | HS256 (development), RS256 (production) | RS256 allows public-key verification by API gateway |
| Access token TTL | 3600 seconds (1 hour) | Replaces indefinite CICS session with bounded lifetime |
| Refresh token TTL | 86400 seconds (24 hours) | Allows re-authentication without full re-login |
| Secret key length | 256 bits minimum | Matches HS256 security level |
| `jti` claim | UUID4, stored in Redis/DB blacklist | Enables token revocation (logout) |

### 2.2 Login Endpoint Behavior

**COBOL source mapping**: COSGN00C `READ-USER-SEC-FILE` paragraph → `POST /api/v1/auth/login`

**COBOL login logic (lines 270–310 of COSGN00C)**:
```
READ USRSEC INTO(SEC-USER-DATA) RIDFLD(SEC-USR-ID)
IF RESP = NORMAL:
    IF CDEMO-SIGNON-PASSWD = SEC-USR-PWD:
        SET CDEMO-USRTYP-ADMIN or CDEMO-USRTYP-USER
        XCTL to COADM01C or COMEN01C
    ELSE: display error
ELSE IF RESP = NOTFND:
    display 'Invalid User ID or Password'
```

**Modern equivalent flow**:
```python
async def login(request: LoginRequest, db: AsyncSession) -> LoginResponse:
    """
    COBOL origin: COSGN00C MAIN-PARA + READ-USER-SEC-FILE paragraph.
    Replaces plain-text VSAM password comparison with bcrypt verification.
    """
    user = await user_repository.get_by_id(db, request.user_id.strip())
    
    # Return identical error for not-found and wrong-password (no enumeration)
    if user is None or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail={"error_code": "INVALID_CREDENTIALS",
                    "message": "Invalid User ID or Password"}
        )
    
    access_token = create_access_token(
        subject=user.user_id,
        user_type=user.user_type,
        expires_delta=timedelta(seconds=settings.ACCESS_TOKEN_EXPIRE_SECONDS)
    )
    return LoginResponse(
        access_token=access_token,
        user_type=user.user_type,
        user_id=user.user_id
    )
```

**Security note**: The COBOL program displays different messages for "user not found" vs. "wrong password" (NOTFND vs. password mismatch). The modern API must return a **uniform error message** ("Invalid User ID or Password") for both conditions to prevent user enumeration attacks. This is a deliberate improvement over the COBOL behavior.

### 2.3 Password Hashing

**COBOL source**: `SEC-USR-PWD PIC X(8)` — 8-character plain-text password

**Modern implementation**:

```python
# app/utils/security.py

from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Work factor; adjust for hardware (aim for ~250ms hash time)
)

def hash_password(plain_password: str) -> str:
    """
    Hash a plain-text password using bcrypt.
    
    COBOL origin: Replaces plain-text SEC-USR-PWD X(8) storage in USRSEC VSAM.
    The COBOL system compared passwords byte-by-byte: 
        IF CDEMO-SIGNON-PASSWD = SEC-USR-PWD
    This is replaced by constant-time bcrypt comparison to prevent timing attacks.
    """
    return pwd_context.hash(plain_password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against its bcrypt hash.
    Uses constant-time comparison to prevent timing side-channel attacks.
    """
    return pwd_context.verify(plain_password, hashed_password)
```

**bcrypt work factor selection**:
- Development: rounds=10 (faster for test runs)
- Production: rounds=12 (target ~250ms per hash; adjust based on server hardware)
- Minimum: rounds=10 (OWASP minimum recommendation 2024)

**Password policy enforcement** (not present in COBOL; new requirement):

| Rule | Implementation |
|------|---------------|
| Minimum length | 8 characters (matches COBOL SEC-USR-PWD length; encourage longer for new accounts) |
| Maximum length | 72 characters (bcrypt limit) |
| Complexity | Recommended but not enforced in API (frontend enforces: 1 uppercase, 1 digit, 1 special) |
| History | Not enforced (no history table; can add later) |
| Expiry | Not enforced initially; `password_reset_required` flag triggers forced reset |

### 2.4 Token Validation Middleware

```python
# app/api/dependencies.py

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

security_scheme = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Validate JWT token and return the authenticated user.
    
    COBOL origin: Replaces EIBCALEN check (IF EIBCALEN = 0: XCTL to COSGN00C).
    In COBOL, EIBCALEN=0 means no COMMAREA — unauthenticated entry.
    This dependency raises 401 for any request without a valid JWT.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"error_code": "INVALID_TOKEN", "message": "Could not validate credentials"},
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await user_repository.get_by_id(db, user_id)
    if user is None:
        raise credentials_exception
    return user

async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Enforce admin-only access.
    
    COBOL origin: Replaces CDEMO-USRTYP-ADMIN check.
    Admin screens (COADM01C and its sub-screens) check CDEMO-USER-TYPE='A'.
    All user management and transaction type management endpoints require this dependency.
    """
    if current_user.user_type != 'A':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error_code": "ADMIN_REQUIRED",
                    "message": "This function requires administrator privileges"}
        )
    return current_user
```

---

## 3. Role-Based Access Control (RBAC)

### 3.1 Role Definitions

The COBOL system has exactly two roles, derived from `SEC-USR-TYPE X(1)` in USRSEC VSAM:

| COBOL Value | Role Name | Description |
|-------------|-----------|-------------|
| `'A'` | ADMIN | Administrator: full access including user management and transaction type management |
| `'U'` | USER | Regular user: access to account/card/transaction/billing/reports; no user management |

These two roles are preserved exactly in the modern system. No additional roles are introduced.

### 3.2 Endpoint Authorization Matrix

Complete mapping of all API endpoints to required role and originating COBOL program:

#### Authentication (no role required)

| Method | Endpoint | COBOL Program | Required Role |
|--------|---------|---------------|---------------|
| POST | `/api/v1/auth/login` | COSGN00C | None (public) |
| POST | `/api/v1/auth/refresh` | — (new) | None (valid refresh token) |
| POST | `/api/v1/auth/logout` | COSGN00C PF3/exit | Authenticated (any) |

#### Account Management

| Method | Endpoint | COBOL Program | Required Role |
|--------|---------|---------------|---------------|
| GET | `/api/v1/accounts/{account_id}` | COACTVWC | USER or ADMIN |
| GET | `/api/v1/accounts/{account_id}/customer` | COACTVWC | USER or ADMIN |
| PUT | `/api/v1/accounts/{account_id}` | COACTUPC | USER or ADMIN |

#### Credit Card Management

| Method | Endpoint | COBOL Program | Required Role |
|--------|---------|---------------|---------------|
| GET | `/api/v1/cards` | COCRDLIC | USER or ADMIN |
| GET | `/api/v1/cards/{card_number}` | COCRDSLC | USER or ADMIN |
| PUT | `/api/v1/cards/{card_number}` | COCRDUPC | USER or ADMIN |

#### Transaction Management

| Method | Endpoint | COBOL Program | Required Role |
|--------|---------|---------------|---------------|
| GET | `/api/v1/transactions` | COTRN00C | USER or ADMIN |
| GET | `/api/v1/transactions/{transaction_id}` | COTRN01C | USER or ADMIN |
| POST | `/api/v1/transactions` | COTRN02C | USER or ADMIN |

#### Billing

| Method | Endpoint | COBOL Program | Required Role |
|--------|---------|---------------|---------------|
| GET | `/api/v1/billing/account/{account_id}` | COBIL00C (lookup phase) | USER or ADMIN |
| POST | `/api/v1/billing/payment` | COBIL00C (confirm phase) | USER or ADMIN |

#### Reports

| Method | Endpoint | COBOL Program | Required Role |
|--------|---------|---------------|---------------|
| POST | `/api/v1/reports/request` | CORPT00C | USER or ADMIN |
| GET | `/api/v1/reports/status/{job_id}` | — (new) | USER or ADMIN |

#### User Management (ADMIN only)

| Method | Endpoint | COBOL Program | Required Role |
|--------|---------|---------------|---------------|
| GET | `/api/v1/users` | COUSR00C | **ADMIN** |
| POST | `/api/v1/users` | COUSR01C | **ADMIN** |
| GET | `/api/v1/users/{user_id}` | COUSR02C (lookup) | **ADMIN** |
| PUT | `/api/v1/users/{user_id}` | COUSR02C (update) | **ADMIN** |
| DELETE | `/api/v1/users/{user_id}` | COUSR03C | **ADMIN** |

#### Transaction Type Management (ADMIN only)

| Method | Endpoint | COBOL Program | Required Role |
|--------|---------|---------------|---------------|
| GET | `/api/v1/transaction-types` | COTRTLIC | **ADMIN** |
| POST | `/api/v1/transaction-types` | COTRTUPC | **ADMIN** |
| PUT | `/api/v1/transaction-types/{type_code}` | COTRTUPC | **ADMIN** |
| DELETE | `/api/v1/transaction-types/{type_code}` | COTRTLIC | **ADMIN** |

#### Pending Authorizations (ADMIN only)

| Method | Endpoint | COBOL Program | Required Role |
|--------|---------|---------------|---------------|
| GET | `/api/v1/authorizations` | COPAUS0C | **ADMIN** |
| GET | `/api/v1/authorizations/{card_number}` | COPAUS1C | **ADMIN** |
| POST | `/api/v1/authorizations/{card_number}/fraud-flag` | COPAUS2C | **ADMIN** |

**Rationale for authorization scope**: The COBOL system makes admin-only functions accessible only via COADM01C (admin menu). Regular users start at COMEN01C and cannot navigate to admin screens. The modern API enforces this at the HTTP layer via the `require_admin` dependency on all `/users`, `/transaction-types`, and `/authorizations` endpoints.

---

## 4. Data Protection

### 4.1 Sensitive Field Protection Matrix

| Data Element | COBOL Storage | Modern Storage | Protection Method |
|--------------|--------------|----------------|------------------|
| User password | SEC-USR-PWD X(8) plain text | `users.password_hash VARCHAR(255)` | bcrypt(rounds=12) one-way hash |
| Customer SSN | CUST-SSN X(10) plain text | `customers.ssn_encrypted VARCHAR(255)` + `ssn_last_four CHAR(4)` | AES-256-GCM with KMS-managed key |
| Full card number (PAN) | CARD-NUM X(16) plain text | `credit_cards.card_number_masked VARCHAR(19)` + `card_number_token CHAR(64)` | SHA-256 HMAC token; masked display |
| Card CVV | CARD-CVV-CD X(3) plain text | **Never stored** | Discarded at extraction/API boundary |
| Card expiry date | CARD-EXPIRAION-DATE X(8) | `credit_cards.expiration_date DATE` | No special protection (non-sensitive alone) |
| Transaction amounts | TRAN-AMT S9(10)V99 COMP-3 | `transactions.transaction_amount NUMERIC(12,2)` | Database access control |

### 4.2 API Response Field Masking

The following fields must be masked in all API responses regardless of caller role:

| Field | Raw Value | Masked Response Value |
|-------|-----------|----------------------|
| `card_number` | `4111111111111111` | `411111XXXXXX1111` |
| `ssn` | `123456789` | `XXX-XX-6789` |
| `password_hash` | `$2b$12$...` | **Never returned in any response** |

**Implementation**:
```python
# app/schemas/card_schemas.py

class CreditCardResponse(BaseModel):
    card_number_masked: str    # "411111XXXXXX1111" — never return full PAN
    account_id: int
    embossed_name: str
    expiration_date: Optional[date]
    active_status: str
    # card_number_token is internal; never serialized to response
    
    class Config:
        # Explicitly exclude card_number_token from serialization
        fields = {'card_number_token': {'exclude': True}}

class UserResponse(BaseModel):
    user_id: str
    first_name: str
    last_name: str
    user_type: str
    created_at: datetime
    updated_at: datetime
    # password_hash is excluded — must NEVER appear in any response

class CustomerResponse(BaseModel):
    customer_id: int
    first_name: str
    last_name: str
    ssn_last_four: str         # Only last 4 digits
    # ssn_encrypted is excluded — never returned
    date_of_birth: Optional[date]
    phone_number_1: Optional[str]
    account_id: int
```

### 4.3 Transport Security

| Layer | Requirement |
|-------|-------------|
| All API endpoints | HTTPS only (TLS 1.2 minimum; TLS 1.3 preferred) |
| HTTP → HTTPS redirect | Enforced at load balancer / nginx |
| HSTS header | `Strict-Transport-Security: max-age=31536000; includeSubDomains` |
| JWT transmission | `Authorization: Bearer` header only; never in URL query params |
| Cookie security | If cookies used for refresh token: `HttpOnly; Secure; SameSite=Strict` |

### 4.4 Database Connection Security

| Parameter | Requirement |
|-----------|-------------|
| Connection string | Read from environment variable `DATABASE_URL`; never hardcoded |
| TLS to PostgreSQL | `sslmode=require` in connection string |
| Database user | Application connects with least-privilege user (SELECT/INSERT/UPDATE/DELETE on app tables only; no DDL) |
| Separate migration user | DDL operations (CREATE TABLE, ALTER) use a separate migration-role user, not the app user |

---

## 5. Input Validation and Injection Prevention

### 5.1 SQL Injection Prevention

The COBOL system accesses VSAM via CICS file control commands (READ, WRITE, REWRITE, DELETE) — not SQL. There is no SQL injection risk in the COBOL source. The modern system introduces SQL (PostgreSQL) and must prevent injection.

**Approach**: All database queries use SQLAlchemy ORM or parameterized queries exclusively. No raw SQL string concatenation is permitted anywhere in the codebase.

```python
# CORRECT — parameterized query via SQLAlchemy ORM:
result = await db.execute(
    select(User).where(User.user_id == user_id)
)

# CORRECT — parameterized raw SQL:
result = await db.execute(
    text("SELECT * FROM users WHERE user_id = :uid"),
    {"uid": user_id}
)

# NEVER — string concatenation (SQL injection risk):
# result = await db.execute(f"SELECT * FROM users WHERE user_id = '{user_id}'")
```

### 5.2 Pydantic Validation as Input Sanitization

All API inputs pass through Pydantic models before reaching service or repository layers. This provides automatic type checking, length limits, and pattern validation.

**Key validation rules mapped from COBOL field definitions**:

| COBOL Field | COBOL PIC | Pydantic Validator |
|------------|-----------|-------------------|
| USRIDINI (user ID lookup) | X(8) | `Field(..., min_length=1, max_length=8, pattern=r'^[A-Za-z0-9]+$')` |
| FNAMEI (first name) | X(20) | `Field(..., min_length=1, max_length=20)` |
| LNAMEI (last name) | X(20) | `Field(..., min_length=1, max_length=20)` |
| PASSWDI (password) | X(8)→expanded | `Field(..., min_length=8, max_length=72)` |
| USRTYPEI (user type) | X(1) | `Field(..., pattern=r'^[AU]$')` |
| ACTIDIN (account ID) | 9(11) | `Field(..., gt=0, le=99999999999)` |
| CARDNIN (card number) | X(16) | `Field(..., min_length=16, max_length=16, pattern=r'^\d{16}$')` |
| TRNIDIN (transaction ID) | X(16) | `Field(..., min_length=1, max_length=16)` |
| TRAN-AMT | S9(10)V99 | `Field(..., gt=Decimal('0'), le=Decimal('9999999999.99'))` |

### 5.3 XSS Prevention

The Next.js frontend is the primary XSS exposure surface. Server-side rendering (SSR) with React's JSX escaping provides automatic XSS prevention. Additional mitigations:

| Control | Implementation |
|---------|---------------|
| Content Security Policy | `next.config.js` headers: `Content-Security-Policy: default-src 'self'; script-src 'self'` |
| `dangerouslySetInnerHTML` | Never used; all dynamic content rendered via JSX |
| User-provided strings | All merchant names, user names displayed via React text nodes (auto-escaped) |

### 5.4 CSRF Prevention

Since the frontend uses JWT in `Authorization` header (not cookies), CSRF is inherently prevented — CSRF attacks cannot set the `Authorization` header. If cookies are used for refresh tokens, add CSRF protection:

```python
# If refresh token is in cookie:
# app/middleware/csrf.py
# Verify Origin/Referer header matches expected domain for all state-changing requests
```

---

## 6. Audit Logging

The COBOL system has no centralized audit logging. The mainframe's CICS journal and SMF records provide some audit capability, but no application-level audit trail exists.

The modern system implements structured audit logging for all state-changing operations:

### 6.1 Audit Events

| Event | Trigger | Log Level |
|-------|---------|-----------|
| User login success | `POST /auth/login` 200 | INFO |
| User login failure | `POST /auth/login` 401 | WARNING |
| User logout | `POST /auth/logout` | INFO |
| User created | `POST /users` | INFO |
| User updated | `PUT /users/{id}` | INFO |
| User deleted | `DELETE /users/{id}` | INFO |
| Account updated | `PUT /accounts/{id}` | INFO |
| Card updated | `PUT /cards/{id}` | INFO |
| Transaction created | `POST /transactions` | INFO |
| Bill payment posted | `POST /billing/payment` | INFO |
| Fraud flag toggled | `POST /authorizations/{id}/fraud-flag` | WARNING |
| Failed authorization attempt | `POST /auth/login` 401 | WARNING |
| 403 Forbidden access attempt | Any 403 response | WARNING |
| 500 Internal Server Error | Any 5xx response | ERROR |

### 6.2 Audit Log Structure

```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "event_type": "USER_DELETED",
  "actor_user_id": "ADMIN001",
  "actor_user_type": "A",
  "target_resource": "/api/v1/users/USER0005",
  "target_id": "USER0005",
  "http_method": "DELETE",
  "http_status": 200,
  "request_id": "uuid4-request-id",
  "client_ip": "10.0.0.1",
  "details": {
    "deleted_user_type": "U",
    "deleted_first_name": "George"
  }
}
```

### 6.3 Implementation

```python
# app/utils/audit_logger.py

import structlog
from uuid import uuid4

audit_log = structlog.get_logger("audit")

def log_audit_event(
    event_type: str,
    actor: User,
    target_resource: str,
    target_id: str,
    http_status: int,
    details: dict = None
) -> None:
    """
    Emit a structured audit log event.
    
    COBOL origin: No equivalent in legacy system.
    New requirement for compliance and operational visibility.
    All state-changing operations (CUD in CRUD) emit audit events.
    """
    audit_log.info(
        event_type,
        actor_user_id=actor.user_id if actor else "anonymous",
        actor_user_type=actor.user_type if actor else None,
        target_resource=target_resource,
        target_id=target_id,
        http_status=http_status,
        request_id=str(uuid4()),
        **(details or {})
    )
```

---

## 7. Security Headers

Configure the following HTTP security headers in `app/main.py` or the nginx reverse proxy:

```python
# app/middleware/security_headers.py

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "0"  # Disable legacy XSS filter
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        # Note: HSTS set at nginx/load balancer level, not app level
        return response
```

---

## 8. Secrets Management

| Secret | Storage | Access Pattern |
|--------|---------|---------------|
| `JWT_SECRET_KEY` | Environment variable (AWS Secrets Manager / HashiCorp Vault) | Read at startup; cached in memory |
| `DATABASE_URL` | Environment variable | Read at startup |
| `SSN_ENCRYPTION_KEY` | AWS KMS key ID or Vault path | Retrieved per-request (with local cache) |
| `CARD_TOKEN_HMAC_KEY` | Environment variable | Read at startup; cached in memory |
| bcrypt work factor | `settings.py` configuration | Hardcoded constant (not a secret) |

**Implementation via `app/config.py`**:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # JWT
    SECRET_KEY: str                          # Min 256-bit random value
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 3600
    REFRESH_TOKEN_EXPIRE_SECONDS: int = 86400
    
    # Encryption
    SSN_ENCRYPTION_KEY_ID: str               # AWS KMS key ID or Vault path
    CARD_TOKEN_HMAC_KEY: str                 # Hex-encoded 256-bit key
    
    # Security
    BCRYPT_ROUNDS: int = 12
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

**Never**:
- Commit `.env` files to version control
- Log secret values (JWT payloads, passwords, card numbers) in application logs
- Return `password_hash` in any API response
- Store the full PAN in any database table in the modern system

---

## 9. CORS Configuration

The Next.js frontend and FastAPI backend run on different ports/domains in development and may be on different subdomains in production. CORS must be configured correctly.

```python
# app/main.py

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,    # ["https://carddemo.example.com"] in prod
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Total-Count", "X-Page", "X-Page-Size"],
)
```

**Production CORS**: `CORS_ORIGINS` must list only the exact production frontend URL. Wildcard (`*`) is never permitted when `allow_credentials=True`.

---

## 10. Rate Limiting

The COBOL system has no rate limiting (CICS session management provides natural throttling via 3270 terminal capacity). The REST API must implement rate limiting to prevent brute-force attacks.

| Endpoint | Limit | Window | Action on Exceed |
|----------|-------|--------|-----------------|
| `POST /auth/login` | 5 attempts | 1 minute per IP | 429 Too Many Requests; exponential backoff message |
| All authenticated endpoints | 1000 requests | 1 minute per user | 429 Too Many Requests |
| `POST /transactions` | 10 creates | 1 minute per user | 429 Too Many Requests |
| `DELETE /users/{id}` | 5 deletes | 1 minute per admin | 429 Too Many Requests |

**Implementation**: Use `slowapi` library (FastAPI-compatible rate limiter using Redis for distributed state):

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# On login endpoint:
@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, credentials: LoginRequest, ...):
    ...
```

---

## 11. Known Issues Resolution Summary

All security issues from the legacy system's Known Issues section are addressed as follows:

| Legacy Issue | Resolution | Document Reference |
|-------------|------------|-------------------|
| Plain-text passwords | bcrypt(rounds=12) hashing | Section 2.3 |
| No session timeout | JWT `exp` claim = 3600 seconds | Section 2.1 |
| No password masking at rest | `password_hash`; hash is one-way | Section 2.3 |
| READ UPDATE for display-only (COTRN01C) | GET uses SELECT; no lock held | Section 1 (table) |
| Transaction ID race condition (COTRN02C) | PostgreSQL `NEXTVAL` sequence | Section 1 (table) |
| ZIP code dropped from MQ reply (COACCT01) | ZIP always in account API response | Section 1 (table) |
| Missing COMMIT (COBTUPDT) | SQLAlchemy session with explicit commit | Section 1 (table) |
| Error continues after ABEND (COBTUPDT) | FastAPI exception handlers terminate request | Section 1 (table) |
| Plain-text SSN | AES-256 encryption; last-4 for display | Section 4.1 |
| Full PAN in plain text | Masked + HMAC token; CVV discarded | Section 4.1, 5.3 |
| No centralized audit logging | Structured audit events on all CUD operations | Section 6 |
| No rate limiting | `slowapi` with 5/min on login endpoint | Section 10 |
| User enumeration on login | Uniform 401 response for all credential failures | Section 2.2 |

---

*This security specification mandates bcrypt password hashing, AES-256 SSN encryption, PCI-compliant card number masking, JWT session management, RBAC enforcement at every endpoint, and structured audit logging. All 13 known security and code-quality issues from the legacy system are explicitly resolved.*
