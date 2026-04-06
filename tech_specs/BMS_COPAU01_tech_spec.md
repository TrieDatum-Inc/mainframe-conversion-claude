# Technical Specification: BMS Screen — COPAU01 (View Authorization Details)

## 1. Screen Overview

| Attribute | Value |
|-----------|-------|
| Mapset | COPAU01 |
| Map | COPAU1A |
| Source File | `app/app-authorization-ims-db2-mq/bms/COPAU01.bms` |
| COBOL Program | COPAUS1C |
| Domain | Authorization |

## 2. Purpose

Detailed view of a single authorization record. Includes card, amount, response, merchant details, and fraud status. Supports fraud marking action.

## 3. Screen Layout

```
Row 1-2:  [Standard header]
Row 4:    "View Authorization Details" (BRT,NEUTRAL)
Row 7:    Card Number: XXXXXXXXXXXXXXXX   Auth Date: XXXXXXXXXX   Time: XXXXXXXXXX
Row 9:    Response: X   Reason: XXXXXXXXXXXXXXXXXXXX   Auth Code: XXXXXX
Row 11:   Amount: XXXXXXXXXXXX   POS Mode: XXXX   Source: XXXXXXXXXX
Row 13:   MCC: XXXX   Card Exp: XXXXX   Auth Type: XXXXXXXXXXXXXX
Row 15:   Tran ID: XXXXXXXXXXXXXXX   Match: X (RED)   Fraud: XXXXXXXXXX (RED)
Row 17:   "Merchant Details -----..."
Row 19:   Name: XXXXXXXXXXXXXXXXXXXXXXXXX   ID: XXXXXXXXXXXXXXX
Row 21:   City: XXXXXXXXXXXXXXXXXXXXXXXXX   State: XX   Zip: XXXXXXXXXX
Row 23:   [Error message]
Row 24:   F3=Back  F5=Mark/Remove Fraud  F8=Next Auth
```

## 4. Output Fields

All fields are output (ASKIP): CARDNUM(16,PINK), AUTHDT(10), AUTHTM(10), AUTHRSP(1), AUTHRSN(20), AUTHCD(6), AUTHAMT(12), POSEMD(4), AUTHSRC(10), MCCCD(4), CRDEXP(5), AUTHTYP(14), TRNID(15), AUTHMTC(1,RED), AUTHFRD(10,RED), MERNAME(25), MERID(15), MERCITY(25), MERST(2), MERZIP(10)

## 5. Function Keys

| Key | Action |
|-----|--------|
| F3 | Back to COPAU00 |
| F5 | Mark/Remove fraud flag (triggers LINK to COPAUS2C) |
| F8 | Next authorization record |
