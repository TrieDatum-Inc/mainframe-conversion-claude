"""User management schemas matching COBOL CSUSR01Y.cpy and COUSR00C/COUSR01C/COUSR02C screens.

- UserListItem: list columns from COUSR00C screen
- UserCreate: new user input from COUSR01C
- UserUpdate: partial update from COUSR02C
- UserRead: display fields from COUSR02C (no password)
"""

from typing import Optional

from pydantic import BaseModel, Field


class UserListItem(BaseModel):
    """User list item matching COUSR00C screen columns.

    Fields from CSUSR01Y.cpy SEC-USER-DATA.
    """

    usr_id: str = Field(..., max_length=8, description="User ID (SEC-USR-ID PIC X(08))")
    usr_fname: str = Field(
        ..., max_length=20, description="First name (SEC-USR-FNAME PIC X(20))"
    )
    usr_lname: str = Field(
        ..., max_length=20, description="Last name (SEC-USR-LNAME PIC X(20))"
    )
    usr_type: str = Field(
        ..., max_length=1, description="User type A/U (SEC-USR-TYPE PIC X(01))"
    )


class UserCreate(BaseModel):
    """New user input matching COUSR01C screen.

    All fields from CSUSR01Y.cpy SEC-USER-DATA.
    """

    usr_id: str = Field(..., max_length=8, description="User ID (SEC-USR-ID PIC X(08))")
    usr_fname: str = Field(
        ..., max_length=20, description="First name (SEC-USR-FNAME PIC X(20))"
    )
    usr_lname: str = Field(
        ..., max_length=20, description="Last name (SEC-USR-LNAME PIC X(20))"
    )
    usr_pwd: str = Field(
        ..., max_length=8, description="Password (SEC-USR-PWD PIC X(08))"
    )
    usr_type: str = Field(
        ..., max_length=1, description="User type A/U (SEC-USR-TYPE PIC X(01))"
    )


class UserUpdate(BaseModel):
    """User update matching COUSR02C input. Only non-None fields are applied."""

    usr_fname: Optional[str] = Field(None, max_length=20, description="First name")
    usr_lname: Optional[str] = Field(None, max_length=20, description="Last name")
    usr_pwd: Optional[str] = Field(None, max_length=8, description="Password")
    usr_type: Optional[str] = Field(None, max_length=1, description="User type A/U")


class UserRead(BaseModel):
    """User display matching COUSR02C output (no password exposed)."""

    usr_id: str = Field(..., max_length=8, description="User ID (SEC-USR-ID PIC X(08))")
    usr_fname: str = Field(
        ..., max_length=20, description="First name (SEC-USR-FNAME PIC X(20))"
    )
    usr_lname: str = Field(
        ..., max_length=20, description="Last name (SEC-USR-LNAME PIC X(20))"
    )
    usr_type: str = Field(
        ..., max_length=1, description="User type A/U (SEC-USR-TYPE PIC X(01))"
    )
