"""
Constants for CBACT04C Interest Calculation Pipeline.

Replaces hardcoded COBOL values in paragraph 1300-B-WRITE-TX and business rules.
All constants match the original COBOL specification exactly.
"""

# Transaction type/category for generated interest charge records
# COBOL: MOVE '01' TO TRAN-TYPE-CD   (paragraph 1300-B-WRITE-TX)
INTEREST_TRAN_TYPE_CD: str = "01"

# COBOL: MOVE 05 TO TRAN-CAT-CD  (paragraph 1300-B-WRITE-TX)
INTEREST_TRAN_CAT_CD: int = 5

# COBOL: MOVE 'System' TO TRAN-SOURCE  (paragraph 1300-B-WRITE-TX, PIC X(10))
INTEREST_TRAN_SOURCE: str = "System"

# COBOL: MOVE 0 TO TRAN-MERCHANT-ID  (paragraph 1300-B-WRITE-TX)
INTEREST_TRAN_MERCHANT_ID: int = 0

# COBOL: MOVE SPACES TO TRAN-MERCHANT-NAME, TRAN-MERCHANT-CITY, TRAN-MERCHANT-ZIP
INTEREST_TRAN_MERCHANT_NAME: str = ""
INTEREST_TRAN_MERCHANT_CITY: str = ""
INTEREST_TRAN_MERCHANT_ZIP: str = ""

# COBOL: MOVE 'Int. for a/c ' TO TRAN-DESC-PREFIX  (paragraph 1300-B-WRITE-TX)
INTEREST_TRAN_DESC_PREFIX: str = "Int. for a/c "

# DISCGRP fallback group identifier
# COBOL paragraph 1200-A-GET-DEFAULT-INT-RATE: MOVE 'DEFAULT' TO FD-DIS-ACCT-GROUP-ID
DEFAULT_DISCLOSURE_GROUP: str = "DEFAULT"

# TRAN-ID length constraints
# COBOL: PARM-DATE X(10) prefix + WS-TRANID-SUFFIX 9(6) zero-padded counter
# TRAN-ID is PIC X(16); run_date stored without dashes (YYYYMMDD = 8 chars) + 6-digit suffix = 14 chars
TRAN_ID_DATE_CHARS: int = 8   # YYYYMMDD without dashes
TRAN_ID_SUFFIX_DIGITS: int = 6

# Interest calculation divisor
# COBOL: COMPUTE WS-MONTHLY-INT = (TRAN-CAT-BAL * DIS-INT-RATE) / 1200
# 1200 = 12 months * 100 (percent-to-fraction conversion)
INTEREST_DIVISOR: int = 1200

# Source system tag for pipeline_metrics
SOURCE_PROGRAM: str = "CBACT04C"
DATABRICKS_JOB_NAME: str = "cbact04c_interest_calc"
