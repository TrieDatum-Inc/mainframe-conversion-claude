# Technical Specification: PAUDBLOD

## Program Name and Purpose

**Program ID:** PAUDBLOD  
**Source File:** `/app/app-authorization-ims-db2-mq/cbl/PAUDBLOD.CBL`  
**Type:** Batch COBOL IMS Program (sequential file input)  
**Application:** CardDemo - Authorization Module  
**Function:** Load IMS Pending Authorization Database from Sequential Flat Files

PAUDBLOD is the inverse of PAUDBUNL. It reads two sequential input files — INFILE1 (summary/root segment records) and INFILE2 (detail/child segment records) — and inserts them back into the IMS authorization database using CBLTDLI calls. This is a reload/migration utility, typically used to restore data after an unload (by PAUDBUNL) or to migrate data between environments.

The program reads INFILE1 sequentially first to insert all summary (PAUTSUM0) segments. Then it reads INFILE2 sequentially to insert all detail (PAUTDTL1) child segments. For each child record, a GU (Get Unique) call retrieves the parent summary segment using the ROOT-SEG-KEY from INFILE2, then the ISRT inserts the child under that parent.

---

## Artifact Inventory

| Artifact | Type | Role |
|----------|------|------|
| PAUDBLOD.CBL | COBOL Source | Main program |
| CIPAUSMY.cpy | Copybook | IMS PAUTSUM0 segment layout |
| CIPAUDTY.cpy | Copybook | IMS PAUTDTL1 segment layout |
| IMSFUNCS.cpy | Copybook | DL/I function code constants |
| PAUTBPCB.CPY | Copybook | IMS database PCB mask |

---

## IDENTIFICATION DIVISION Metadata

- **PROGRAM-ID:** PAUDBLOD  
- **AUTHOR:** AWS  
- WS-PGMNAME = 'IMSUNLOD' (cloned template artifact, not 'PAUDBLOD')
- Source lines 17–19

---

## ENVIRONMENT DIVISION — FILE-CONTROL (lines 25–35)

```cobol
SELECT INFILE1 ASSIGN TO INFILE1
ORGANIZATION IS SEQUENTIAL
ACCESS MODE  IS SEQUENTIAL
FILE STATUS IS WS-INFIL1-STATUS.

SELECT INFILE2 ASSIGN TO INFILE2
ORGANIZATION IS SEQUENTIAL
ACCESS MODE  IS SEQUENTIAL
FILE STATUS IS WS-INFIL2-STATUS.
```

Two sequential input files. DD names INFILE1 and INFILE2 in JCL.

---

## DATA DIVISION

### FILE SECTION (lines 42–48)

```
FD INFILE1.
01 INFIL1-REC          PIC X(100).      -- one root segment record per read

FD INFILE2.
01 INFIL2-REC.
  05 ROOT-SEG-KEY      PIC S9(11) COMP-3  -- account ID (6 bytes packed)
  05 CHILD-SEG-REC     PIC X(200)         -- detail segment data
```

The format of INFIL2-REC (ROOT-SEG-KEY + CHILD-SEG-REC) matches what PAUDBUNL writes to OPFILE2: it stores the account ID at the front of each child record so PAUDBLOD can issue the qualifying GU call.

### SSA Definitions (lines 113–127)

```
01 ROOT-QUAL-SSA.
  05 QUAL-SSA-SEG-NAME  PIC X(08) VALUE 'PAUTSUM0'.
  05 FILLER             PIC X(01) VALUE '('.
  05 QUAL-SSA-KEY-FIELD PIC X(08) VALUE 'ACCNTID '.
  05 QUAL-SSA-REL-OPER  PIC X(02) VALUE 'EQ'.
  05 QUAL-SSA-KEY-VALUE PIC S9(11) COMP-3.     -- filled at runtime
  05 FILLER             PIC X(01) VALUE ')'.

01 ROOT-UNQUAL-SSA.
  05 FILLER PIC X(08) VALUE 'PAUTSUM0'.
  05 FILLER PIC X(01) VALUE ' '.

01 CHILD-UNQUAL-SSA.
  05 FILLER PIC X(08) VALUE 'PAUTDTL1'.
  05 FILLER PIC X(01) VALUE ' '.
```

### Key State Flags (lines 80–86)

| Field | PIC | Purpose |
|-------|-----|---------|
| WS-END-OF-INFILE1 | X(01) | 'Y' when INFILE1 is exhausted |
| WS-END-OF-INFILE2 | X(01) | 'Y' when INFILE2 is exhausted |
| WS-INFIL1-STATUS | X(02) | INFILE1 file status |
| WS-INFIL2-STATUS | X(02) | INFILE2 file status |
| END-ROOT-SEG-FILE | X(01) | (redundant with WS-END-OF-INFILE1) |
| END-CHILD-SEG-FILE | X(01) | Controls INFILE2 read loop |

---

## LINKAGE SECTION (lines 157–165)

```cobol
01 IO-PCB-MASK   PIC X(1).
COPY PAUTBPCB.     -- 01 PAUTBPCB
```

```cobol
PROCEDURE DIVISION USING IO-PCB-MASK PAUTBPCB.
```

The `IO-PCB-MASK` precedes PAUTBPCB (following IMS batch DL/I convention where the I/O PCB is first). ENTRY 'DLITCBL' USING PAUTBPCB at line 171 provides the alternate entry.

---

## IMS DL/I Calls (CBLTDLI interface)

### 2100-INSERT-ROOT-SEG (line 242)

```cobol
CALL 'CBLTDLI' USING FUNC-ISRT
                     PAUTBPCB
                     PENDING-AUTH-SUMMARY
                     ROOT-UNQUAL-SSA.
```
- Inserts a new PAUTSUM0 root segment.
- Status 'II' (duplicate) is tolerated and logged as informational (line 256–258: "ROOT SEGMENT ALREADY IN DB").
- Any other non-space status triggers 9999-ABEND.

### 3100-INSERT-CHILD-SEG (lines 296–314) — Two calls

**Step 1: GU to establish parent position:**
```cobol
INITIALIZE PAUT-PCB-STATUS
CALL 'CBLTDLI' USING FUNC-GU
                     PAUTBPCB
                     PENDING-AUTH-SUMMARY
                     ROOT-QUAL-SSA.     -- qualified by QUAL-SSA-KEY-VALUE
```
- ROOT-SEG-KEY from INFILE2 is moved to QUAL-SSA-KEY-VALUE before this call.
- Status spaces = success; other = ABEND.

**Step 2: ISRT to insert child:**

Performed in 3200-INSERT-IMS-CALL (line 318):
```cobol
CALL 'CBLTDLI' USING FUNC-ISRT
                     PAUTBPCB
                     PENDING-AUTH-DETAILS
                     CHILD-UNQUAL-SSA.
```
- Status 'II' = duplicate (logged, no abend).
- Other non-space = ABEND.

---

## Program Flow

### MAIN-PARA (line 169)

```
ENTRY 'DLITCBL' USING PAUTBPCB

DISPLAY 'STARTING PAUDBLOD'
PERFORM 1000-INITIALIZE

-- Pass 1: Load all root (summary) segments
PERFORM 2000-READ-ROOT-SEG-FILE
UNTIL END-ROOT-SEG-FILE = 'Y'

-- Pass 2: Load all child (detail) segments
PERFORM 3000-READ-CHILD-SEG-FILE
UNTIL END-CHILD-SEG-FILE = 'Y'

PERFORM 4000-FILE-CLOSE
GOBACK
```

**Design note:** Root segments are loaded entirely before any child segments. This ensures parent segments exist before child INSRTs attempt to locate them via GU.

### 1000-INITIALIZE (line 190)

- ACCEPT current date and Julian date.
- OPEN INPUT INFILE1 — abend if status not '00' or spaces.
- OPEN INPUT INFILE2 — abend if status not '00' or spaces.

### 2000-READ-ROOT-SEG-FILE (line 222)

```
READ INFILE1
IF status spaces/'00':
    MOVE INFIL1-REC to PENDING-AUTH-SUMMARY
    PERFORM 2100-INSERT-ROOT-SEG
ELSE IF status '10':
    MOVE 'Y' to END-ROOT-SEG-FILE
ELSE:
    DISPLAY 'ERROR READING ROOT SEG INFILE'
```

### 2100-INSERT-ROOT-SEG (line 242)

```
CALL CBLTDLI FUNC-ISRT PAUTBPCB PENDING-AUTH-SUMMARY ROOT-UNQUAL-SSA
IF status spaces: DISPLAY 'ROOT INSERT SUCCESS'
IF status 'II':   DISPLAY 'ROOT SEGMENT ALREADY IN DB'
IF other:         DISPLAY error; PERFORM 9999-ABEND
```

### 3000-READ-CHILD-SEG-FILE (line 269)

```
READ INFILE2
IF status spaces/'00':
    IF ROOT-SEG-KEY IS NUMERIC:
        MOVE ROOT-SEG-KEY to QUAL-SSA-KEY-VALUE
        MOVE CHILD-SEG-REC to PENDING-AUTH-DETAILS
        PERFORM 3100-INSERT-CHILD-SEG
ELSE IF status '10':
    MOVE 'Y' to END-CHILD-SEG-FILE
ELSE:
    DISPLAY 'ERROR READING CHILD SEG INFILE'
```

### 3100-INSERT-CHILD-SEG (line 292)

```
INITIALIZE PAUT-PCB-STATUS
CALL CBLTDLI FUNC-GU PAUTBPCB PENDING-AUTH-SUMMARY ROOT-QUAL-SSA
DISPLAY separators
IF status spaces:
    DISPLAY 'GU CALL TO ROOT SEG SUCCESS'
    PERFORM 3200-INSERT-IMS-CALL
IF status not spaces and not 'II':
    DISPLAY error; PERFORM 9999-ABEND
```

**Note — Logic issue:** The IF at line 310 checking `PAUT-PCB-STATUS NOT EQUAL TO SPACES AND 'II'` is nested inside the first `IF PAUT-PCB-STATUS = SPACES` block (line 305). This means if GU fails with a non-space status, the abend check may not fire correctly. This is a potential defect.

### 3200-INSERT-IMS-CALL (line 318)

```
CALL CBLTDLI FUNC-ISRT PAUTBPCB PENDING-AUTH-DETAILS CHILD-UNQUAL-SSA
IF status spaces:   DISPLAY 'CHILD SEGMENT INSERTED SUCCESS'
IF status 'II':     DISPLAY 'CHILD SEGMENT ALREADY IN DB'
IF other:           DISPLAY error; PERFORM 9999-ABEND
```

### 4000-FILE-CLOSE (line 341)

- CLOSE INFILE1, check status.
- CLOSE INFILE2, check status.

### 9999-ABEND (line 359)

- DISPLAY 'IMS LOAD ABENDING ...'
- MOVE 16 TO RETURN-CODE
- GOBACK

---

## Error Handling

| Condition | Action |
|-----------|--------|
| INFILE1 open failure | DISPLAY error; 9999-ABEND |
| INFILE2 open failure | DISPLAY error; 9999-ABEND |
| INFILE1 read error (not '00' or '10') | DISPLAY 'ERROR READING ROOT SEG INFILE' |
| INFILE2 read error (not '00' or '10') | DISPLAY 'ERROR READING CHILD SEG INFILE' |
| Root ISRT status 'II' | DISPLAY 'ROOT SEGMENT ALREADY IN DB' (non-fatal) |
| Root ISRT other failure | DISPLAY status; 9999-ABEND |
| Child GU failure | DISPLAY status + KEYFB; 9999-ABEND |
| Child ISRT status 'II' | DISPLAY 'CHILD SEGMENT ALREADY IN DB' (non-fatal) |
| Child ISRT other failure | DISPLAY status + KEYFB; 9999-ABEND |

---

## Transaction Flow Participation

Standalone batch utility. Typical invocation:

```
//PAUDBLOD EXEC PGM=DFSRRC00,PARM='DLI,PAUDBLOD,PSBPAUTB,...'
//INFILE1  DD DSN=PAUDBUNL.SUMMARY.OUTPUT,...   (from PAUDBUNL run)
//INFILE2  DD DSN=PAUDBUNL.DETAIL.OUTPUT,...    (from PAUDBUNL run)
```

---

## Inter-Program Interactions

| Program | Relationship |
|---------|-------------|
| PAUDBUNL | Produces INFILE1 and INFILE2 used as input |
| DBUNLDGS | Alternative unload that uses GSAM instead of flat files |
