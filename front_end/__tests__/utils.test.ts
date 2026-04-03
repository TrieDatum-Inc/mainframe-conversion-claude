/**
 * Frontend utility tests — mirrors COBOL display formatting logic.
 */

import { formatAmount, formatDateMMDDYY, truncateDesc } from "@/lib/utils";

describe("formatAmount", () => {
  test("negative amount shows minus sign", () => {
    expect(formatAmount(-52.47)).toBe("-00000052.47");
  });

  test("positive amount shows plus sign", () => {
    expect(formatAmount(250.0)).toBe("+00000250.00");
  });

  test("zero shows plus sign", () => {
    expect(formatAmount(0)).toBe("+00000000.00");
  });

  test("large negative amount", () => {
    const result = formatAmount(-99999999.99);
    expect(result.startsWith("-")).toBe(true);
    expect(result).toContain("99999999");
  });
});

describe("formatDateMMDDYY", () => {
  test("formats ISO timestamp to MM/DD/YY", () => {
    const result = formatDateMMDDYY("2026-03-15T09:00:00.000Z");
    expect(result).toBe("03/15/26");
  });
});

describe("truncateDesc", () => {
  test("short description passes through unchanged", () => {
    expect(truncateDesc("Short desc")).toBe("Short desc");
  });

  test("long description truncated with ellipsis", () => {
    const long = "This is a very long transaction description that exceeds the limit";
    const result = truncateDesc(long, 26);
    expect(result.length).toBeLessThanOrEqual(26);
    expect(result.endsWith("…")).toBe(true);
  });

  test("exactly 26 chars passes through unchanged", () => {
    const exact = "A".repeat(26);
    expect(truncateDesc(exact, 26)).toBe(exact);
  });
});
