# Technical Specification: COADM01C — Admin Menu

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| Program ID | COADM01C |
| Source File | `app/cbl/COADM01C.cbl` |
| Type | CICS Online |
| Transaction ID | CA00 |
| BMS Mapset | COADM01 |
| BMS Map | COADM1A |

## 2. Purpose

COADM01C is the **admin navigation menu** for administrator-type users. It is structurally identical to COMEN01C but uses the COADM02Y copybook for admin-specific menu options (up to 6 options).

## 3. Copybooks Used

| Copybook | Purpose |
|----------|---------|
| COCOM01Y | CARDDEMO-COMMAREA |
| COADM02Y | Admin menu option array (6 options) |
| COADM01 | BMS symbolic map |
| COTTL01Y | Application title strings |
| CSDAT01Y | Date/time working storage |
| CSMSG01Y | Common screen messages |
| CSUSR01Y | User record layout |
| DFHAID | CICS AID constants |
| DFHBMSCA | BMS field attribute constants |

## 4. VSAM Files Accessed

None directly.

## 5. Menu Options (from COADM02Y)

| Option | Display Name | Target Program |
|--------|-------------|----------------|
| 01 | User List (Security) | COUSR00C |
| 02 | User Add (Security) | COUSR01C |
| 03 | User Update (Security) | COUSR02C |
| 04 | User Delete (Security) | COUSR03C |
| 05 | Transaction Type List/Update (Db2) | COTRTLIC |
| 06 | Transaction Type Maintenance (Db2) | COTRTUPC |

## 6. Screen Fields

### Input Fields
| Field | Length | Type | Description |
|-------|--------|------|-------------|
| OPTION | 2 | X(2), NUM | 2-digit option number |

### Function Keys
| Key | Action |
|-----|--------|
| ENTER | Navigate to selected option |
| PF3 | Return to COSGN00C |

## 7. Program Flow

Identical pattern to COMEN01C:
1. Validate EIBCALEN > 0 (else redirect to COSGN00C)
2. Build menu from COADM02Y array
3. On ENTER: validate option in range 1..6, check for 'DUMMY' programs
4. XCTL to selected program with COMMAREA
5. PF3: XCTL to COSGN00C

## 8. Inter-Program Communication

### Programs Called
| Target | Method | Condition |
|--------|--------|-----------|
| COUSR00C–COUSR03C | XCTL | User management options |
| COTRTLIC, COTRTUPC | XCTL | Transaction type maintenance |
| COSGN00C | XCTL | PF3 |

## 9. Error Handling

- Uses EXEC CICS HANDLE CONDITION PGMIDERR for runtime program-not-found traps.
- Programs starting with 'DUMMY' display "not installed" message.
