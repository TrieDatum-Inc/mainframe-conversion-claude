"""
Pydantic schemas for fraud management.

Maps to COPAUS2C fraud mark/remove operations on DB2 AUTHFRDS.
COPAUS1C invoked COPAUS2C via EXEC CICS LINK with action='F' or action='R'.
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class FraudActionRequest(BaseModel):
    """
    Fraud mark/remove request.

    Maps to the action flag passed from COPAUS1C to COPAUS2C:
    - 'mark'   → WS-REPORT-FRAUD ('F') — INSERT INTO AUTHFRDS
    - 'remove' → WS-REMOVE-FRAUD ('R') — UPDATE AUTHFRDS SET AUTH_FRAUD='R'
    """

    action: str = Field(
        ...,
        pattern="^(mark|remove)$",
        description="'mark' to flag as fraud, 'remove' to clear fraud flag",
    )


class FraudActionResponse(BaseModel):
    """
    Fraud action result.

    Maps to WS-FRD-UPDT-SUCCESS/WS-FRD-UPDT-FAILED return from COPAUS2C.
    """

    success: bool
    action: str
    fraud_flag: Optional[str] = Field(
        None, description="Current fraud flag: F=confirmed, R=removed, None=cleared"
    )
    fraud_report_date: Optional[date] = None
    message: str

    model_config = {"from_attributes": True}
