# Technical Specification: PAUDBLOD
## IMS Database Load from Sequential Files Program

---

### 1. Program Overview

| Attribute       | Value                                                          |
|-----------------|----------------------------------------------------------------|
| Program Name    | PAUDBLOD                                                       |
| Source File     | cbl/PAUDBLOD.CBL                                               |
| Program Type    | Batch IMS DLI (non-BMP)                                       |
| Function        | Load IMS DBPAUTP0 from two sequential (QSAM) input files      |
| JCL Job         | LOADPADB.JCL                                                   |
| Author          | AWS                                                            |
| WS-PGMNAME      | 'IMSUNLOD' (hardcoded; does not match program ID)             |
| PSB Used        | PSBPAUTB (PROCOPT=AP — Add and Get)                           |
| IMS PCB         | PAUTBPCB (copied from PAUTBPCB.CPY)                           |

**Purpose:** PAUDBLOD is the IMS database reload utility, the inverse of PAUDBUNL. It reads INFILE1 (root segment flat file) and inserts each record as a PAUTSUM0 segment. It then reads INFILE2 (child segment flat file with embedded parent key) and inserts each record as a PAUTDTL1 child under the parent identified by the ROOT-SEG-KEY field. This is used to restore the IMS authorization database from a flat file backup.

---

### 2. Program Flow

```
MAIN-PARA / ENTRY 'DLITCBL' USING PAUTBPCB
  |
  +-- 1000-INITIALIZE
  |     ACCEPT CURRENT-DATE FROM DATE
  |     ACCEPT CURRENT-YYDDD FROM DAY
  |     DISPLAY header
  |     OPEN INPUT INFILE1 (check WS-INFIL1-STATUS)
  |     OPEN INPUT INFILE2 (check WS-INFIL2-STATUS)
  |
  +-- 2000-READ-ROOT-SEG-FILE  UNTIL END-ROOT-SEG-FILE='Y'
  |     READ INFILE1
  |     [status = SPACES or '00']
  |       MOVE INFIL1-REC TO PENDING-AUTH-SUMMARY
  |       2100-INSERT-ROOT-SEG:
  |         CALL 'CBLTDLI' USING FUNC-ISRT PAUTBPCB PENDING-AUTH-SUMMARY ROOT-UNQUAL-SSA
  |         [SPACES]  -> DISPLAY 'ROOT INSERT SUCCESS'
  |         ['II']    -> DISPLAY 'ROOT SEGMENT ALREADY IN DB'
  |         [other]   -> DISPLAY error + PAUT-KEYFB; 9999-ABEND
  |     [status = '10'] -> MOVE 'Y' TO END-ROOT-SEG-FILE (EOF)
  |     [other status]  -> DISPLAY 'ERROR READING ROOT SEG INFILE'
  |
  +-- 3000-READ-CHILD-SEG-FILE  UNTIL END-CHILD-SEG-FILE='Y'
  |     READ INFILE2
  |     [status = SPACES or '00']
  |       IF ROOT-SEG-KEY IS NUMERIC:
  |         MOVE ROOT-SEG-KEY TO QUAL-SSA-KEY-VALUE
  |         MOVE CHILD-SEG-REC TO PENDING-AUTH-DETAILS
  |         3100-INSERT-CHILD-SEG:
  |           INITIALIZE PAUT-PCB-STATUS
  |           CALL 'CBLTDLI' FUNC-GU PAUTBPCB PENDING-AUTH-SUMMARY ROOT-QUAL-SSA
  |           [SPACES] -> DISPLAY 'GU CALL TO ROOT SEG SUCCESS'
  |                       3200-INSERT-IMS-CALL:
  |                         CALL 'CBLTDLI' FUNC-ISRT PAUTBPCB PENDING-AUTH-DETAILS CHILD-UNQUAL-SSA
  |                         [SPACES] -> 'CHILD SEGMENT INSERTED SUCCESS'
  |                         ['II']   -> 'CHILD SEGMENT ALREADY IN DB'
  |                         [other]  -> DISPLAY + PAUT-KEYFB; 9999-ABEND
  |           [non-SPACES/non-'II'] -> DISPLAY + PAUT-KEYFB; 9999-ABEND
  |     [status = '10'] -> MOVE 'Y' TO END-CHILD-SEG-FILE (EOF)
  |     [other status]  -> DISPLAY 'ERROR READING CHILD SEG INFILE'
  |
  +-- 4000-FILE-CLOSE
  |     CLOSE INFILE1; check status
  |     CLOSE INFILE2; check status
  +-- GOBACK
```

---

### 3. File Definitions

#### INFILE1 — Root Segment Input File
| Attribute     | Value                                         |
|---------------|-----------------------------------------------|
| SELECT Name   | INFILE1                                       |
| ASSIGN        | INFILE1                                       |
| Organization  | Sequential                                    |
| Record Layout | PIC X(100) (INFIL1-REC) — PAUTSUM0 segment   |
| JCL Dataset   | AWS.M2.CARDDEMO.PAUTDB.ROOT.FILEO (as written by PAUDBUNL) |

#### INFILE2 — Child Segment Input File
| Attribute     | Value                                         |
|---------------|-----------------------------------------------|
| SELECT Name   | INFILE2                                       |
| ASSIGN        | INFILE2                                       |
| Organization  | Sequential                                    |
| Record Layout | 05 ROOT-SEG-KEY PIC S9(11) COMP-3 + 05 CHILD-SEG-REC PIC X(200) = 206 bytes |
| JCL Dataset   | AWS.M2.CARDDEMO.PAUTDB.CHILD.FILEO (as written by PAUDBUNL) |

---

### 4. Qualified SSA for Root Segment GU

PAUDBLOD uses a qualified SSA for the GU call that positions to the parent before inserting each child. This is defined in WS (lines 113–119):

```cobol
01 ROOT-QUAL-SSA.
   05 QUAL-SSA-SEG-NAME   PIC X(08) VALUE 'PAUTSUM0'.
   05 FILLER              PIC X(01) VALUE '('.
   05 QUAL-SSA-KEY-FIELD  PIC X(08) VALUE 'ACCNTID '.
   05 QUAL-SSA-REL-OPER   PIC X(02) VALUE 'EQ'.
   05 QUAL-SSA-KEY-VALUE  PIC S9(11) COMP-3.
   05 FILLER              PIC X(01) VALUE ')'.
```

The QUAL-SSA-KEY-VALUE is loaded from ROOT-SEG-KEY (the account ID embedded in each INFILE2 record) at line 277.

---

### 5. IMS Calls

| Function | PCB       | Segment               | SSA                  | Purpose                                     |
|----------|-----------|-----------------------|----------------------|---------------------------------------------|
| ISRT     | PAUTBPCB  | PENDING-AUTH-SUMMARY  | ROOT-UNQUAL-SSA      | Insert root segment (no parent qualifier needed) |
| GU       | PAUTBPCB  | PENDING-AUTH-SUMMARY  | ROOT-QUAL-SSA (ACCNTID = value) | Position to parent for child insert |
| ISRT     | PAUTBPCB  | PENDING-AUTH-DETAILS  | CHILD-UNQUAL-SSA     | Insert child segment under positioned parent |

---

### 6. Error Handling

| Condition                                      | Response                                                |
|------------------------------------------------|---------------------------------------------------------|
| INFILE1 open error                            | DISPLAY status; 9999-ABEND (RC=16)                      |
| INFILE2 open error                            | DISPLAY status; 9999-ABEND (RC=16)                      |
| Root INSERT: non-SPACES, non-'II'             | DISPLAY + PAUT-KEYFB; 9999-ABEND (RC=16)               |
| Root GU: non-SPACES, non-'II'                 | DISPLAY + PAUT-KEYFB; 9999-ABEND (RC=16)               |
| Child ISRT: non-SPACES, non-'II'              | DISPLAY + PAUT-KEYFB; 9999-ABEND (RC=16)               |
| INFILE1/INFILE2 read: non-'10', non-SPACES   | DISPLAY error (no abend)                               |
| INFILE1/INFILE2 close error                   | DISPLAY status (no abend)                              |
| 'II' (duplicate) on ISRT                      | Log message only — no abend, processing continues       |

---

### 7. Business Rules

1. Root segments (PAUTSUM0) are loaded first (2000-READ-ROOT-SEG-FILE loop), before any child segments.
2. Child segments (PAUTDTL1) are loaded in a separate pass (3000-READ-CHILD-SEG-FILE loop) after all roots are loaded.
3. Each child record in INFILE2 carries its parent key (ROOT-SEG-KEY = PA-ACCT-ID). A GU is performed to position the IMS cursor at the parent before each child ISRT.
4. Duplicate key conditions (IMS status 'II') are tolerated and logged but do not cause abend — this allows re-runs if a partial load occurred.
5. Non-numeric ROOT-SEG-KEY values cause the child record to be skipped without error (matching the PAUDBUNL behavior that only writes numeric account IDs).

---

### 8. JCL — LOADPADB.JCL

| JCL Element | Value                                                        |
|-------------|--------------------------------------------------------------|
| STEP01 PGM  | DFSRRC00                                                     |
| PARM        | 'BMP,PAUDBLOD,PSBPAUTB'                                     |
| STEPLIB     | OEMA.IMS.IMSP.SDFSRESL + V151 + AWS.M2.CARDDEMO.LOADLIB    |
| IMS         | OEM.IMS.IMSP.PSBLIB + OEM.IMS.IMSP.DBDLIB                  |
| INFILE1     | AWS.M2.CARDDEMO.PAUTDB.ROOT.FILEO (DISP=SHR)               |
| INFILE2     | AWS.M2.CARDDEMO.PAUTDB.CHILD.FILEO (DISP=SHR)              |

**Note:** The PARM uses 'BMP' but the source code uses ENTRY 'DLITCBL' which is the DLI call interface, not BMP. The DD names for DDPAUTP0/DDPAUTX0 are commented out in the JCL (lines 40–41), meaning the database DDs are provided through the PSB library resolution. This is a potential installation issue.

---

### 9. Relationship to Other Programs

| Program  | Relationship                                                           |
|----------|------------------------------------------------------------------------|
| PAUDBUNL | Creates OUTFIL1/OUTFIL2 which become INFILE1/INFILE2 for PAUDBLOD     |
| DBUNLDGS | Creates GSAM output; does NOT feed PAUDBLOD (different output format)  |
| CBPAUP0C | After CBPAUP0C deletes expired records, PAUDBUNL+PAUDBLOD can be used for backup/restore cycle |

---

### 10. I/O Specification

| Direction | Resource       | Operation  | Description                                             |
|-----------|----------------|------------|---------------------------------------------------------|
| Input     | INFILE1 (QSAM) | READ       | 100-byte root segment records                           |
| Input     | INFILE2 (QSAM) | READ       | 206-byte records (6-byte parent key + 200-byte child)   |
| Output    | IMS DBPAUTP0   | ISRT (root)| Insert PAUTSUM0 root segments                           |
| Output    | IMS DBPAUTP0   | GU + ISRT  | Position to parent + insert PAUTDTL1 child segments     |

---
