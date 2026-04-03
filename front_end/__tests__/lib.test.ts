/**
 * Unit tests for frontend utility functions.
 * Testing lib/utils.ts and lib/api.ts helpers.
 */
import {
  formatHeaderDate,
  formatHeaderTime,
  getErrorMessage,
  messageTypeToClass,
  isAdmin,
} from "../lib/utils";

// ============================================================
// formatHeaderDate — maps COBOL POPULATE-HEADER-INFO date formatting
// ============================================================

describe("formatHeaderDate", () => {
  it("formats ISO date to MM/DD/YY", () => {
    const result = formatHeaderDate("2026-04-03T10:30:00Z");
    expect(result).toMatch(/^\d{2}\/\d{2}\/\d{2}$/);
  });

  it("returns empty string for invalid date", () => {
    // Invalid dates should not crash — graceful degradation
    expect(formatHeaderDate("not-a-date")).toBe("");
  });
});

// ============================================================
// formatHeaderTime — maps COBOL HH:MM:SS format
// ============================================================

describe("formatHeaderTime", () => {
  it("returns HH:MM:SS format", () => {
    const result = formatHeaderTime("2026-04-03T14:25:36Z");
    expect(result).toMatch(/^\d{2}:\d{2}:\d{2}$/);
  });
});

// ============================================================
// getErrorMessage — extracts API error messages
// ============================================================

describe("getErrorMessage", () => {
  it("extracts string detail from API error", () => {
    const err = { detail: "User not found. Try again ..." };
    expect(getErrorMessage(err)).toBe("User not found. Try again ...");
  });

  it("extracts nested detail.message from API error", () => {
    const err = { detail: { message: "Please enter a valid option number..." } };
    expect(getErrorMessage(err)).toBe("Please enter a valid option number...");
  });

  it("returns fallback message for unknown error", () => {
    expect(getErrorMessage(null)).toBe("An unexpected error occurred");
    expect(getErrorMessage(undefined)).toBe("An unexpected error occurred");
  });
});

// ============================================================
// messageTypeToClass — maps DFHRED/DFHGREEN to CSS
// ============================================================

describe("messageTypeToClass", () => {
  it("returns red class for error type (DFHRED)", () => {
    const cls = messageTypeToClass("error");
    expect(cls).toContain("red");
  });

  it("returns green class for info type (DFHGREEN)", () => {
    const cls = messageTypeToClass("info");
    expect(cls).toContain("green");
  });

  it("returns gray class for null type", () => {
    const cls = messageTypeToClass(null);
    expect(cls).toContain("gray");
  });
});

// ============================================================
// isAdmin — maps CDEMO-USRTYP-ADMIN condition
// ============================================================

describe("isAdmin", () => {
  it("returns true for user_type A", () => {
    expect(isAdmin("A")).toBe(true);
  });

  it("returns false for user_type U", () => {
    expect(isAdmin("U")).toBe(false);
  });
});
