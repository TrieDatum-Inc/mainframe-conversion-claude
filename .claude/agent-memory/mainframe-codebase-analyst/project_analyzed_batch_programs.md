---
name: Analyzed Batch Programs
description: Summary of 18 batch programs analyzed and documented in tech_specs/ directory, including the CBACT, CBCUS, CBTRN series
type: project
---

**Why:** These programs were analyzed and spec'd as part of the migration_1 branch work. Specs are in tech_specs/.

## CBACT01C (tech_specs/CBACT01C_spec.md)

Account file multi-format output test. Reads ACCTFILE (KSDS) sequentially. Writes to 3 output files: OUTFILE (flat sequential, one record per account), ARRYFILE (array record with 5 occurrence slots - only 3 populated, 2 with hardcoded test data), VBRCFILE (variable-length 10-80 bytes - writes two VBR records per account: 12-byte status record + 39-byte balance record). Calls COBDATFT assembler program to convert ACCT-REISSUE-DATE format. Hardcoded default: if ACCT-CURR-CYC-DEBIT=0, OUT-ACCT-CURR-CYC-DEBIT is set to 2525.00. Output files not explicitly closed - defect. Diagnostic/demo program, not production logic.

## CBACT02C (tech_specs/CBACT02C_spec.md)

Card file display utility. Reads CARDFILE (KSDS) sequentially. No output file - displays CARD-RECORD to SYSOUT only. Uses CVACT02Y: CARD-NUM X(16), CARD-ACCT-ID 9(11), CARD-CVV-CD 9(03), CARD-EMBOSSED-NAME X(50), CARD-EXPIRAION-DATE X(10), CARD-ACTIVE-STATUS X(01). Pure diagnostic program.

## CBACT03C (tech_specs/CBACT03C_spec.md)

Cross-reference file display utility. Reads XREFFILE (KSDS) sequentially. Uses CVACT03Y: XREF-CARD-NUM X(16), XREF-CUST-ID 9(09), XREF-ACCT-ID 9(11). **Defect: double DISPLAY per record** - once inside 1000-XREFFILE-GET-NEXT (line 96) and once in main loop (line 78). CBACT02C has inner DISPLAY commented out; CBACT03C does not.

## CBACT04C (tech_specs/CBACT04C_spec.md)

Interest calculator - the most complex batch program. PROCEDURE DIVISION USING EXTERNAL-PARMS (PARM-LENGTH S9(04) COMP + PARM-DATE X(10) from JCL PARM). Reads TCATBAL-FILE (KSDS, sequential, sorted by account). For each account group: reads ACCOUNT-FILE (random I-O), XREF-FILE (random by alternate key ACCT-ID), DISCGRP-FILE (random by GROUP+TYPE+CAT). Interest formula: MONTHLY-INT = (TRAN-CAT-BAL * DIS-INT-RATE) / 1200. Default interest rate fallback: if group key '23' not found, retries with 'DEFAULT' as group ID. Generates interest TRAN-RECORD entries to TRANSACT-FILE with TRAN-TYPE-CD='01', TRAN-CAT-CD='05', TRAN-SOURCE='System'. At account break and EOF: REWRITEs account with ACCT-CURR-BAL += total_interest + zeros cycle credit/debit. 1400-COMPUTE-FEES is an empty stub. Transaction ID format: PARM-DATE(10) || suffix(6 digits).

## CBCUS01C (tech_specs/CBCUS01C_spec.md)

Customer file display utility. Reads CUSTFILE (KSDS) sequentially. Uses CVCUS01Y (500-byte): CUST-ID 9(09), name fields, 3-line address, state/country/zip, 2 phones, CUST-SSN 9(09), CUST-GOVT-ISSUED-ID X(20), CUST-DOB-YYYY-MM-DD X(10), CUST-EFT-ACCOUNT-ID X(10), CUST-PRI-CARD-HOLDER-IND X(01), CUST-FICO-CREDIT-SCORE 9(03). **Security note: DISPLAYs raw SSN and FICO score to SYSOUT.** Same double-DISPLAY defect as CBACT03C. Abend/IO-status paragraphs use Z- prefix (Z-ABEND-PROGRAM, Z-DISPLAY-IO-STATUS) instead of 9999-/9910- used by CBACT series.

## CBEXPORT (tech_specs/CBEXPORT_spec.md)

Branch migration export. Reads 5 VSAM input files sequentially (CUSTFILE/ACCTFILE/XREFFILE/TRANSACT/CARDFILE) in 5 separate passes and writes all records to EXPFILE (VSAM KSDS, 500-byte fixed). Each record gets type code: C=Customer, A=Account, X=Xref, T=Transaction, D=Card. Monotonically incrementing sequence number is VSAM key. CVEXPORT.cpy defines the union export record structure with REDEFINES. Numeric fields in CVEXPORT use COMP/COMP-3 - file is binary, not plain text. Hardcoded BRANCH-ID='0001', REGION-CODE='NORTH'. Calls CEE3ABD on error.

## CBIMPORT (tech_specs/CBIMPORT_spec.md)

Inverse of CBEXPORT. Reads EXPFILE sequentially, dispatches each record by type code to 5 normalized sequential output files (CUSTOUT/ACCTOUT/XREFOUT/TRNXOUT/CARDOUT). Unknown types go to ERROUT (132-byte pipe-delimited error records). 3000-VALIDATE-IMPORT is a stub - no actual validation. Output files are flat sequential, not VSAM. Calls CEE3ABD on fatal errors; ERROUT write failure is non-fatal.

## CBSTM03A (tech_specs/CBSTM03A_spec.md)

Statement generation main driver. Reads TRNXFILE/XREFFILE/CUSTFILE/ACCTFILE via CBSTM03B subroutine. Produces STMTFILE (80-byte plain text) and HTMLFILE (100-byte HTML). Uses ALTER/GO TO dispatch, PSA/TCB/TIOT control block walk, and a 2D in-memory array (51 cards x 10 transactions). Hard limit: max 51 card numbers or 10 transactions per card - no overflow handling. Calls CBSTM03B and CEE3ABD. Uses CUSTREC.cpy (not CVCUS01Y) - CUST-DOB-YYYYMMDD (no separators) vs CUST-DOB-YYYY-MM-DD in CVCUS01Y.

## CBSTM03B (tech_specs/CBSTM03B_spec.md)

Pure file I/O subroutine called by CBSTM03A. Handles Open/Read-seq/Read-keyed/Close for TRNXFILE (seq composite key CARD+TRAN-ID), XREFFILE (seq), CUSTFILE (random FD-CUST-ID PIC X(09)), ACCTFILE (random). Single LINKAGE parameter block (LK-M03B-AREA). Returns VSAM file status in LK-M03B-RC, record in LK-M03B-FLDT (1000 bytes). No error handling internally. W/Z (write/rewrite) not implemented. Uses PERFORM...THRU pattern.

## CBTRN01C (tech_specs/CBTRN01C_spec.md)

Daily transaction validation diagnostic. Reads DALYTRAN (sequential), validates card via XREFFILE (random), validates account via ACCTFILE (random). Does NOT post or write any records - DISPLAY-only output. Opens but never reads: CUSTFILE, CARDFILE, TRANSACT-FILE. **Defect: post-EOF lookups execute on stale data** (XREF/account lookup outside inner EOF guard). **Defect: 9000-DALYTRAN-CLOSE uses wrong status variable CUSTFILE-STATUS instead of DALYTRAN-STATUS on error.** Prototype/scaffolding program.

## CBTRN02C (tech_specs/CBTRN02C_spec.md)

Daily transaction posting - core posting engine. Reads DALYTRAN (sequential). Validation rules: 100=bad card, 101=account not found, 102=overlimit (uses CYC fields not CURR-BAL), 103=expired. Valid transactions: (1) write to TRANSACT-FILE (OUTPUT - fresh each run), (2) create or REWRITE TCATBAL-FILE entry, (3) REWRITE ACCOUNT-FILE balance. Rejects go to DALYREJS with 4-byte reason code + 76-byte description. RETURN-CODE=4 if any rejects. **Defect: 2800-UPDATE-ACCOUNT-REC REWRITE INVALID KEY sets reason=109 but does NOT abend** - transaction posted without account update. Uses overlimit formula: CYC-CREDIT - CYC-DEBIT + AMT > CREDIT-LIMIT. Both validation rules 102 and 103 checked sequentially - last failure code wins.

## CBTRN03C (tech_specs/CBTRN03C_spec.md)

Daily transaction detail report. Reads DATEPARM file (start-date WS-START-DATE X(10) + end-date WS-END-DATE X(10)). Filters TRANSACT-FILE (SEQUENTIAL organization - not KSDS) by TRAN-PROC-TS(1:10) within date range. For each qualifying record: keyed lookup CARDXREF (on card change only), TRANTYPE (always), TRANCATG (always). All lookup failures are fatal abends. Paginated at WS-PAGE-SIZE=20 lines. Totals: page total (reset each page), account total (reset each card), grand total. Report line width: 133 characters. CVTRA07Y defines all report structures (headers, detail, totals). **Defect: EOF branch double-counts last transaction amount in page total.** **Defect: final account total never written at EOF.**

## COBSWAIT (tech_specs/COBSWAIT_spec.md)

Minimal 4-line utility. Reads centiseconds from SYSIN, calls system routine MVSWAIT to suspend execution for that duration. Used in JCL job streams to pace processing or wait for resources. No error handling. PIC 9(8) COMP parameter = max ~11.57 days.

## CSUTLDTC (tech_specs/CSUTLDTC_spec.md)

Date validation subroutine. Called with (date X(10), format X(10), result X(80)). Calls IBM LE CEEDAYS API to convert date to Lilian format and capture feedback. Returns RETURN-CODE = severity (0=valid). FC-INVALID-DATE (all-zero hex) = valid date (counter-intuitive naming). Used by CORPT00C (online) for custom date range validation with format 'YYYY-MM-DD'. Future date (msg '2513') is explicitly accepted by CORPT00C. All linkage via static COBOL CALL (not CICS LINK).
