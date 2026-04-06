# Technical Specification: COBSWAIT — Wait Utility

## 1. Program Overview

| Attribute | Value |
|-----------|-------|
| Program ID | COBSWAIT |
| Source File | `app/cbl/COBSWAIT.cbl` |
| Type | Batch COBOL (Utility) |

## 2. Purpose

COBSWAIT is a **timing utility** that reads a numeric value (centiseconds) from SYSIN and calls the assembler routine MVSWAIT to pause execution. Used in JCL job streams to introduce controlled delays between steps.

## 3. Interface

- Input: ACCEPT from SYSIN — numeric value in centiseconds
- External Call: `CALL 'MVSWAIT' USING MVSWAIT-TIME` where MVSWAIT-TIME is PIC 9(8) COMP

## 4. Assembler Dependency

MVSWAIT.asm wraps the MVS STIMER SVC via the ASMWAIT macro (`STIMER WAIT,BINTVL=&B`).

## 5. JCL Usage

Used in the WAITSTEP JCL job within daily batch chains (CLOSEFIL → TRANBKP → WAITSTEP → OPENFIL) to wait for CICS file closure before reopening.
