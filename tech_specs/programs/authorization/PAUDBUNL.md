# Technical Specification: PAUDBUNL
## IMS Database Unload to Sequential Files Program

---

### 1. Program Overview

| Attribute       | Value                                                        |
|-----------------|--------------------------------------------------------------|
| Program Name    | PAUDBUNL                                                     |
| Source File     | cbl/PAUDBUNL.CBL                                             |
| Program Type    | Batch IMS DLI (non-BMP)                                     |
| Function        | Unload IMS DBPAUTP0 to two sequential (QSAM) datasets       |
| JCL Job         | UNLDPADB.JCL                                                 |
| Author          | AWS                                                          |
| WS-PGMNAME      | 'IMSUNLOD' (hardcoded; does not match program ID)           |
| PSB Used        | PAUTBUNL (PROCOPT=GOTP, no GSAM PCBs)                       |
| IMS Database PCB| PAUTBPCB (referenced via COPY PAUTBPCB)                     |

**Purpose:** PAUDBUNL reads the entire IMS DBPAUTP0 database sequentially and writes each PAUTSUM0 root segment to OPFILE1 (100-byte sequential file) and each PAUTDTL1 child segment to OPFILE2 (206-byte record: 6-byte key + 200-byte data). This is the primary unload utility for migrating or backing up the IMS authorization database to flat files, which can then be re-loaded by PAUDBLOD.

---

### 2. Program Flow

```
MAIN-PARA / ENTRY 'DLITCBL' USING PAUTBPCB
  |
  +-- 1000-INITIALIZE
  |     ACCEPT CURRENT-DATE FROM DATE
  |     ACCEPT CURRENT-YYDDD FROM DAY
  |     DISPLAY startup messages
  |     OPEN OUTPUT OPFILE1 (check WS-OUTFL1-STATUS)
  |     OPEN OUTPUT OPFILE2 (check WS-OUTFL2-STATUS)
  |
  +-- 2000-FIND-NEXT-AUTH-SUMMARY
  |   UNTIL WS-END-OF-ROOT-SEG = 'Y'
  |     CALL 'CBLTDLI' USING FUNC-GN PAUTBPCB PENDING-AUTH-SUMMARY ROOT-UNQUAL-SSA
  |     [SPACES]  -> increment counters
  |               -> MOVE PENDING-AUTH-SUMMARY TO OPFIL1-REC
  |               -> MOVE PA-ACCT-ID TO ROOT-SEG-KEY
  |               -> IF PA-ACCT-ID IS NUMERIC:
  |                    WRITE OPFIL1-REC (root to OPFILE1)
  |                    Reset WS-END-OF-CHILD-SEG
  |                    Loop: 3000-FIND-NEXT-AUTH-DTL UNTIL WS-END-OF-CHILD-SEG='Y'
  |     ['GB']    -> SET END-OF-AUTHDB; SET WS-END-OF-ROOT-SEG='Y'
  |     [other]   -> DISPLAY error + PAUT-KEYFB; 9999-ABEND
  |
  +-- 4000-FILE-CLOSE
  |     DISPLAY 'CLOSING THE FILE'
  |     CLOSE OPFILE1; check status
  |     CLOSE OPFILE2; check status
  +-- GOBACK
```

#### 3000-FIND-NEXT-AUTH-DTL (inner loop for children)
```
CALL 'CBLTDLI' USING FUNC-GNP PAUTBPCB PENDING-AUTH-DETAILS CHILD-UNQUAL-SSA
[SPACES] -> increment counters
          -> MOVE PENDING-AUTH-DETAILS TO CHILD-SEG-REC
          -> WRITE OPFIL2-REC (child + key to OPFILE2)
['GE']   -> MOVE 'Y' TO WS-END-OF-CHILD-SEG; DISPLAY flag
[other]  -> DISPLAY error + PAUT-KEYFB; 9999-ABEND
INITIALIZE PAUT-PCB-STATUS
```

---

### 3. File Definitions

#### OPFILE1 — Root Segment File
| Attribute     | Value                                        |
|---------------|----------------------------------------------|
| SELECT Name   | OPFILE1                                      |
| ASSIGN        | OUTFIL1                                      |
| Organization  | Sequential                                   |
| Access Mode   | Sequential                                   |
| Record Layout | PIC X(100) — full PAUTSUM0 segment (100 bytes) |
| JCL DCB       | LRECL=100, BLKSIZE=0, RECFM=FB              |
| Dataset Name  | AWS.M2.CARDDEMO.PAUTDB.ROOT.FILEO            |

#### OPFILE2 — Child Segment File
| Attribute     | Value                                        |
|---------------|----------------------------------------------|
| SELECT Name   | OPFILE2                                      |
| ASSIGN        | OUTFIL2                                      |
| Organization  | Sequential                                   |
| Access Mode   | Sequential                                   |
| Record Layout | 05 ROOT-SEG-KEY PIC S9(11) COMP-3 + 05 CHILD-SEG-REC PIC X(200) = 206 bytes |
| JCL DCB       | LRECL=206, BLKSIZE=0, RECFM=FB              |
| Dataset Name  | AWS.M2.CARDDEMO.PAUTDB.CHILD.FILEO           |

The OPFIL2-REC structure:
- ROOT-SEG-KEY (6 bytes, COMP-3 PIC S9(11)): carries the parent PAUTSUM0 key (PA-ACCT-ID) with each child record
- CHILD-SEG-REC (200 bytes): full PAUTDTL1 segment data

---

### 4. IMS Calls (CALL 'CBLTDLI' form)

| Function | PCB Used  | Segment               | SSA                                          | Purpose                   |
|----------|-----------|-----------------------|----------------------------------------------|---------------------------|
| GN       | PAUTBPCB  | PENDING-AUTH-SUMMARY  | ROOT-UNQUAL-SSA ('PAUTSUM0 ')               | Get next root segment     |
| GNP      | PAUTBPCB  | PENDING-AUTH-DETAILS  | CHILD-UNQUAL-SSA ('PAUTDTL1 ')              | Get next child segment    |

---

### 5. Error Handling

| Condition                                      | Response                                          |
|------------------------------------------------|---------------------------------------------------|
| PAUT-PCB-STATUS not SPACES or 'GB' after GN   | DISPLAY + PAUT-KEYFB; 9999-ABEND (RC=16)         |
| PAUT-PCB-STATUS not SPACES or 'GE' after GNP  | DISPLAY + PAUT-KEYFB; 9999-ABEND (RC=16)         |
| OPFILE1 open error                            | DISPLAY status; 9999-ABEND (RC=16)               |
| OPFILE2 open error                            | DISPLAY status; 9999-ABEND (RC=16)               |
| OPFILE1/OPFILE2 close error                   | DISPLAY status (no abend on close)               |

---

### 6. JCL — UNLDPADB.JCL

| JCL Element | Value                                                         |
|-------------|---------------------------------------------------------------|
| STEP0       | IEFBR14 (deletes existing output datasets)                   |
| DD1 / DD2   | Old output files deleted in STEP0                            |
| STEP01 PGM  | DFSRRC00                                                     |
| PARM        | 'DLI,PAUDBUNL,PAUTBUNL,,,,,,,,,,,N'                        |
| OUTFIL1     | AWS.M2.CARDDEMO.PAUTDB.ROOT.FILEO (NEW,CATLG,DELETE)        |
| OUTFIL2     | AWS.M2.CARDDEMO.PAUTDB.CHILD.FILEO (NEW,CATLG,DELETE)       |
| DDPAUTP0    | OEM.IMS.IMSP.PAUTHDB                                         |
| DDPAUTX0    | OEM.IMS.IMSP.PAUTHDBX                                        |

---

### 7. Relationship to Other Programs

| Program   | Relationship                                                     |
|-----------|------------------------------------------------------------------|
| PAUDBLOD  | PAUDBUNL creates OUTFIL1/OUTFIL2; PAUDBLOD reads INFILE1/INFILE2 (same datasets) |
| DBUNLDGS  | Functional equivalent using GSAM output instead of QSAM         |
| CBPAUP0C  | CBPAUP0C deletes records in IMS; PAUDBUNL unloads what remains  |

---

### 8. I/O Specification

| Direction | Resource       | Operation | Description                                     |
|-----------|----------------|-----------|-------------------------------------------------|
| Input     | IMS DBPAUTP0   | GN        | All PAUTSUM0 root segments                      |
| Input     | IMS DBPAUTP0   | GNP       | All PAUTDTL1 child segments                     |
| Output    | OPFILE1 (QSAM) | WRITE     | 100-byte root segment records                   |
| Output    | OPFILE2 (QSAM) | WRITE     | 206-byte records (6-byte parent key + 200-byte child) |

---
