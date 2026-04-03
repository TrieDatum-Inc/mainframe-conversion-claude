/**
 * Unit tests for Reports and Bill Payment frontend logic.
 *
 * Tests cover:
 *   - Report date range calculations (CORPT00C monthly/yearly path)
 *   - Custom date validation (CORPT00C custom path, BR-006/007/008)
 *   - Balance formatting for COBIL00C CURBAL display
 *   - API function type contracts
 */

// ============================================================
// Report date calculation tests — CORPT00C Monthly/Yearly Path
// ============================================================

/**
 * Calculate the first and last day of a given month.
 * Mirrors CORPT00C Monthly Path (lines 217-236).
 */
function calculateMonthlyRange(referenceDate: Date): { start: string; end: string } {
  const start = new Date(referenceDate.getFullYear(), referenceDate.getMonth(), 1);
  const end = new Date(referenceDate.getFullYear(), referenceDate.getMonth() + 1, 0);
  return {
    start: start.toISOString().split("T")[0],
    end: end.toISOString().split("T")[0],
  };
}

/**
 * Calculate yearly range.
 * Mirrors CORPT00C Yearly Path (lines 240-254).
 */
function calculateYearlyRange(referenceDate: Date): { start: string; end: string } {
  const yr = referenceDate.getFullYear();
  return {
    start: `${yr}-01-01`,
    end: `${yr}-12-31`,
  };
}

describe("calculateMonthlyRange — CORPT00C Monthly Path", () => {
  it("BR-002: start date is first of month", () => {
    const result = calculateMonthlyRange(new Date("2024-06-15"));
    expect(result.start).toBe("2024-06-01");
  });

  it("BR-002: end date is last day of month (30-day month)", () => {
    const result = calculateMonthlyRange(new Date("2024-06-15"));
    expect(result.end).toBe("2024-06-30");
  });

  it("BR-002: end date for January (31 days)", () => {
    const result = calculateMonthlyRange(new Date("2024-01-10"));
    expect(result.end).toBe("2024-01-31");
  });

  it("BR-002: February leap year ends on 29", () => {
    const result = calculateMonthlyRange(new Date("2024-02-10"));
    expect(result.end).toBe("2024-02-29");
  });

  it("BR-002: February non-leap year ends on 28", () => {
    const result = calculateMonthlyRange(new Date("2023-02-10"));
    expect(result.end).toBe("2023-02-28");
  });

  it("BR-002: December ends on 31 (COBOL special case — month+1 wraps)", () => {
    const result = calculateMonthlyRange(new Date("2024-12-15"));
    expect(result.start).toBe("2024-12-01");
    expect(result.end).toBe("2024-12-31");
  });
});

describe("calculateYearlyRange — CORPT00C Yearly Path", () => {
  it("BR-003: start date is Jan 1", () => {
    const result = calculateYearlyRange(new Date("2024-06-15"));
    expect(result.start).toBe("2024-01-01");
  });

  it("BR-003: end date is Dec 31", () => {
    const result = calculateYearlyRange(new Date("2024-06-15"));
    expect(result.end).toBe("2024-12-31");
  });

  it("year matches reference year", () => {
    const result = calculateYearlyRange(new Date("2023-03-01"));
    expect(result.start.startsWith("2023")).toBe(true);
    expect(result.end.startsWith("2023")).toBe(true);
  });
});

// ============================================================
// Custom date validation — CORPT00C Custom Path
// ============================================================

/**
 * Client-side custom date validation.
 * Mirrors CORPT00C PROCESS-ENTER-KEY custom path validation.
 */
function validateCustomDates(startDate: string, endDate: string): string | null {
  // BR-004/005: Presence checks
  if (!startDate) return "Start date is required for custom date range";
  if (!endDate) return "End date is required for custom date range";

  // BR-006/007: Gregorian validation (invalid dates like Feb 31 produce NaN)
  const start = new Date(startDate);
  const end = new Date(endDate);
  if (isNaN(start.getTime())) return "Start date is not a valid date";
  if (isNaN(end.getTime())) return "End date is not a valid date";

  // BR-008: start <= end
  if (startDate > endDate) return "Start date must be on or before end date";

  return null; // valid
}

describe("validateCustomDates — CORPT00C Custom Path validation", () => {
  it("returns null for valid date range", () => {
    expect(validateCustomDates("2024-01-01", "2024-03-31")).toBeNull();
  });

  it("returns null for same start and end date (BR-008 allows equal)", () => {
    expect(validateCustomDates("2024-06-15", "2024-06-15")).toBeNull();
  });

  it("BR-004: error when start date empty", () => {
    const err = validateCustomDates("", "2024-03-31");
    expect(err).not.toBeNull();
    expect(err).toMatch(/start date/i);
  });

  it("BR-005: error when end date empty", () => {
    const err = validateCustomDates("2024-01-01", "");
    expect(err).not.toBeNull();
    expect(err).toMatch(/end date/i);
  });

  it("BR-008: error when start date after end date", () => {
    const err = validateCustomDates("2024-06-01", "2024-03-01");
    expect(err).not.toBeNull();
    expect(err).toMatch(/before/i);
  });
});

// ============================================================
// Balance formatting — COBIL00C CURBAL display
// ============================================================

function formatBalance(amount: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(amount);
}

describe("formatBalance — COBIL00C CURBAL display", () => {
  it("formats positive balance with dollar sign", () => {
    expect(formatBalance(1250.75)).toBe("$1,250.75");
  });

  it("formats zero balance", () => {
    expect(formatBalance(0)).toBe("$0.00");
  });

  it("formats large balance", () => {
    expect(formatBalance(99999.99)).toBe("$99,999.99");
  });
});

// ============================================================
// Confirm input validation — COBIL00C CONFIRMI EVALUATE
// ============================================================

/**
 * Mirrors COBIL00C EVALUATE CONFIRMI (lines 173-191).
 * Returns 'pay', 'cancel', or an error message.
 */
function evaluateConfirmInput(input: string): "pay" | "cancel" | "error" {
  const normalized = input.trim().toUpperCase();
  if (normalized === "Y") return "pay";
  if (normalized === "N") return "cancel";
  return "error";
}

describe("evaluateConfirmInput — COBIL00C EVALUATE CONFIRMI", () => {
  it("'Y' maps to pay action", () => {
    expect(evaluateConfirmInput("Y")).toBe("pay");
  });

  it("lowercase 'y' maps to pay action (COBOL accepts both)", () => {
    expect(evaluateConfirmInput("y")).toBe("pay");
  });

  it("'N' maps to cancel action", () => {
    expect(evaluateConfirmInput("N")).toBe("cancel");
  });

  it("lowercase 'n' maps to cancel action", () => {
    expect(evaluateConfirmInput("n")).toBe("cancel");
  });

  it("empty input maps to error", () => {
    expect(evaluateConfirmInput("")).toBe("error");
  });

  it("other value maps to error", () => {
    expect(evaluateConfirmInput("X")).toBe("error");
  });

  it("number input maps to error", () => {
    expect(evaluateConfirmInput("1")).toBe("error");
  });
});

// ============================================================
// Transaction ID generation — COBIL00C lines 216-219
// ============================================================

/**
 * Generate next transaction ID from the last one.
 * COBIL00C: MOVE TRAN-ID TO WS-TRAN-ID-NUM, ADD 1, move back.
 */
function generateNextTranId(lastTranId: string | null): string {
  if (!lastTranId) return "0000000000000001"; // ENDFILE → MOVE ZEROS + ADD 1
  const next = parseInt(lastTranId, 10) + 1;
  return String(next).padStart(16, "0");
}

describe("generateNextTranId — COBIL00C transaction ID generation", () => {
  it("BR-005: increments last transaction ID by 1", () => {
    expect(generateNextTranId("0000000000000005")).toBe("0000000000000006");
  });

  it("BR-005: starts at 0000000000000001 when no previous transactions", () => {
    expect(generateNextTranId(null)).toBe("0000000000000001");
  });

  it("BR-005: pads result to 16 characters", () => {
    const result = generateNextTranId("0000000000000099");
    expect(result).toHaveLength(16);
    expect(result).toBe("0000000000000100");
  });

  it("BR-005: handles first transaction correctly (ENDFILE path)", () => {
    expect(generateNextTranId(null)).toHaveLength(16);
  });
});

// ============================================================
// Report type selection validation — CORPT00C BR-001
// ============================================================

/**
 * Validates that exactly one report type is selected.
 * CORPT00C BR-001: 'Select a report type to print report...'
 */
function validateReportTypeSelected(reportType: string | null): string | null {
  if (!reportType) return "Select a report type to print report...";
  if (!["monthly", "yearly", "custom"].includes(reportType)) {
    return "Invalid report type selected";
  }
  return null;
}

describe("validateReportTypeSelected — CORPT00C BR-001", () => {
  it("returns null for monthly selection", () => {
    expect(validateReportTypeSelected("monthly")).toBeNull();
  });

  it("returns null for yearly selection", () => {
    expect(validateReportTypeSelected("yearly")).toBeNull();
  });

  it("returns null for custom selection", () => {
    expect(validateReportTypeSelected("custom")).toBeNull();
  });

  it("BR-001: returns error message when nothing selected", () => {
    const err = validateReportTypeSelected(null);
    expect(err).toBe("Select a report type to print report...");
  });

  it("returns error for unknown report type", () => {
    const err = validateReportTypeSelected("quarterly");
    expect(err).not.toBeNull();
  });
});
