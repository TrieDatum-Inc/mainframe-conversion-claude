# Technical Specification: BMS Screen — COADM01 (Admin Menu)

## 1. Screen Overview

| Attribute | Value |
|-----------|-------|
| Mapset | COADM01 |
| Map | COADM1A |
| Source File | `app/bms/COADM01.bms` |
| Copybook | `app/cpy-bms/COADM01.CPY` |
| COBOL Program | COADM01C |
| Domain | Navigation (Admin) |

## 2. Purpose

Admin navigation menu. Structurally identical to COMEN01 but title reads "Admin Menu" and options come from COADM02Y (6 admin options: User CRUD + Transaction Type maintenance).

## 3. Screen Layout

Identical to COMEN01 except Row 4 title: "Admin Menu" (10 chars vs 9).

## 4. Field Definitions

Same as COMEN01: OPTION input (2 digits), OPTN001–OPTN012 output, ERRMSG.

## 5. Function Keys

| Key | Action |
|-----|--------|
| ENTER | Navigate to selected admin option |
| F3 | Exit |
