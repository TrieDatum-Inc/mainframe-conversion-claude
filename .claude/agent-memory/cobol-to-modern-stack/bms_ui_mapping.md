---
name: BMS-to-UI Mapping Patterns
description: How BMS DFHMDF field attributes map to React/Tailwind components
type: reference
---

## BMS Field Attributes to React

| BMS Attribute | React/HTML Equivalent |
|--------------|-----------------------|
| ATTRB=(UNPROT) | `<input>` editable field |
| ATTRB=(ASKIP) | `<input readOnly>` or `<div>` display field |
| ATTRB=(PROT) | `<input disabled>` |
| ATTRB=(DRK) | `<input type="password">` |
| ATTRB=(NUM) | `<input type="number" inputMode="numeric">` |
| ATTRB=(IC) | `autoFocus` on the first editable field |
| ATTRB=(FSET) | Always send field content — no UI equivalent needed |
| ATTRB=(BRT) | `font-bold` or highlighted text |

## BMS Colors to Tailwind

| BMS Color | Tailwind Usage |
|-----------|---------------|
| DFHGREEN / GREEN | `text-green-700`, `border-b-green-500` on input, success messages `bg-green-50` |
| DFHRED / RED | `text-red-600`, `bg-red-50` for error messages |
| DFHBLUE / BLUE | `text-blue-600` for labels and metadata |
| DFHYELLO / YELLOW | `text-yellow-400` for titles (TITLE01/TITLE02) |
| DFHTURQ / TURQUOISE | `text-cyan-700` for field labels |
| DFHNEUTR / NEUTRAL | `text-gray-600`, `bg-blue-50` for informational messages |

## BMS Function Keys to UI Buttons

| BMS PF Key | Button Text | Variant |
|-----------|------------|---------|
| ENTER | "Submit" / "Add User" / "Search" | primary |
| PF3 Save&Exit (COUSR02C) | "Save & Exit (F3)" | secondary |
| PF3 Back/Cancel (COUSR03C) | "Back / Cancel (F3)" | secondary |
| PF4 Clear | "Clear (F4)" | ghost |
| PF5 Save | "Save (F5)" | primary |
| PF5 Delete confirm | "Delete (F5)" | danger |
| PF7 Backward | "F7 - Backward" | secondary, disabled when no prev page |
| PF8 Forward | "F8 - Forward" | secondary, disabled when no next page |
| PF12 Cancel | "Cancel (F12)" | ghost |

## BMS Screen Header (Rows 1-2) Component

Standard COUSR0x header (PageHeader component):
- Row 1: "Tran: [TRNNAME]  [TITLE01]  Date: [CURDATE]"
- Row 2: "Prog: [PGMNAME]  [TITLE02]  Time: [CURTIME]"
- Row 4 center: Screen title (bold)
- Colors: TRNNAME/CURDATE/CURTIME in BLUE, TITLE01/TITLE02 in YELLOW

## ERRMSG Field (Row 23)

StatusMessage component with three types:
- `type="error"` → red (DFHRED — validation errors, not found)
- `type="success"` → green (DFHGREEN — 'User has been added/updated/deleted...')
- `type="info"` → blue (DFHNEUTR — 'Press PF5 to save...' etc.)

## Delete Screen ASKIP Fields

COUSR03C: FNAME/LNAME/USRTYPE are ASKIP (read-only for confirmation).
In React: render as `<FormField readOnly>` with `bg-gray-50` styling.
No password field on this screen (COUSR03 BMS map has no PASSWD field).
