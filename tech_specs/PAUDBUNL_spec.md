# Technical Specification: PAUDBUNL

## Program Name and Purpose

**Program ID:** PAUDBUNL  
**Source File:** `/app/app-authorization-ims-db2-mq/cbl/PAUDBUNL.CBL`  
**Type:** Batch COBOL IMS Program (sequential file output)  
**Application:** CardDemo - Authorization Module  
**Function:** Unload IMS Pending Authorization Database to Sequential Flat Files

PAUDBUNL reads all PAUTSUM0 (root/summary) and PAUTDTL1 (child/detail) segments from the IMS authorization database and writes them to two sequential output flat files: OPFILE1 for summary records and OPFILE2 for detail records. This is a sequential unload utility — the complement to PAUDBLOD (which loads data back in).

Unlike DBUNLDGS which uses GSAM output PCBs, PAUDBUNL uses standard COBOL `WRITE` statements to flat sequential datasets.

---

## Artifact Inventory

| Artifact | Type | Role |
|----------|------|------|
| PAUDBUNL.CBL | COBOL Source | Main program |
| CIPAUSMY.cpy | Copybook | IMS PAUTSUM0 segment layout |
| CIPAUDTY.cpy | Copybook | IMS PAUTDTL1 segment layout |
| IMSFUNCS.cpy | Copybook | DL/I function code constants |
| PAUTBPCB.CPY | Copybook | IMS database PCB mask |

---

## IDENTIFICATION DIVISION Metadata

- **PROGRAM-ID:** PAUDBUNL  
- **AUTHOR:** AWS  
- WS-PGMNAME = 'IMSUNLOD' (cloned template artifact)
- Source lines 17–19

---

## ENVIRONMENT DIVISION — FILE-CONTROL (lines 25–35)

```cobol
SELECT OPFILE1 ASSIGN TO OUTFIL1
ORGANIZATION IS SEQUENTIAL
ACCESS MODE  IS SEQUENTIAL
FILE STATUS IS WS-OUTFL1-STATUS.

SELECT OPFILE2 ASSIGN TO OUTFIL2
ORGANIZATION IS SEQUENTIAL
ACCESS MODE  IS SEQUENTIAL
FILE STATUS IS WS-OUTFL2-STATUS.
```

Two sequential output files. JCL DD names: OUTFIL1 and OUTFIL2.

---

## DATA DIVISION

### FILE SECTION (lines 42–48)

```
FD OPFILE1.
01 OPFIL1-REC      PIC X(100).

FD OPFILE2.
01 OPFIL2-REC.
  05 ROOT-SEG-KEY  PIC S9(11) COMP-3    -- account ID packed decimal (6 bytes)
  05 CHILD-SEG-REC PIC X(200)           -- detail segment data (200 bytes)
```

Total OPFIL2-REC length: 6 + 200 = 206 bytes.

OPFIL1-REC at 100 bytes covers the CIPAUSMY layout (which occupies approximately 72 bytes of defined fields + 34 bytes filler = 106 bytes packed — the 100-byte buffer may truncate the filler but not meaningful data).

### SSA Definitions (lines 111–117)

```
01 ROOT-UNQUAL-SSA.
  05 FILLER PIC X(08) VALUE 'PAUTSUM0'.
  05 FILLER PIC X(01) VALUE ' '.

01 CHILD-UNQUAL-SSA.
  05 FILLER PIC X(08) VALUE 'PAUTDTL1'.
  05 FILLER PIC X(01) VALUE ' '.
```

### State Flags (lines 80–81)

```
WS-END-OF-ROOT-SEG   PIC X(01)  -- 'Y' when all root segments read
WS-END-OF-CHILD-SEG  PIC X(01)  -- 'Y' when all children of current root read
```

---

## Copybooks Referenced

| Copybook | Line | Purpose |
|----------|------|---------|
| IMSFUNCS.cpy | 132 | DL/I function codes (FUNC-GN, FUNC-GNP, etc.) |
| CIPAUSMY.cpy | 139 | PENDING-AUTH-SUMMARY segment layout |
| CIPAUDTY.cpy | 143 | PENDING-AUTH-DETAILS segment layout |
| PAUTBPCB.CPY | 150 | PAUTBPCB PCB mask |

---

## LINKAGE SECTION (lines 147–150)

```cobol
COPY PAUTBPCB.    -- 01 PAUTBPCB
```

```cobol
PROCEDURE DIVISION USING PAUTBPCB.
ENTRY 'DLITCBL' USING PAUTBPCB.
```

Only one PCB: the IMS database PCB. No GSAM PCBs needed since native COBOL WRITE is used for output.

---

## IMS DL/I Calls (CBLTDLI interface)

### 2000-FIND-NEXT-AUTH-SUMMARY — GN (line 213)

```cobol
INITIALIZE PAUT-PCB-STATUS
CALL 'CBLTDLI' USING FUNC-GN
                     PAUTBPCB
                     PENDING-AUTH-SUMMARY
                     ROOT-UNQUAL-SSA.
```
- Sequential GN to read each PAUTSUM0 root segment.
- Status spaces = success; 'GB' = end of database.

### 3000-FIND-NEXT-AUTH-DTL — GNP (line 257)

```cobol
CALL 'CBLTDLI' USING FUNC-GNP
                     PAUTBPCB
                     PENDING-AUTH-DETAILS
                     CHILD-UNQUAL-SSA.
```
- Reads next child PAUTDTL1 under current parent.
- Status spaces = success; 'GE' = no more children.

---

## Program Flow

### MAIN-PARA (line 157)

```
ENTRY 'DLITCBL' USING PAUTBPCB

PERFORM 1000-INITIALIZE

PERFORM 2000-FIND-NEXT-AUTH-SUMMARY
UNTIL WS-END-OF-ROOT-SEG = 'Y'

PERFORM 4000-FILE-CLOSE

GOBACK
```

### 1000-INITIALIZE (line 173)

- ACCEPT current date and Julian date.
- DISPLAY 'STARTING PROGRAM PAUDBUNL::' and date.
- OPEN OUTPUT OPFILE1 — abend if status not spaces/'00'.
- OPEN OUTPUT OPFILE2 — abend if status not spaces/'00'.

### 2000-FIND-NEXT-AUTH-SUMMARY (line 207)

```
INITIALIZE PAUT-PCB-STATUS
CALL CBLTDLI GN PAUTBPCB PENDING-AUTH-SUMMARY ROOT-UNQUAL-SSA

IF status spaces:
    Increment counters
    MOVE PENDING-AUTH-SUMMARY to OPFIL1-REC
    INITIALIZE ROOT-SEG-KEY, CHILD-SEG-REC
    MOVE PA-ACCT-ID to ROOT-SEG-KEY
    IF PA-ACCT-ID IS NUMERIC:
        WRITE OPFIL1-REC                    (write summary record)
        INITIALIZE WS-END-OF-CHILD-SEG
        PERFORM 3000-FIND-NEXT-AUTH-DTL
        UNTIL WS-END-OF-CHILD-SEG = 'Y'    (write all children)
IF status 'GB':
    SET END-OF-AUTHDB; MOVE 'Y' to WS-END-OF-ROOT-SEG
IF other: DISPLAY error + PAUT-KEYFB; PERFORM 9999-ABEND
```

The guard `IF PA-ACCT-ID IS NUMERIC` prevents writing summary records with corrupt or null account IDs.

### 3000-FIND-NEXT-AUTH-DTL (line 253)

```
CALL CBLTDLI GNP PAUTBPCB PENDING-AUTH-DETAILS CHILD-UNQUAL-SSA

IF status spaces:
    SET MORE-AUTHS
    Increment counters
    MOVE PENDING-AUTH-DETAILS to CHILD-SEG-REC
    WRITE OPFIL2-REC                        (write detail record with ROOT-SEG-KEY prefix)
IF status 'GE':
    MOVE 'Y' to WS-END-OF-CHILD-SEG
    DISPLAY 'CHILD SEG FLAG GE : ' WS-END-OF-CHILD-SEG
IF other: DISPLAY error + PAUT-KEYFB; PERFORM 9999-ABEND
INITIALIZE PAUT-PCB-STATUS
```

Note that each OPFIL2-REC write contains ROOT-SEG-KEY (the account ID copied from the parent) as a prefix before the 200-byte CHILD-SEG-REC. This allows PAUDBLOD to issue a qualified GU call to re-establish the parent during reload.

### 4000-FILE-CLOSE (line 289)

- CLOSE OPFILE1, check WS-OUTFL1-STATUS.
- CLOSE OPFILE2, check WS-OUTFL2-STATUS.

### 9999-ABEND (line 308)

- DISPLAY 'IMSUNLOD ABENDING ...'
- MOVE 16 TO RETURN-CODE
- GOBACK

---

## Output File Formats

### OUTFIL1 — Summary Records (OPFIL1-REC, PIC X(100))

Contains verbatim copy of PENDING-AUTH-SUMMARY (CIPAUSMY layout). Fixed length 100 bytes. One record per account that has pending authorizations.

### OUTFIL2 — Detail Records (OPFIL2-REC, 206 bytes)

| Offset | Length | Field | Description |
|--------|--------|-------|-------------|
| 0 | 6 | ROOT-SEG-KEY | S9(11) COMP-3 — parent account ID |
| 6 | 200 | CHILD-SEG-REC | CIPAUDTY layout — auth detail |

One record per pending authorization detail segment.

---

## Error Handling

| Condition | Action |
|-----------|--------|
| OPFILE1 open failure | DISPLAY error; 9999-ABEND |
| OPFILE2 open failure | DISPLAY error; 9999-ABEND |
| GN returns non-spaces, non-GB | DISPLAY status + PAUT-KEYFB; 9999-ABEND |
| GNP returns non-spaces, non-GE | DISPLAY status + PAUT-KEYFB; 9999-ABEND |
| CLOSE failures | DISPLAY error only (no abend) |
| 9999-ABEND | RETURN-CODE = 16, GOBACK |

---

## Transaction Flow Participation

Standalone batch utility. Typical JCL:

```
//PAUDBUNL EXEC PGM=DFSRRC00,PARM='DLI,PAUDBUNL,PSBPAUTB,...'
//OUTFIL1  DD DSN=PAUDBUNL.SUMMARY.OUTPUT,DISP=(NEW,CATLG),...
//OUTFIL2  DD DSN=PAUDBUNL.DETAIL.OUTPUT,DISP=(NEW,CATLG),...
```

---

## Comparison with DBUNLDGS

| Attribute | PAUDBUNL | DBUNLDGS |
|-----------|----------|----------|
| Output method | COBOL WRITE (sequential) | GSAM ISRT via CBLTDLI |
| PCBs required | 1 (IMS DB only) | 3 (IMS DB + 2 GSAM) |
| OPFILE1/OPFILE2 writes | Active (WRITE statements) | Commented out (uses GSAM) |
| Complement to | PAUDBLOD (load from seq files) | PAUDBLOD (via GSAM) |

---

## Inter-Program Interactions

| Program | Relationship |
|---------|-------------|
| PAUDBLOD | Consumes OUTFIL1 (as INFILE1) and OUTFIL2 (as INFILE2) |
| DBUNLDGS | Functional equivalent using GSAM output instead of flat files |
