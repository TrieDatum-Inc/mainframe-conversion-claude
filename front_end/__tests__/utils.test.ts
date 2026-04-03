/**
 * Tests for frontend utility functions.
 */

import { formatCurrency, formatDate, parsePhone, parseSsn } from "@/lib/utils";

describe("formatCurrency", () => {
  it("formats positive value with + sign", () => {
    expect(formatCurrency(1250.75)).toBe("+1,250.75");
  });

  it("formats zero with space sign", () => {
    expect(formatCurrency(0)).toBe(" 0.00");
  });

  it("formats negative value with - sign", () => {
    expect(formatCurrency(-500)).toBe("-500.00");
  });
});

describe("formatDate", () => {
  it("formats ISO date as MM/DD/YYYY", () => {
    expect(formatDate("2020-01-15")).toBe("01/15/2020");
  });

  it("returns empty string for null", () => {
    expect(formatDate(null)).toBe("");
  });

  it("returns empty string for undefined", () => {
    expect(formatDate(undefined)).toBe("");
  });
});

describe("parsePhone", () => {
  it("parses (202)456-1111", () => {
    const result = parsePhone("(202)456-1111");
    expect(result).toEqual({
      area_code: "202",
      prefix: "456",
      line_number: "1111",
    });
  });

  it("returns null for invalid format", () => {
    expect(parsePhone("202-456-1111")).toBeNull();
  });

  it("returns null for null input", () => {
    expect(parsePhone(null)).toBeNull();
  });
});

describe("parseSsn", () => {
  it("splits 9-digit SSN into 3 parts", () => {
    const result = parseSsn("123456789");
    expect(result).toEqual({ part1: "123", part2: "45", part3: "6789" });
  });

  it("returns null for null input", () => {
    expect(parseSsn(null)).toBeNull();
  });
});
