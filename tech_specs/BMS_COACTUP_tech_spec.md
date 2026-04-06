# Technical Specification: BMS Screen — COACTUP (Update Account)

## 1. Screen Overview

| Attribute | Value |
|-----------|-------|
| Mapset | COACTUP |
| Map | CACTUPA |
| Source File | `app/bms/COACTUP.bms` |
| Copybook | `app/cpy-bms/COACTUP.CPY` |
| COBOL Program | COACTUPC |
| Domain | Accounts |

## 2. Purpose

Full account and customer edit form. Mirrors COACTVW layout but all fields are UNPROT (editable).

## 3. Key Differences from COACTVW

- All fields are UNPROT (editable)
- SSN split into 3 fields: ACTSSN1(3), ACTSSN2(2), ACTSSN3(4) with literal hyphens
- Date fields split: year(4)/month(2)/day(2) sub-fields with JUSTIFY=RIGHT
- Phone numbers split: area(3)/prefix(3)/number(4)
- Financial fields are FSET,UNPROT without PICOUT formatting
- F5=Save and F12=Cancel function keys are initially DRK (hidden), revealed dynamically

## 4. Function Keys

| Key | Visibility | Action |
|-----|-----------|--------|
| ENTER | Always | Process/validate |
| F3 | Always | Exit |
| F5 | Dynamic (DRK→visible) | Save |
| F12 | Dynamic (DRK→visible) | Cancel |
