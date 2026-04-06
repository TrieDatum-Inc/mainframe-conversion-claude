/**
 * Tests for src/lib/utils.ts utility functions.
 */
import { describe, expect, it } from "@jest/globals";
import { userTypeLabel, formatDate, truncate, fullName } from "../src/lib/utils";

describe("userTypeLabel", () => {
  it("returns 'Admin' for user_type 'A'", () => {
    expect(userTypeLabel("A")).toBe("Admin");
  });

  it("returns 'User' for user_type 'U'", () => {
    expect(userTypeLabel("U")).toBe("User");
  });
});

describe("truncate", () => {
  it("returns the string unchanged if within maxLen", () => {
    expect(truncate("hello", 10)).toBe("hello");
  });

  it("truncates and adds ellipsis when over maxLen", () => {
    const result = truncate("abcdefghij", 5);
    expect(result).toHaveLength(5);
    expect(result.endsWith("…")).toBe(true);
  });

  it("returns string unchanged when exactly maxLen", () => {
    expect(truncate("exact", 5)).toBe("exact");
  });
});

describe("fullName", () => {
  it("joins first and last name with a space", () => {
    expect(fullName("Alice", "Smith")).toBe("Alice Smith");
  });

  it("trims extra whitespace", () => {
    expect(fullName("  Bob  ", "  Jones  ")).toBe("Bob    Jones");
  });
});

describe("formatDate", () => {
  it("returns empty string for empty input", () => {
    expect(formatDate("")).toBe("");
  });

  it("returns a non-empty string for a valid ISO date", () => {
    const result = formatDate("2024-06-01T00:00:00Z");
    expect(typeof result).toBe("string");
    expect(result.length).toBeGreaterThan(0);
  });
});
