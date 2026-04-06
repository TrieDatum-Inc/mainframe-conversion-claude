/**
 * Tests for utility functions.
 * Covers formatting and Tailwind class helpers.
 */

import {
  formatCurrency,
  formatDate,
  formatTime,
  getAccountStatusClasses,
  getFraudBadgeClasses,
  getMatchStatusClasses,
  getResponseBadgeClasses,
  maskCardNumber,
} from "@/lib/utils";

describe("formatCurrency", () => {
  it("formats positive amount with dollar sign", () => {
    expect(formatCurrency("12345.67")).toBe("$12,345.67");
  });

  it("formats zero", () => {
    expect(formatCurrency("0")).toBe("$0.00");
  });

  it("handles null gracefully", () => {
    expect(formatCurrency(null)).toBe("$0.00");
  });

  it("handles undefined gracefully", () => {
    expect(formatCurrency(undefined)).toBe("$0.00");
  });

  it("formats number input", () => {
    expect(formatCurrency(500)).toBe("$500.00");
  });
});

describe("formatDate", () => {
  it("converts ISO date to MM/DD/YYYY", () => {
    expect(formatDate("2026-04-01")).toBe("04/01/2026");
  });

  it("returns empty string for null", () => {
    expect(formatDate(null)).toBe("");
  });

  it("returns empty string for undefined", () => {
    expect(formatDate(undefined)).toBe("");
  });
});

describe("formatTime", () => {
  it("returns HH:MM:SS portion", () => {
    expect(formatTime("10:23:45")).toBe("10:23:45");
  });

  it("returns empty string for null", () => {
    expect(formatTime(null)).toBe("");
  });
});

describe("maskCardNumber", () => {
  it("masks all but last 4 digits", () => {
    expect(maskCardNumber("4111111111111111")).toBe("**** **** **** 1111");
  });

  it("handles short card numbers gracefully", () => {
    const result = maskCardNumber("1234");
    expect(result).toBe("1234"); // too short to mask, returns as-is
  });
});

describe("getResponseBadgeClasses", () => {
  it("returns green classes for approved", () => {
    const classes = getResponseBadgeClasses("A");
    expect(classes).toContain("green");
  });

  it("returns red classes for declined", () => {
    const classes = getResponseBadgeClasses("D");
    expect(classes).toContain("red");
  });
});

describe("getFraudBadgeClasses", () => {
  it("returns red bold classes when fraud confirmed (F)", () => {
    const classes = getFraudBadgeClasses("F");
    expect(classes).toContain("red");
    expect(classes).toContain("bold");
  });

  it("returns yellow classes when fraud removed (R)", () => {
    const classes = getFraudBadgeClasses("R");
    expect(classes).toContain("yellow");
  });

  it("returns gray classes when no fraud status", () => {
    const classes = getFraudBadgeClasses(null);
    expect(classes).toContain("gray");
  });
});

describe("getMatchStatusClasses", () => {
  it("P=Pending returns blue", () => {
    expect(getMatchStatusClasses("P")).toContain("blue");
  });

  it("D=Declined returns red", () => {
    expect(getMatchStatusClasses("D")).toContain("red");
  });

  it("E=Expired returns gray", () => {
    expect(getMatchStatusClasses("E")).toContain("gray");
  });

  it("M=Matched returns green", () => {
    expect(getMatchStatusClasses("M")).toContain("green");
  });
});

describe("getAccountStatusClasses", () => {
  it("Active account returns green", () => {
    expect(getAccountStatusClasses("A")).toContain("green");
  });

  it("Closed account returns red", () => {
    expect(getAccountStatusClasses("C")).toContain("red");
  });
});
