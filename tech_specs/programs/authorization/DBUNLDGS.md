# Technical Specification: DBUNLDGS
## IMS Database Unload to GSAM Program

---

### 1. Program Overview

| Attribute       | Value                                                      |
|-----------------|------------------------------------------------------------|
| Program Name    | DBUNLDGS                                                   |
| Source File     | cbl/DBUNLDGS.CBL                                           |
| Program Type    | Batch IMS DLI (non-BMP)                                   |
| Function        | Unload IMS DBPAUTP0 database to two GSAM datasets         |
| JCL Job         | UNLDGSAM.JCL                                               |
| Author          | AWS                                                        |
| WS-PGMNAME      | 'IMSUNLOD' (note: hardcoded name does not match program ID)|
| PSB Used        | DLIGSAMP (provides PAUTBPCB + PASFLPCB + PADFLPCB)        |
| IMS Database PCB| PAUTBPCB (DBPAUTP0, PROCOPT=GOTP)                         |
| IMS GSAM PCBs   | PASFLPCB (PASFLDBD, PROCOPT=LS) — root output              |
|                 | PADFLPCB (PADFLDBD, PROCOPT=LS) — child output             |

**Purpose:** DBUNLDGS reads every PAUTSUM0 root segment and every PAUTDTL1 child segment from IMS DBPAUTP0, and writes them to two GSAM (Generalized Sequential Access Method) datasets. This is an IMS-native unload mechanism — the output files are GSAM PCB datasets, not conventional sequential files. The program is the functional equivalent of PAUDBUNL but uses GSAM output rather than VSAM/QSAM output files.

**Important Note:** File OPEN/WRITE/CLOSE statements for OPFILE1/OPFILE2 are all commented out in DBUNLDGS.CBL (lines 26–36, 195–209, 238–243, 340–353). The active code uses GSAM ISRT calls (3100-INSERT-PARENT-SEG-GSAM and 3200-INSERT-CHILD-SEG-GSAM).

---

### 2. Program Flow

```
MAIN-PARA / ENTRY 'DLITCBL' USING PAUTBPCB, PASFLPCB, PADFLPCB
  |
  +-- 1000-INITIALIZE
  |     ACCEPT CURRENT-DATE FROM DATE
  |     ACCEPT CURRENT-YYDDD FROM DAY
  |     DISPLAY startup message
  |     (File opens commented out)
  |
  +-- 2000-FIND-NEXT-AUTH-SUMMARY
  |   UNTIL WS-END-OF-ROOT-SEG = 'Y'
  |     CALL 'CBLTDLI' USING FUNC-GN PAUTBPCB PENDING-AUTH-SUMMARY ROOT-UNQUAL-SSA
  |     [SPACES]  -> increment counters; write root to OPFIL1-REC (in-memory)
  |               -> IF PA-ACCT-ID IS NUMERIC:
  |                    3100-INSERT-PARENT-SEG-GSAM (CBLTDLI ISRT PASFLPCB)
  |                    Loop: 3000-FIND-NEXT-AUTH-DTL UNTIL WS-END-OF-CHILD-SEG
  |     [' GB']   -> SET END-OF-AUTHDB; SET WS-END-OF-ROOT-SEG='Y'
  |     [other]   -> DISPLAY error + PAUT-KEYFB; 9999-ABEND
  |
  +-- 4000-FILE-CLOSE  (displays 'CLOSING THE FILE'; actual closes commented out)
  +-- GOBACK
```

#### 3000-FIND-NEXT-AUTH-DTL (inner loop)
```
CALL 'CBLTDLI' USING FUNC-GNP PAUTBPCB PENDING-AUTH-DETAILS CHILD-UNQUAL-SSA
[SPACES] -> increment counters; copy to CHILD-SEG-REC
          -> 3200-INSERT-CHILD-SEG-GSAM (CBLTDLI ISRT PADFLPCB)
[' GE']  -> SET WS-END-OF-CHILD-SEG='Y'; DISPLAY flag
[other]  -> DISPLAY error + PAUT-KEYFB; 9999-ABEND
INITIALIZE PAUT-PCB-STATUS (reset after each call)
```

---

### 3. IMS Calls (CALL 'CBLTDLI' form)

| Function  | PCB Used   | Segment          | SSA              | Purpose                                        |
|-----------|------------|------------------|------------------|------------------------------------------------|
| GN        | PAUTBPCB   | PENDING-AUTH-SUMMARY | ROOT-UNQUAL-SSA (PAUTSUM0 + space) | Sequential get-next root |
| GNP       | PAUTBPCB   | PENDING-AUTH-DETAILS | CHILD-UNQUAL-SSA (PAUTDTL1 + space) | Sequential get-next child |
| ISRT      | PASFLPCB   | PENDING-AUTH-SUMMARY | — (GSAM no SSA) | Insert root record to GSAM summary file |
| ISRT      | PADFLPCB   | PENDING-AUTH-DETAILS | — (GSAM no SSA) | Insert child record to GSAM detail file |

**Function codes** come from copybook IMSFUNCS.cpy: FUNC-GN = 'GN  ', FUNC-GNP = 'GNP ', FUNC-ISRT = 'ISRT'.

---

### 4. PCB Layout (from LINKAGE SECTION)

| PCB Name  | Copybook   | Type    | DBD       | PROCOPT | DD Names                    |
|-----------|------------|---------|-----------|---------|-----------------------------|
| PAUTBPCB  | PAUTBPCB.CPY | DB    | DBPAUTP0  | GOTP    | DDPAUTP0, DDPAUTX0          |
| PASFLPCB  | PASFLPCB.CPY | GSAM  | PASFLDBD  | LS      | PASFILIP (in), PASFILOP (out) |
| PADFLPCB  | PADFLPCB.CPY | GSAM  | PADFLDBD  | LS      | PADFILIP (in), PADFILOP (out) |

**GSAM PROCOPT=LS:** Load/Store — supports ISRT (store) for output.

---

### 5. Static Segment Search Arguments

| SSA Name        | Field Content                         |
|-----------------|---------------------------------------|
| ROOT-UNQUAL-SSA | 'PAUTSUM0 ' (8 bytes segment name + 1 space = unqualified SSA) |
| CHILD-UNQUAL-SSA| 'PAUTDTL1 ' (8 bytes segment name + 1 space = unqualified SSA) |

---

### 6. Error Handling

| Condition                                          | Response                                                |
|----------------------------------------------------|---------------------------------------------------------|
| PAUT-PCB-STATUS not SPACES or 'GB' after GN        | DISPLAY + PAUT-KEYFB key feedback; 9999-ABEND (RC=16)  |
| PAUT-PCB-STATUS not SPACES or 'GE' after GNP       | DISPLAY + PAUT-KEYFB key feedback; 9999-ABEND (RC=16)  |
| PASFL-PCB-STATUS not SPACES after GSAM ISRT (root) | DISPLAY + PASFL-KEYFB; 9999-ABEND (RC=16)              |
| PADFL-PCB-STATUS not SPACES after GSAM ISRT (child)| DISPLAY + PADFL-KEYFB; 9999-ABEND (RC=16)              |

---

### 7. Business Rules

1. Only PAUTSUM0 segments where PA-ACCT-ID IS NUMERIC are processed. Non-numeric account IDs cause the root record to be skipped (and its children not unloaded).
2. PAUT-PCB-STATUS is initialized (INITIALIZE PAUT-PCB-STATUS) after each PAUTDTL1 GNP call to prevent stale status being evaluated.
3. GSAM output records for root and child segments are written sequentially in parent-child order (all children of a root before the next root is read).

---

### 8. JCL — UNLDGSAM.JCL

| JCL Element  | Value                                                        |
|--------------|--------------------------------------------------------------|
| PGM          | DFSRRC00                                                     |
| PARM         | 'DLI,DBUNLDGS,DLIGSAMP,,,,,,,,,,,N'                        |
| STEPLIB      | OEMA.IMS.IMSP.SDFSRESL + V151 + AWS.M2.CARDDEMO.LOADLIB    |
| IMS          | OEM.IMS.IMSP.PSBLIB + OEM.IMS.IMSP.DBDLIB                  |
| PASFILOP     | AWS.M2.CARDDEMO.PAUTDB.ROOT.GSAM (DISP=OLD,KEEP)           |
| PADFILOP     | AWS.M2.CARDDEMO.PAUTDB.CHILD.GSAM (DISP=OLD,KEEP)          |
| DDPAUTP0     | OEM.IMS.IMSP.PAUTHDB                                        |
| DDPAUTX0     | OEM.IMS.IMSP.PAUTHDBX                                       |
| DFSVSAMP     | OEMPP.IMS.V15R01MB.PROCLIB(DFSVSMDB)                       |
| IMSLOGR/IEFRDER | DUMMY                                                    |

---

### 9. Counters Reported

At program end (via DISPLAY statements, lines 171–177):
- WS-NO-SUMRY-READ: Total summary segments read
- WS-NO-SUMRY-DELETED: Always 0 (no deletes in this program)
- WS-NO-DTL-READ: Total detail segments read
- WS-NO-DTL-DELETED: Always 0 (no deletes in this program)

**Note:** WS-NO-SUMRY-READ is incremented both when reading root AND child segments (lines 234–235, 278–279 in DBUNLDGS.CBL). This appears to be a counter naming inconsistency — both root and child reads increment WS-NO-SUMRY-READ rather than separate counters.

---

### 10. I/O Specification

| Direction | Resource         | Operation       | Description                              |
|-----------|------------------|-----------------|------------------------------------------|
| Input     | IMS DBPAUTP0     | GN (PAUTSUM0)   | Sequential read of all root segments     |
| Input     | IMS DBPAUTP0     | GNP (PAUTDTL1)  | Sequential read of children under each root |
| Output    | GSAM PASFLDBD    | ISRT            | Write 100-byte root segment record       |
| Output    | GSAM PADFLDBD    | ISRT            | Write 200-byte child segment record      |

---
