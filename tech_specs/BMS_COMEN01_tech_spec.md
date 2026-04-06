# Technical Specification: BMS Screen — COMEN01 (Main Menu)

## 1. Screen Overview

| Attribute | Value |
|-----------|-------|
| Mapset | COMEN01 |
| Map | COMEN1A |
| Source File | `app/bms/COMEN01.bms` |
| Copybook | `app/cpy-bms/COMEN01.CPY` |
| COBOL Program | COMEN01C |
| Domain | Navigation |

## 2. Purpose

Main navigation menu for regular (non-admin) users. Displays up to 12 dynamically populated menu options and accepts a 2-digit selection.

## 3. Screen Layout

```
Row 1-2:  [Standard header]
Row 4:    "Main Menu" (centered, BRT)
Row 6-17: [12 menu option lines - OPTN001 through OPTN012]
Row 20:   "Please select an option :" [__] (2 digits)
Row 23:   [Error message - RED]
Row 24:   ENTER=Continue  F3=Exit
```

## 4. Field Definitions

### Input Fields
| Field | Row,Col | Length | Attributes |
|-------|---------|--------|------------|
| OPTION | 20,41 | 2 | FSET,IC,NORM,NUM,UNPROT,UNDERLINE,JUSTIFY(RIGHT,ZERO) |

### Output Fields
| Field | Row,Col | Length | Attributes |
|-------|---------|--------|------------|
| OPTN001–OPTN012 | 6–17,20 | 40 each | ASKIP,FSET,NORM,BLUE |
| ERRMSG | 23,1 | 78 | ASKIP,BRT,FSET,RED |

## 5. Function Keys

| Key | Action |
|-----|--------|
| ENTER | Navigate to selected option |
| F3 | Exit/logout |

## 6. Navigation

Selection routes to programs defined in COMEN02Y array:
Options 01–11 covering Account View/Update, Card List/View/Update, Transaction List/View/Add, Reports, Bill Payment, and Pending Authorization View.
