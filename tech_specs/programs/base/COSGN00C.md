# Technical Specification: COSGN00C

## 1. Program Overview

| Attribute        | Value                                                |
|------------------|------------------------------------------------------|
| Program ID       | COSGN00C                                             |
| Source File      | app/cbl/COSGN00C.cbl                                 |
| Application      | CardDemo                                             |
| Type             | CICS COBOL Program (Online)                          |
| Transaction ID   | CC00 (WS-TRANID, line 37)                            |
| Function         | CardDemo signon screen. Accepts user ID and password from BMS map COSGN0A. Reads USRSEC VSAM file to authenticate. On success, sets up CARDDEMO-COMMAREA with user info and XCTLs to COADM01C (admin users) or COMEN01C (regular users). PF3 sends thank-you message and exits cleanly. EXEC CICS ASSIGN APPLID/SYSID used to populate screen header with system identifiers. |

---

## 2. Program Flow

### High-Level Flow

```
ENTRY (CICS RETURN with TRANSID=CC00 and COMMAREA, or cold start)

Clear WS-MESSAGE; SET ERR-FLG-OFF

IF EIBCALEN = 0:
    MOVE LOW-VALUES TO COSGN0AO
    PERFORM SEND-SIGNON-SCREEN (first display, no receive)
ELSE:
    MOVE DFHCOMMAREA(1:EIBCALEN) TO CARDDEMO-COMMAREA
    PERFORM RECEIVE-SIGNON-SCREEN
    EVALUATE EIBAID:
        WHEN DFHENTER: PERFORM PROCESS-ENTER-KEY
        WHEN DFHPF3:   PERFORM RETURN-TO-PREV-SCREEN
        WHEN OTHER:    Set ERR-FLG-ON; CCDA-MSG-INVALID-KEY; SEND-SIGNON-SCREEN

EXEC CICS RETURN TRANSID('CC00') COMMAREA(CARDDEMO-COMMAREA)
```

### Paragraph-Level Detail

| Paragraph              | Lines     | Description |
|------------------------|-----------|-------------|
| MAIN-PARA              | 74–113    | Main entry: EIBCALEN check; first/reenter dispatch; AID evaluate; CICS RETURN |
| PROCESS-ENTER-KEY      | 118–183   | Trim WS-USER-ID; validate non-blank; READ USRSEC; check RESP; compare password; set user info in COMMAREA; XCTL based on user type |
| RETURN-TO-PREV-SCREEN  | 188–200   | Move CCDA-MSG-THANK-YOU to WS-MESSAGE; PERFORM SEND-SIGNON-SCREEN; bare EXEC CICS RETURN (no TRANSID — ends session) |
| SEND-SIGNON-SCREEN     | 205–220   | POPULATE-HEADER-INFO; MOVE WS-MESSAGE to ERRMSGO; CICS SEND MAP('COSGN0A') MAPSET('COSGN00') FROM(COSGN0AO) ERASE |
| RECEIVE-SIGNON-SCREEN  | 225–235   | CICS RECEIVE MAP('COSGN0A') MAPSET('COSGN00') INTO(COSGN0AI) RESP RESP2 |
| POPULATE-HEADER-INFO   | 240–261   | EXEC CICS ASSIGN APPLID(WS-APPLID) SYSID(WS-SYSID); fill TITLE01O, TITLE02O, TRNNAMEO, PGMNAMEO, CURDATEO, CURTIMEO; APPLID and SYSID placed in header fields |

---

## 3. Data Structures

### Copybooks Referenced

| Copybook  | Used In              | Contents |
|-----------|----------------------|----------|
| COCOM01Y  | WORKING-STORAGE (line 49) | CARDDEMO-COMMAREA: CDEMO-GENERAL-INFO (CDEMO-FROM-PROGRAM, CDEMO-TO-PROGRAM, CDEMO-PGM-REENTER, CDEMO-USRTYP-ADMIN, etc.), CDEMO-CUSTOMER-INFO, CDEMO-ACCOUNT-INFO, menu option tables |
| COSGN00  | WORKING-STORAGE (line 51)  | BMS mapset copybook: COSGN0AI (input map), COSGN0AO (output map); contains USRIDL/USRIDI, PASSWDL/PASSWDI, ERRMSGO, TITLE01O, TITLE02O, TRNNAMEO, PGMNAMEO, CURDATEO, CURTIMEO |
| COTTL01Y  | WORKING-STORAGE (line 53) | Screen title constants CCDA-TITLE01, CCDA-TITLE02 |
| CSDAT01Y  | WORKING-STORAGE (line 54) | Current date/time working storage fields |
| CSMSG01Y  | WORKING-STORAGE (line 55) | Common messages: CCDA-MSG-INVALID-KEY, CCDA-MSG-THANK-YOU |
| CSUSR01Y  | WORKING-STORAGE (line 56) | Signed-on user data: SEC-USR-ID, SEC-USR-PWD, SEC-USR-FNAME, SEC-USR-LNAME, SEC-USR-TYPE, SEC-USR-FILLER; maps to USRSEC record layout |
| DFHAID    | WORKING-STORAGE (line 58) | EIBAID constants: DFHENTER, DFHPF3 |
| DFHBMSCA  | WORKING-STORAGE (line 59) | BMS attribute byte constants |

### Key Working Storage Variables

| Variable             | PIC       | Purpose |
|----------------------|-----------|---------|
| WS-PGMNAME           | X(08) = 'COSGN00C' | Program name for screen header |
| WS-TRANID            | X(04) = 'CC00' | Transaction ID for CICS RETURN |
| WS-MESSAGE           | X(80)     | User-visible message moved to ERRMSGO |
| WS-ERR-FLG           | X(01)     | 'Y'=error; 'N'=ok; 88 ERR-FLG-ON/ERR-FLG-OFF |
| WS-RESP-CD / WS-REAS-CD | S9(09) COMP | CICS response/reason codes |
| WS-USER-ID           | X(08)     | User ID entered on screen (from USRIDI); trimmed of trailing spaces |
| WS-USER-PWD          | X(08)     | Password entered on screen (from PASSWDI) |
| WS-USRSEC-FILE       | X(08) = 'USRSEC  ' | CICS file name for user security file |
| WS-APPLID            | X(08)     | CICS application ID from EXEC CICS ASSIGN APPLID |
| WS-SYSID             | X(04)     | CICS system ID from EXEC CICS ASSIGN SYSID |

### USRSEC Record Layout (from CSUSR01Y)

| Field         | PIC      | Purpose |
|---------------|----------|---------|
| SEC-USR-ID    | X(08)    | User ID — VSAM KSDS key |
| SEC-USR-PWD   | X(08)    | Plain-text password |
| SEC-USR-FNAME | X(20)    | First name |
| SEC-USR-LNAME | X(20)    | Last name |
| SEC-USR-TYPE  | X(01)    | User type: 'A'=Admin, 'R'=Regular |
| SEC-USR-FILLER| X(23)    | Unused filler |

---

## 4. CICS Commands Used

| Command | Where | Purpose |
|---------|-------|---------|
| EXEC CICS RETURN TRANSID('CC00') COMMAREA(CARDDEMO-COMMAREA) | MAIN-PARA | Pseudo-conversational return |
| EXEC CICS READ FILE(WS-USRSEC-FILE) INTO(CDEMO-USRSEC-REC) RIDFLD(WS-USER-ID) RESP RESP2 | PROCESS-ENTER-KEY | Authenticate user by reading USRSEC by user ID key |
| EXEC CICS XCTL PROGRAM('COADM01C') COMMAREA(CARDDEMO-COMMAREA) | PROCESS-ENTER-KEY | Transfer to admin menu for admin users |
| EXEC CICS XCTL PROGRAM('COMEN01C') COMMAREA(CARDDEMO-COMMAREA) | PROCESS-ENTER-KEY | Transfer to main menu for regular users |
| EXEC CICS SEND MAP('COSGN0A') MAPSET('COSGN00') FROM(COSGN0AO) ERASE | SEND-SIGNON-SCREEN | Display signon screen |
| EXEC CICS RECEIVE MAP('COSGN0A') MAPSET('COSGN00') INTO(COSGN0AI) RESP RESP2 | RECEIVE-SIGNON-SCREEN | Receive user ID and password |
| EXEC CICS ASSIGN APPLID(WS-APPLID) SYSID(WS-SYSID) | POPULATE-HEADER-INFO | Retrieve CICS system identifiers for screen header |
| EXEC CICS RETURN (bare, no TRANSID) | RETURN-TO-PREV-SCREEN (PF3 path) | Ends CICS task cleanly; no re-entry |

---

## 5. File/Dataset Access

| File Name | CICS File | Access Type | Key   | Purpose |
|-----------|-----------|-------------|-------|---------|
| USRSEC    | USRSEC    | READ        | WS-USER-ID (X(08)) | Authenticate user and retrieve user type, name |

**READ behavior:**
- RESP=DFHRESP(NORMAL) (0): user found; compare SEC-USR-PWD to WS-USER-PWD
- RESP=DFHRESP(NOTFND) (13): user not found; display 'Invalid credentials' message
- Other RESP: display generic error message with RESP/RESP2 codes

**Security note**: Password comparison is plain-text equality: `IF SEC-USR-PWD = WS-USER-PWD`. No hashing or encryption.

---

## 6. Screen Interaction

| BMS Mapset | BMS Map | Transaction |
|------------|---------|-------------|
| COSGN00    | COSGN0A | CC00        |

**Key Screen Fields:**

| Field      | Direction | Description |
|------------|-----------|-------------|
| USRIDI     | Input     | User ID entered by operator (8 characters) |
| PASSWDI    | Input     | Password (non-display attribute in BMS map) |
| ERRMSGO    | Output    | WS-MESSAGE: error or status message |
| TITLE01O   | Output    | Application title line 1 |
| TITLE02O   | Output    | Application title line 2 |
| TRNNAMEO   | Output    | Transaction ID (CC00) |
| PGMNAMEO   | Output    | Program name (COSGN00C); also includes APPLID/SYSID from ASSIGN |
| CURDATEO   | Output    | Current date MM/DD/YY |
| CURTIMEO   | Output    | Current time HH:MM:SS |

**Navigation:**
- ENTER: authenticate and transfer to appropriate menu
- PF3: display thank-you message, send screen, then bare CICS RETURN (session ends)
- Other keys: display CCDA-MSG-INVALID-KEY, re-send map

---

## 7. Called Programs / Transfers

| Program    | Method       | Condition |
|------------|--------------|-----------|
| COADM01C   | CICS XCTL   | Authentication succeeds AND SEC-USR-TYPE='A' (admin) |
| COMEN01C   | CICS XCTL   | Authentication succeeds AND SEC-USR-TYPE != 'A' (regular user) |

**COMMAREA passed on XCTL:**
- CDEMO-FROM-PROGRAM = 'COSGN00C'
- CDEMO-FROM-TRANID = 'CC00'
- CDEMO-PGM-REENTER = FALSE (new entry)
- CDEMO-USRTYP-ADMIN = TRUE/FALSE based on SEC-USR-TYPE
- CDEMO-SIGNED-ON-FLAG = TRUE
- CDEMO-USER-ID, CDEMO-USER-FNAME, CDEMO-USER-LNAME populated from USRSEC record

---

## 8. Error Handling

| Condition | Action |
|-----------|--------|
| EIBCALEN = 0 | First display: send signon screen (no receive needed) |
| Blank user ID (after trimming) | ERR-FLG-ON; 'Please enter your user id...' message; re-send map |
| USRSEC READ RESP = NOTFND (13) | 'Invalid User ID or Password' message; re-send map |
| USRSEC READ RESP = other | Generic error with RESP/RESP2 codes displayed; re-send map |
| Password mismatch (SEC-USR-PWD != WS-USER-PWD) | 'Invalid User ID or Password' message; re-send map |
| Invalid AID key (not ENTER or PF3) | ERR-FLG-ON; CCDA-MSG-INVALID-KEY; re-send map |

**Security observation**: The same 'Invalid User ID or Password' message is used for both user-not-found and password-mismatch conditions, preventing user enumeration.

---

## 9. Business Rules

1. **Entry point**: COSGN00C is the primary application entry point. Transaction CC00 is launched directly by the operator (cold start) or by other programs returning via XCTL.
2. **User type routing**: After successful authentication, user type governs which menu is displayed — SEC-USR-TYPE='A' → COADM01C; all others → COMEN01C.
3. **Plain-text password**: Passwords are stored and compared as plain-text 8-byte strings in the USRSEC file. No encryption or hashing is applied.
4. **APPLID/SYSID in header**: COSGN00C is the only program in the codebase that uses EXEC CICS ASSIGN APPLID/SYSID. These values are placed in the screen header to identify the CICS region and system.
5. **Cold start behavior**: When EIBCALEN=0 (no COMMAREA), the signon screen is sent immediately without attempting to receive (correct for first display).
6. **PF3 clean exit**: PF3 sends CCDA-MSG-THANK-YOU and then executes bare CICS RETURN (no TRANSID), which terminates the CICS task. No re-entry into CC00 occurs.
7. **No error flag on NOTFND**: The NOTFND condition sets WS-MESSAGE and re-sends map but does not necessarily set ERR-FLG-ON (the flag is used internally to prevent double sends; the message display path handles it).

---

## 10. Inputs and Outputs

### Inputs

| Source    | Description |
|-----------|-------------|
| BMS Screen (COSGN0A) | USRIDI — user ID; PASSWDI — password |
| CICS File USRSEC | User security record: ID, password, name, type |
| EXEC CICS ASSIGN | APPLID (8 bytes), SYSID (4 bytes) |

### Outputs

| Destination | Description |
|-------------|-------------|
| BMS Screen (COSGN0A) | Signon screen with header; error/status messages |
| COMMAREA (via XCTL) | Full CARDDEMO-COMMAREA populated with authenticated user info; passed to COADM01C or COMEN01C |

---

## 11. Key Variables and Their Purpose

| Variable           | Purpose |
|--------------------|---------|
| WS-USER-ID         | Trimmed user ID from screen input; used as RIDFLD for USRSEC READ |
| WS-USER-PWD        | Password from screen input; compared to SEC-USR-PWD from USRSEC |
| SEC-USR-TYPE       | User type from USRSEC; drives XCTL routing (admin vs. regular menu) |
| WS-APPLID / WS-SYSID | CICS system identifiers retrieved via ASSIGN; placed in screen header |
| CDEMO-USRTYP-ADMIN | 88-level condition in COMMAREA; set TRUE when SEC-USR-TYPE='A'; governs downstream admin access |
