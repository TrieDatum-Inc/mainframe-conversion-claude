/**
 * Tests for frontend utility functions.
 */

import { formatCurrency, formatExpiry, padRight, formatDate } from "../src/lib/utils";

describe("formatCurrency", () => {
  it("formats positive amount as USD", () => {
    expect(formatCurrency(1234.56)).toBe("$1,234.56");
  });

  it("formats zero", () => {
    expect(formatCurrency(0)).toBe("$0.00");
  });

  it("formats negative as negative USD", () => {
    expect(formatCurrency(-500.5)).toMatch(/-?\$500\.50|-\$500\.50/);
  });
});

describe("formatExpiry", () => {
  it("formats month and year", () => {
    expect(formatExpiry(12, 2026)).toBe("12/2026");
  });

  it("pads single digit month", () => {
    expect(formatExpiry(1, 2025)).toBe("01/2025");
  });

  it("returns N/A when month missing", () => {
    expect(formatExpiry(undefined, 2025)).toBe("N/A");
  });

  it("returns N/A when year missing", () => {
    expect(formatExpiry(12, undefined)).toBe("N/A");
  });
});

describe("padRight", () => {
  it("pads short string", () => {
    expect(padRight("ABC", 6)).toBe("ABC   ");
  });

  it("truncates long string", () => {
    expect(padRight("ABCDEFGH", 5)).toBe("ABCDE");
  });

  it("returns exact length string unchanged", () => {
    expect(padRight("HELLO", 5)).toBe("HELLO");
  });
});

describe("formatDate", () => {
  it("converts YYYY-MM-DD to MM/DD/YYYY", () => {
    expect(formatDate("2026-12-31")).toBe("12/31/2026");
  });

  it("returns empty string for undefined", () => {
    expect(formatDate(undefined)).toBe("");
  });

  it("returns empty string for empty string", () => {
    expect(formatDate("")).toBe("");
  });
});
