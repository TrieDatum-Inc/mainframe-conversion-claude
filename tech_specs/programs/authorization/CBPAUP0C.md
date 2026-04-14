# Technical Specification: CBPAUP0C
## Batch Expired Authorization Purge Program

---

### 1. Program Overview

| Attribute       | Value                                                   |
|-----------------|---------------------------------------------------------|
| Program Name    | CBPAUP0C                                                |
| Source File     | cbl/CBPAUP0C.cbl                                        |
| Program Type    | Batch IMS BMP (Batch Message Processing)                |
| Function        | Delete Expired Pending Authorization Messages from IMS  |
| JCL Job         | CBPAUP0J.jcl                                            |
| Author          | AWS                                                     |
| IMS Execution   | DFSRRC00 PGM=BMP, PSB=PSBPAUTB                         |
| PSB Used        | PSBPAUTB                                                |
| IMS PCB         | PAUT-PCB-NUM = +2 (position in PSBPAUTB, BMP uses IO-PCB at +1) |

**Purpose:** CBPAUP0C is a daily batch job that scans all IMS PAUTDTL1 child segments under each PAUTSUM0 root segment and deletes those whose authorization date has exceeded the configured expiry threshold (in days). After deleting all expired detail records under a summary segment, if both PA-APPROVED-AUTH-CNT and PA-DECLINED-AUTH-CNT are zero or less, the summary segment is also deleted. Checkpointing is performed at configurable intervals.

---

### 2. Program Flow

```
MAIN-PARA
  |
  +-- 1000-INITIALIZE
  |     ACCEPT CURRENT-DATE FROM DATE      (YYMMDD format)
  |     ACCEPT CURRENT-YYDDD FROM DAY      (Julian date YYDDD)
  |     ACCEPT PRM-INFO FROM SYSIN         (parameters)
  |     Validate and default parameters
  |
  +-- 2000-FIND-NEXT-AUTH-SUMMARY  [initial read]
  |
  +-- PERFORM UNTIL ERR-FLG-ON OR END-OF-AUTHDB:
  |     +-- 3000-FIND-NEXT-AUTH-DTL  [first child of this summary]
  |     +-- PERFORM UNTIL NO-MORE-AUTHS:
  |     |     4000-CHECK-IF-EXPIRED
  |     |     [QUALIFIED-FOR-DELETE] -> 5000-DELETE-AUTH-DTL
  |     |     3000-FIND-NEXT-AUTH-DTL  [next child]
  |     +-- [PA-APPROVED-AUTH-CNT <= 0 AND PA-DECLINED-AUTH-CNT <= 0]
  |     |       -> 6000-DELETE-AUTH-SUMMARY
  |     +-- [WS-AUTH-SMRY-PROC-CNT > P-CHKP-FREQ]
  |     |       -> 9000-TAKE-CHECKPOINT
  |     |       -> Reset WS-AUTH-SMRY-PROC-CNT to 0
  |     +-- 2000-FIND-NEXT-AUTH-SUMMARY  [advance to next root]
  |
  +-- 9000-TAKE-CHECKPOINT  [final checkpoint]
  +-- DISPLAY statistics
  +-- GOBACK
```

---

### 3. Program Parameters (SYSIN)

Parameter format PRM-INFO (line 98):

```
Positions  Field            Picture   Default  Description
1-2        P-EXPIRY-DAYS    9(02)     5        Expiry threshold in days
3          FILLER           X(01)     space
4-8        P-CHKP-FREQ      X(05)     5        Checkpoint every N summary records
9          FILLER           X(01)     space
10-14      P-CHKP-DIS-FREQ  X(05)     10       Display checkpoint message every N checkpoints
15         FILLER           X(01)     space
16         P-DEBUG-FLAG     X(01)     'N'      'Y'=debug DISPLAY enabled
17         FILLER           X(01)
```

**Example SYSIN (from CBPAUP0J.jcl line 37):** `00,00001,00001,Y`
- P-EXPIRY-DAYS = 00 (override in job to 0-day expiry for testing)
- P-CHKP-FREQ = 00001 (checkpoint every 1 summary)
- P-CHKP-DIS-FREQ = 00001 (display every 1 checkpoint)
- P-DEBUG-FLAG = Y (debug on)

**Defaults (from 1000-INITIALIZE, lines 197–209):**
- P-EXPIRY-DAYS defaults to 5 if not numeric
- P-CHKP-FREQ defaults to 5 if spaces/zero/low-values
- P-CHKP-DIS-FREQ defaults to 10 if spaces/zero/low-values
- P-DEBUG-FLAG defaults to 'N' if not 'Y'

---

### 4. Data Structures

#### 4.1 Working Storage Key Fields (lines 41–95)

| Field                    | Picture     | Description                                          |
|--------------------------|-------------|------------------------------------------------------|
| WS-PGMNAME               | PIC X(08)   | 'CBPAUP0C'                                           |
| CURRENT-DATE             | PIC 9(06)   | Current date YYMMDD (from ACCEPT FROM DATE)          |
| CURRENT-YYDDD            | PIC 9(05)   | Current Julian date YYDDD (from ACCEPT FROM DAY)     |
| WS-AUTH-DATE             | PIC 9(05)   | Reconstructed auth date from IMS key                 |
| WS-EXPIRY-DAYS           | PIC S9(4) COMP | Expiry threshold in days (from PRM-INFO)           |
| WS-DAY-DIFF              | PIC S9(4) COMP | Computed age of record in days                    |
| WS-NO-CHKP               | PIC 9(8)    | Number of checkpoints taken                          |
| WS-AUTH-SMRY-PROC-CNT    | PIC 9(8)    | Summary records processed since last checkpoint      |
| WS-NO-SUMRY-READ         | PIC S9(8) COMP | Total summary records read                        |
| WS-NO-SUMRY-DELETED      | PIC S9(8) COMP | Total summary records deleted                     |
| WS-NO-DTL-READ           | PIC S9(8) COMP | Total detail records read                         |
| WS-NO-DTL-DELETED        | PIC S9(8) COMP | Total detail records deleted                      |
| WS-ERR-FLG               | PIC X(01)   | Error flag                                           |
| WS-END-OF-AUTHDB-FLAG    | PIC X(01)   | 'Y'=all summary records processed                    |
| WS-MORE-AUTHS-FLAG       | PIC X(01)   | 'Y'=more detail records under current summary        |

#### 4.2 Checkpoint ID (lines 75–78)

```
WK-CHKPT-ID:
  FILLER PIC X(04) VALUE 'RMAD'    -- prefix
  WK-CHKPT-ID-CTR PIC 9(04)        -- counter (incremented by EXEC DLI CHKP)
```

Wait — CBPAUP0C uses EXEC DLI CHKP for checkpointing (IMS BMP checkpoint), which uses WK-CHKPT-ID as the 8-character checkpoint ID.

#### 4.3 IMS Variables (lines 79–95)

PSB-NAME = 'PSBPAUTB'. **Note:** PAUT-PCB-NUM = +2 (line 83), not +1 as in the online programs. This is because in a BMP execution, PCB position 1 is the I/O PCB (IO-PCB-MASK in LINKAGE SECTION), and position 2 is the first database PCB (PSBPAUTB).

#### 4.4 LINKAGE SECTION (lines 125–130)

```cobol
01 IO-PCB-MASK    PIC X.
01 PGM-PCB-MASK   PIC X.
PROCEDURE DIVISION USING IO-PCB-MASK PGM-PCB-MASK.
```

This is the BMP LINKAGE pattern. IO-PCB-MASK is the IMS I/O PCB (required for CHKP). PGM-PCB-MASK is unused (one-byte placeholder). The actual database PCB is referenced via the PCB(2) ordinal in DLI calls.

---

### 5. IMS DLI Commands

| Command       | Paragraph                  | Segment    | Qualifier    | Purpose                                              |
|---------------|----------------------------|------------|--------------|------------------------------------------------------|
| EXEC DLI GN   | 2000-FIND-NEXT-AUTH-SUMMARY| PAUTSUM0   | Unqualified  | Sequential read of all root segments                 |
| EXEC DLI GNP  | 3000-FIND-NEXT-AUTH-DTL    | PAUTDTL1   | Unqualified  | Sequential read of all child segments under current root |
| EXEC DLI DLET | 5000-DELETE-AUTH-DTL       | PAUTDTL1   | —            | Delete currently positioned detail segment           |
| EXEC DLI DLET | 6000-DELETE-AUTH-SUMMARY   | PAUTSUM0   | —            | Delete root segment if both counts are zero          |
| EXEC DLI CHKP | 9000-TAKE-CHECKPOINT       | —          | ID(WK-CHKPT-ID) | IMS BMP checkpoint                               |

**Note:** The EXEC DLI form (with implicit PCB via PCB-OFFSET) is used throughout, unlike the batch utility programs (PAUDBUNL, DBUNLDGS, PAUDBLOD) which use explicit CALL 'CBLTDLI'. GN (Get Next) is used for the root segment to traverse all PAUTSUM0 records sequentially from first to last.

---

### 6. Expiry Check Logic (4000-CHECK-IF-EXPIRED, lines 277–298)

```
COMPUTE WS-AUTH-DATE = 99999 - PA-AUTH-DATE-9C
COMPUTE WS-DAY-DIFF = CURRENT-YYDDD - WS-AUTH-DATE
IF WS-DAY-DIFF >= WS-EXPIRY-DAYS -> QUALIFIED-FOR-DELETE
```

PA-AUTH-DATE-9C is stored as (99999 - YYDDD) in IMS. Reversing: `WS-AUTH-DATE = 99999 - PA-AUTH-DATE-9C` recovers the original YYDDD. CURRENT-YYDDD is the Julian date from `ACCEPT CURRENT-YYDDD FROM DAY`. The difference gives the age in days.

**Summary count adjustment on expiry (lines 287–293):**
- Approved record (PA-AUTH-RESP-CODE = '00'): SUBTRACT 1 FROM PA-APPROVED-AUTH-CNT; SUBTRACT PA-APPROVED-AMT FROM PA-APPROVED-AUTH-AMT
- Declined record: SUBTRACT 1 FROM PA-DECLINED-AUTH-CNT; SUBTRACT PA-TRANSACTION-AMT FROM PA-DECLINED-AUTH-AMT

These adjustments to the in-memory PENDING-AUTH-SUMMARY are what ultimately drive the 6000-DELETE-AUTH-SUMMARY condition check, but **the summary segment is NOT updated (REPL'd) with the adjusted counts before potential deletion.** The deletion condition checks the adjusted in-memory counts.

---

### 7. Summary Deletion Condition (line 156)

```cobol
IF PA-APPROVED-AUTH-CNT <= 0 AND PA-APPROVED-AUTH-CNT <= 0
   PERFORM 6000-DELETE-AUTH-SUMMARY
```

**Note:** This condition is `PA-APPROVED-AUTH-CNT <= 0 AND PA-APPROVED-AUTH-CNT <= 0` — both predicates reference PA-APPROVED-AUTH-CNT (the declined count is NOT checked; this appears to be a source code defect where PA-DECLINED-AUTH-CNT should have been used in the second predicate). The effect is that the summary is deleted only when PA-APPROVED-AUTH-CNT drops to zero or below, regardless of PA-DECLINED-AUTH-CNT.

---

### 8. Checkpointing (9000-TAKE-CHECKPOINT, lines 352–374)

```
EXEC DLI CHKP ID(WK-CHKPT-ID)
IF DIBSTAT = SPACES:
  ADD 1 to WS-NO-CHKP
  [if WS-NO-CHKP >= P-CHKP-DIS-FREQ]:
    DISPLAY checkpoint message
    RESET WS-NO-CHKP to 0
ELSE:
  DISPLAY error; PERFORM 9999-ABEND
```

IMS BMP checkpoint commits the UOW and enables restart from the checkpoint in case of failure. The checkpoint ID 'RMADnnnn' is used for IMS restart identification.

---

### 9. ABEND Logic (9999-ABEND, lines 377–386)

```
DISPLAY 'CBPAUP0C ABENDING ...'
MOVE 16 TO RETURN-CODE
GOBACK
```

Return code 16 signals job failure to the JCL. No program dump is explicitly requested (relying on ABENDAID DD).

---

### 10. Error Handling

| Condition                          | Response                                               |
|------------------------------------|--------------------------------------------------------|
| GN PAUTSUM0 status not ' ' or 'GB' | DISPLAY error + DIBSTAT; PERFORM 9999-ABEND (RC=16)   |
| GNP PAUTDTL1 status not ' ','GE','GB' | DISPLAY error + DIBSTAT; PERFORM 9999-ABEND (RC=16) |
| DLET PAUTDTL1 status not ' '       | DISPLAY error + DIBSTAT; PERFORM 9999-ABEND (RC=16)   |
| DLET PAUTSUM0 status not ' '       | DISPLAY error + DIBSTAT; PERFORM 9999-ABEND (RC=16)   |
| CHKP DIBSTAT not ' '               | DISPLAY error; PERFORM 9999-ABEND (RC=16)              |
| P-EXPIRY-DAYS not numeric          | Default to 5                                           |

---

### 11. JCL Overview (CBPAUP0J.jcl)

| Parameter     | Value                                       |
|---------------|---------------------------------------------|
| JOB CLASS     | A                                           |
| MSGCLASS      | H                                           |
| REGION        | 0M                                          |
| PGM           | DFSRRC00 (IMS region controller)            |
| PARM          | 'BMP,CBPAUP0C,PSBPAUTB'                    |
| STEPLIB       | IMS.SDFSRESL + XXXXXXXX.PROD.LOADLIB       |
| DFSRESLB      | IMS.SDFSRESL                               |
| PROCLIB       | IMS.PROCLIB                                |
| IMS           | IMS.PSBLIB + IMS.DBDLIB                    |
| SYSIN         | 00,00001,00001,Y (inline parameters)        |
| SYSOUX/SYSOUT/SYSABOUT/ABENDAID | SYSOUT=*                    |
| IEFRDER/IMSLOGR | DUMMY                                     |

The SYSIN in-stream data contains the run parameters in PRM-INFO format. The job does not specify DDPAUTP0 or DDPAUTX0 DD names explicitly — these are supplied by IMS via the database descriptor. The PSBPAUTB PSB (PROCOPT=AP) gives the program Add and Get access to the database.

---

### 12. Business Rules

1. Authorization records are expired based on their original date (stored in inverted form as PA-AUTH-DATE-9C).
2. The expiry threshold is configurable via SYSIN parameter P-EXPIRY-DAYS.
3. A summary segment is deleted only after all its child detail segments have been processed and the approved authorization count falls to zero or below.
4. Checkpoints are taken every P-CHKP-FREQ summary records to support restart/recovery.
5. Any IMS error causes immediate ABEND with return code 16.
6. A DEBUG mode (P-DEBUG-FLAG='Y') enables additional DISPLAY statements showing record counts.

---

### 13. I/O Specification

| Direction | Resource          | Operation | Description                                          |
|-----------|-------------------|-----------|------------------------------------------------------|
| Input     | SYSIN             | ACCEPT    | Program parameters (expiry days, checkpoint freq, debug flag) |
| Input/Del | IMS PAUTSUM0      | GN        | Sequential read of all authorization summary records |
| Input/Del | IMS PAUTDTL1      | GNP       | Sequential read of detail records under each summary |
| Delete    | IMS PAUTDTL1      | DLET      | Delete expired detail records                        |
| Delete    | IMS PAUTSUM0      | DLET      | Delete summary when no authorized records remain     |
| Output    | SYSOUT            | DISPLAY   | Statistics: summary/detail read/deleted counts; checkpoint messages |

---
