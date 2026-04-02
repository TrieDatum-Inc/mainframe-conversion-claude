# Agent Memory Index

- [User Profile](user_profile.md) — User works on CardDemo mainframe modernization project at Triedatum Inc; analyzes z/OS COBOL for migration
- [CardDemo Architecture](project_carddemo_architecture.md) — Core architecture: 5 VSAM KSDS files, batch+online COBOL, copybook conventions, call graph
- [Analyzed Programs - Batch](project_analyzed_batch_programs.md) — Summary of 18 batch programs: CBACT01-04C, CBCUS01C, CBEXPORT, CBIMPORT, CBSTM03A/B, CBTRN01-03C, COBSWAIT, CSUTLDTC
- [Online Sign-on and Navigation](project_online_signon_navigation.md) — COSGN00C/COMEN01C/COADM01C: COMMAREA protocol, auth flow, menu dispatch, BMS conventions, known defects
- [User Management Subsystem](project_user_management_subsystem.md) — COUSR00C/01C/02C/03C + BMS maps: USRSEC file, COMMAREA patterns, 10 known defects, specs written
- [Transaction Management Programs](project_transaction_management.md) — COTRN00C/01C/02C: pagination design, READ UPDATE issue, non-atomic ID gen, XREF pattern, COMMAREA aliasing
- [Billing and Reporting Subsystem](project_billing_reporting_subsystem.md) — COBIL00C (CB00) full-balance payment, CORPT00C (CR00) TDQ job submit, CSUTLDTC date validator, COBSWAIT batch wait
- [Credit Card Management Subsystem](project_credit_card_management.md) — COCRDLIC/COCRDSLC/COCRDUPC + BMS maps: CARDDAT browse/read/update, pagination, state machine, optimistic locking, 6 spec files written
- [Authorization Subsystem IMS/DB2/MQ](project_authorization_subsystem.md) — COPAUA0C/S0C/S1C/S2C + CBPAUP0C + 3 batch utilities; IMS complement key, MQ trigger, DB2 AUTHFRDS, 3 known defects
- [Transaction Type DB2 and VSAM-MQ](project_transaction_type_and_vsam_mq.md) — COBTUPDT batch + COTRTLIC/COTRTUPC CICS + 2 BMS maps + COACCT01/CODATE01 MQ services; DB2 cursor paging, state machine, MQ request-reply pattern
- [Account Management Subsystem](project_account_management_subsystem.md) — COACTUPC/COACTVWC + BMS maps: 6-state machine, optimistic locking, SYNCPOINT ROLLBACK, 35-field validation, 4 spec files written
- [Copybook Catalog](project_carddemo_architecture.md) — All 57 copybooks cataloged; CICS FCT names, DB2 tables, IMS PCBs, XCTL graph documented in COPYBOOKS_spec.md + SYSTEM_OVERVIEW_spec.md
