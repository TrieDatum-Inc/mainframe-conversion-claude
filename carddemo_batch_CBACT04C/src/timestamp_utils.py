"""
DB2-format timestamp utilities for CBACT04C.

Replicates COBOL paragraph Z-GET-DB2-FORMAT-TIMESTAMP which builds a 26-character
timestamp string in DB2 format: YYYY-MM-DD-HH.MM.SS.mmm0000

COBOL paragraph logic:
    MOVE FUNCTION CURRENT-DATE TO COBOL-TS (21 chars)
    COBOL-TS layout:
        COBOL-TS-YYYY  PIC 9(4)   positions 1-4
        COBOL-TS-MM    PIC 9(2)   positions 5-6
        COBOL-TS-DD    PIC 9(2)   positions 7-8
        COBOL-TS-HH    PIC 9(2)   positions 9-10
        COBOL-TS-MN    PIC 9(2)   positions 11-12
        COBOL-TS-SS    PIC 9(2)   positions 13-14
        COBOL-TS-MS    PIC 9(2)   positions 15-16 (hundredths of second)
    DB2-FORMAT-TS = YYYY-MM-DD-HH.MM.SS.mmm0000  (26 chars, PIC X(26))
    where mmm is milliseconds (hundredths * 10, zero-padded to 3 digits)
"""

from datetime import datetime, timezone


def get_db2_format_timestamp(dt: datetime | None = None) -> str:
    """
    Build a 26-character DB2-format timestamp string.

    Replaces COBOL paragraph Z-GET-DB2-FORMAT-TIMESTAMP.

    Format: YYYY-MM-DD-HH.MM.SS.mmm0000
    Example: 2026-04-07-01.30.00.0000000

    Args:
        dt: datetime to format. Defaults to current UTC time.

    Returns:
        26-character DB2-format timestamp string.
    """
    if dt is None:
        dt = datetime.now(timezone.utc)

    # COBOL CURRENT-DATE provides hundredths of second (2 digits).
    # DB2 format uses microseconds in the fractional part (7 digits: mmm0000).
    # We derive milliseconds from the Python microsecond field.
    milliseconds = dt.microsecond // 1000  # microseconds -> milliseconds

    # DB2 fractional part is 7 digits: mmm followed by 4 zeros
    # COBOL: DB2-FORMAT-TS-MS = COBOL-TS-MS * 10 (converts hundredths to tenths of milliseconds)
    fractional = f"{milliseconds:03d}0000"  # 7 chars total

    return (
        f"{dt.year:04d}-{dt.month:02d}-{dt.day:02d}-"
        f"{dt.hour:02d}.{dt.minute:02d}.{dt.second:02d}.{fractional}"
    )


def parse_db2_timestamp(ts_str: str) -> datetime:
    """
    Parse a DB2-format timestamp string back to a datetime object.

    Args:
        ts_str: 26-character DB2 timestamp string (YYYY-MM-DD-HH.MM.SS.mmm0000).

    Returns:
        datetime (UTC).
    """
    # Format: YYYY-MM-DD-HH.MM.SS.mmm0000
    # Example: 2026-04-07-01.30.00.0000000
    try:
        frac_part = ts_str[20:23]  # mmm (first 3 digits of fractional)
        # Rebuild as parseable string: YYYY-MM-DD HH:MM:SS
        date_str = ts_str[0:10]       # YYYY-MM-DD
        time_str = ts_str[11:19]      # HH.MM.SS -> HH:MM:SS
        time_str = time_str.replace(".", ":")
        ms = int(frac_part) * 1000    # milliseconds -> microseconds
        return datetime.strptime(
            f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S"
        ).replace(microsecond=ms, tzinfo=timezone.utc)
    except (ValueError, IndexError) as exc:
        raise ValueError(f"Cannot parse DB2 timestamp '{ts_str}': {exc}") from exc
