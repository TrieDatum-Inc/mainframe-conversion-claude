# Technical Specification: DBUNLDGS

## Program Name and Purpose

**Program ID:** DBUNLDGS  
**Source File:** `/app/app-authorization-ims-db2-mq/cbl/DBUNLDGS.CBL`  
**Type:** Batch COBOL IMS Program (GSAM output)  
**Application:** CardDemo - Authorization Module  
**Function:** Unload IMS Pending Authorization Database to GSAM Sequential Datasets

DBUNLDGS reads all PAUTSUM0 (summary) root segments and their PAUTDTL1 (detail) child segments from the IMS authorization database using the DL/I CBLTDLI interface, and writes them to two GSAM (Generalized Sequential Access Method) output datasets — one for root segments and one for child segments. This is an IMS unload utility used for data extract/migration purposes.

The program uses three PCBs passed in the PROCEDURE DIVISION USING clause:
- **PAUTBPCB** — the IMS database PCB for reading the pending auth database (DBD likely PAUTB or similar)
- **PASFLPCB** — the GSAM PCB for the root/summary output flat file
- **PADFLPCB** — the GSAM PCB for the child/detail output flat file

Sequential file I/O is commented out in the source (lines 26–35 show `SELECT OPFILE1/OPFILE2` commented); the actual output uses GSAM ISRT calls.

---

## Artifact Inventory

| Artifact | Type | Role |
|----------|------|------|
| DBUNLDGS.CBL | COBOL Source | Main program |
| CIPAUSMY.cpy | Copybook | IMS PAUTSUM0 segment layout |
| CIPAUDTY.cpy | Copybook | IMS PAUTDTL1 segment layout |
| IMSFUNCS.cpy | Copybook | DL/I function code constants |
| PAUTBPCB.CPY | Copybook | PCB mask for IMS database |
| PASFLPCB.CPY | Copybook | PCB mask for GSAM summary output |
| PADFLPCB.CPY | Copybook | PCB mask for GSAM detail output |

---

## IDENTIFICATION DIVISION Metadata

- **PROGRAM-ID:** DBUNLDGS  
- **AUTHOR:** AWS  
- Note: WS-PGMNAME is coded as 'IMSUNLOD' (line 58), not 'DBUNLDGS' — a discrepancy suggesting the program was cloned from a template named IMSUNLOD.
- Source lines 17–19

---

## ENVIRONMENT DIVISION — FILE-CONTROL

The SELECT statements for OPFILE1 and OPFILE2 are **commented out** (lines 26–35). The file-level FD entries and record definitions are also commented out (lines 43–49). Instead, working-storage record areas are used as GSAM I/O buffers:

```
01 OPFIL1-REC      PIC X(100).        -- summary (root) segment buffer
01 OPFIL2-REC.
   05 ROOT-SEG-KEY PIC S9(11) COMP-3  -- account ID key for pairing
   05 CHILD-SEG-REC PIC X(200)        -- detail segment data
```

---

## DATA DIVISION

### Working-Storage Variables (lines 57–94)

Standard batch housekeeping variables identical in structure to CBPAUP0C (see that spec). Key differences:
- WS-PGMNAME = 'IMSUNLOD' (hardcoded, not 'DBUNLDGS')
- WS-END-OF-ROOT-SEG and WS-END-OF-CHILD-SEG PIC X(01) flags for loop control (replaces the 88-level flags used in CBPAUP0C)
- WS-OUTFL1-STATUS, WS-OUTFL2-STATUS PIC X(02) — file status fields (present but no files opened)

### SSA Definitions (lines 115–121)

```
01 ROOT-UNQUAL-SSA.
   05 FILLER PIC X(08) VALUE 'PAUTSUM0'.
   05 FILLER PIC X(01) VALUE ' '.

01 CHILD-UNQUAL-SSA.
   05 FILLER PIC X(08) VALUE 'PAUTDTL1'.
   05 FILLER PIC X(01) VALUE ' '.
```

Unqualified SSAs select all occurrences of the named segment type in hierarchical order.

### IMS Variables (lines 96–112)

Same 88-level status code structure as CBPAUP0C. PSB name and PCB offset commented out — the program uses explicit PCB arguments in CBLTDLI calls.

---

## Copybooks Referenced

| Copybook | Line | Purpose |
|----------|------|---------|
| IMSFUNCS.cpy | 136 | FUNC-GN, FUNC-GNP, FUNC-ISRT, FUNC-DLET, FUNC-GU, FUNC-REPL, FUNC-GHU, FUNC-GHN, FUNC-GHNP — DL/I function codes |
| CIPAUSMY.cpy | 143 | PENDING-AUTH-SUMMARY segment layout |
| CIPAUDTY.cpy | 147 | PENDING-AUTH-DETAILS segment layout |
| PAUTBPCB.CPY | 154 | PAUTBPCB: PAUT-DBDNAME, PAUT-SEG-LEVEL, PAUT-PCB-STATUS, PAUT-PCB-PROCOPT, PAUT-SEG-NAME, PAUT-KEYFB-NAME, PAUT-NUM-SENSEGS, PAUT-KEYFB (X(255)) |
| PASFLPCB.CPY | 155 | PASFLPCB: PASFL-DBDNAME, PASFL-PCB-STATUS, PASFL-PCB-PROCOPT, PASFL-SEG-NAME, PASFL-KEYFB-NAME, PASFL-NUM-SENSEGS, PASFL-KEYFB (X(100)) |
| PADFLPCB.CPY | 156 | PADFLPCB: PADFL-DBDNAME, PADFL-PCB-STATUS, PADFL-PCB-PROCOPT, PADFL-SEG-NAME, PADFL-KEYFB-NAME, PADFL-NUM-SENSEGS, PADFL-KEYFB (X(255)) |

---

## LINKAGE SECTION (lines 151–161)

```cobol
COPY PAUTBPCB.   -- 01 PAUTBPCB (IMS database PCB)
COPY PASFLPCB.   -- 01 PASFLPCB (GSAM summary output PCB)
COPY PADFLPCB.   -- 01 PADFLPCB (GSAM detail output PCB)
```

```cobol
PROCEDURE DIVISION USING PAUTBPCB
                         PASFLPCB
                         PADFLPCB.
```

The program also defines `ENTRY 'DLITCBL' USING PAUTBPCB PASFLPCB PADFLPCB` at line 165–167 for compatibility with both the standard entry and the DLITCBL entry point convention.

---

## IMS DL/I Calls (CBLTDLI interface)

All calls use CALL 'CBLTDLI' with function codes from IMSFUNCS.cpy.

### 2000-FIND-NEXT-AUTH-SUMMARY — GN call (line 222)

```cobol
CALL 'CBLTDLI' USING FUNC-GN
                     PAUTBPCB
                     PENDING-AUTH-SUMMARY
                     ROOT-UNQUAL-SSA.
```
- Sequentially reads each PAUTSUM0 segment.
- Status check: PAUT-PCB-STATUS = spaces (success); 'GB' (end of database).

### 3000-FIND-NEXT-AUTH-DTL — GNP call (line 267)

```cobol
CALL 'CBLTDLI' USING FUNC-GNP
                     PAUTBPCB
                     PENDING-AUTH-DETAILS
                     CHILD-UNQUAL-SSA.
```
- Reads child PAUTDTL1 segments within current parent.
- Status check: spaces=success; 'GE'=no more children.

### 3100-INSERT-PARENT-SEG-GSAM — ISRT to GSAM (line 302)

```cobol
CALL 'CBLTDLI' USING FUNC-ISRT
                     PASFLPCB
                     PENDING-AUTH-SUMMARY.
```
- Writes the root segment to the GSAM summary output file via PASFLPCB.
- Error if PASFL-PCB-STATUS not spaces.

### 3200-INSERT-CHILD-SEG-GSAM — ISRT to GSAM (line 321)

```cobol
CALL 'CBLTDLI' USING FUNC-ISRT
                     PADFLPCB
                     PENDING-AUTH-DETAILS.
```
- Writes each child segment to the GSAM detail output file via PADFLPCB.
- Error if PADFL-PCB-STATUS not spaces.

---

## Program Flow

### MAIN-PARA (line 164)

```
ENTRY 'DLITCBL' USING PAUTBPCB PASFLPCB PADFLPCB

PERFORM 1000-INITIALIZE

PERFORM 2000-FIND-NEXT-AUTH-SUMMARY
UNTIL WS-END-OF-ROOT-SEG = 'Y'

PERFORM 4000-FILE-CLOSE

GOBACK
```

### 1000-INITIALIZE (line 182)

- ACCEPT current date and Julian date.
- DISPLAY 'STARTING PROGRAM DBUNLDGS::'
- No file opens (OPEN OUTPUT OPFILE1/OPFILE2 commented out).

### 2000-FIND-NEXT-AUTH-SUMMARY (line 216)

```
INITIALIZE PAUT-PCB-STATUS
CALL 'CBLTDLI' GN PAUTBPCB PENDING-AUTH-SUMMARY ROOT-UNQUAL-SSA

IF PAUT-PCB-STATUS = spaces:
    Increment counters
    MOVE PENDING-AUTH-SUMMARY to OPFIL1-REC
    INITIALIZE ROOT-SEG-KEY, CHILD-SEG-REC
    MOVE PA-ACCT-ID to ROOT-SEG-KEY
    IF PA-ACCT-ID IS NUMERIC:
        PERFORM 3100-INSERT-PARENT-SEG-GSAM    (write summary to GSAM)
        INITIALIZE WS-END-OF-CHILD-SEG
        PERFORM 3000-FIND-NEXT-AUTH-DTL
        UNTIL WS-END-OF-CHILD-SEG = 'Y'
IF PAUT-PCB-STATUS = 'GB':
    SET END-OF-AUTHDB; MOVE 'Y' to WS-END-OF-ROOT-SEG
IF other status: DISPLAY error; PERFORM 9999-ABEND
```

### 3000-FIND-NEXT-AUTH-DTL (line 263)

```
CALL 'CBLTDLI' GNP PAUTBPCB PENDING-AUTH-DETAILS CHILD-UNQUAL-SSA

IF spaces:
    Increment counters
    MOVE PENDING-AUTH-DETAILS to CHILD-SEG-REC
    PERFORM 3200-INSERT-CHILD-SEG-GSAM    (write detail to GSAM)
IF 'GE':
    MOVE 'Y' to WS-END-OF-CHILD-SEG
    DISPLAY 'CHILD SEG FLAG GE : ' WS-END-OF-CHILD-SEG
IF other: DISPLAY error; PERFORM 9999-ABEND
INITIALIZE PAUT-PCB-STATUS
```

### 4000-FILE-CLOSE (line 338)

- DISPLAY 'CLOSING THE FILE'
- No actual CLOSE statements (commented out).

### 9999-ABEND (line 357)

- DISPLAY 'DBUNLDGS ABENDING ...'
- MOVE 16 TO RETURN-CODE
- GOBACK

---

## Error Handling

| Condition | Action |
|-----------|--------|
| GN returns non-spaces, non-GB | DISPLAY status + KEYFB area; PERFORM 9999-ABEND |
| GNP returns non-spaces, non-GE | DISPLAY status + KEYFB area; PERFORM 9999-ABEND |
| GSAM ISRT (parent) fails | DISPLAY PASFL-PCB-STATUS + KEYFB; PERFORM 9999-ABEND |
| GSAM ISRT (child) fails | DISPLAY PADFL-PCB-STATUS + KEYFB; PERFORM 9999-ABEND |
| Abend | RETURN-CODE = 16, GOBACK |

---

## Transaction Flow Participation

This is a standalone batch utility. It does not participate in CICS transactions. Typical invocation:

```
//DBUNLDGS EXEC PGM=DFSRRC00,PARM='DLI,DBUNLDGS,PSBPAUTB,...'
//         DD DSN=GSAM.SUMMARY.OUTPUT,...
//         DD DSN=GSAM.DETAIL.OUTPUT,...
```

The PSB used is determined by the JCL parm (likely PSBPAUTB or a dedicated unload PSB). The PSB must define three PCBs: the IMS DB PCB plus two GSAM PCBs.

---

## Inter-Program Interactions

None. DBUNLDGS is a self-contained batch utility.

**Relationship to PAUDBLOD:** DBUNLDGS produces the GSAM datasets that PAUDBLOD consumes to reload IMS. PAUDBLOD reads two sequential files (INFILE1 = summary, INFILE2 = detail) that correspond to what DBUNLDGS writes through PASFLPCB and PADFLPCB respectively.

**Relationship to PAUDBUNL:** PAUDBUNL is a variant that writes to flat sequential files (OPFILE1/OPFILE2) rather than GSAM.
