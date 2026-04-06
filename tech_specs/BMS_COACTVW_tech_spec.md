# Technical Specification: BMS Screen — COACTVW (View Account)

## 1. Screen Overview

| Attribute | Value |
|-----------|-------|
| Mapset | COACTVW |
| Map | CACTVWA |
| Source File | `app/bms/COACTVW.bms` |
| Copybook | `app/cpy-bms/COACTVW.CPY` |
| COBOL Program | COACTVWC |
| Domain | Accounts |

## 2. Purpose

Dense account detail viewer spanning rows 5–20. Single input (Account Number, numeric-only with MUSTFILL). All other fields read-only. Includes account financials and customer demographics.

## 3. Key Fields

### Input
| Field | Row,Col | Length | Attributes |
|-------|---------|--------|------------|
| ACCTSID | 5,38 | 11 | UNPROT, PICIN='99999999999', MUSTFILL |

### Account Financial Output
ACSTTUS(1), ADTOPEN(10), ACRDLIM(15, PICOUT='+ZZZ,ZZZ,ZZZ.99'), AEXPDT(10), ACSHLIM(15), AREISDT(10), ACURBAL(15), ACRCYCR(15), AADDGRP(10), ACRCYDB(15)

### Customer Demographic Output
ACSTNUM(9), ACSTSSN(12), ACSTDOB(10), ACSTFCO(3), ACSFNAM/ACSMNAM/ACSLNAM(25 each), ACSADL1/ACSADL2(50 each), ACSSTTE(2), ACSZIPC(5), ACSCITY(50), ACSCTRY(3), ACSPHN1/ACSPHN2(13 each), ACSGOVT(20), ACSEFTC(10), ACSPFLG(1)

## 4. Function Keys

F3=Exit

## 5. Technical Notes

Uses PICIN/PICOUT for formatted I/O. DSATTS=(COLOR,HILIGHT,PS,VALIDN), MAPATTS=(COLOR,HILIGHT,PS,VALIDN).
