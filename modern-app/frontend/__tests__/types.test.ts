/**
 * Tests for type helper functions and decline reason table.
 * Validates the 10-entry COPAUS1C lookup table in the frontend.
 */

import {
  DECLINE_REASON_CODES,
  getAuthStatusLabel,
  getFraudStatusLabel,
  getMatchStatusLabel,
} from "@/types";

describe("DECLINE_REASON_CODES lookup table", () => {
  it("contains exactly 10 codes", () => {
    expect(Object.keys(DECLINE_REASON_CODES)).toHaveLength(10);
  });

  it("code 00 = APPROVED", () => {
    expect(DECLINE_REASON_CODES["00"]).toBe("APPROVED");
  });

  it("code 31 = INVALID CARD", () => {
    expect(DECLINE_REASON_CODES["31"]).toBe("INVALID CARD");
  });

  it("code 41 = INSUFFICIENT FUND", () => {
    expect(DECLINE_REASON_CODES["41"]).toBe("INSUFFICIENT FUND");
  });

  it("code 42 = CARD NOT ACTIVE", () => {
    expect(DECLINE_REASON_CODES["42"]).toBe("CARD NOT ACTIVE");
  });

  it("code 43 = ACCOUNT CLOSED", () => {
    expect(DECLINE_REASON_CODES["43"]).toBe("ACCOUNT CLOSED");
  });

  it("code 44 = EXCEED DAILY LIMIT", () => {
    expect(DECLINE_REASON_CODES["44"]).toBe("EXCEED DAILY LIMIT");
  });

  it("code 51 = CARD FRAUD", () => {
    expect(DECLINE_REASON_CODES["51"]).toBe("CARD FRAUD");
  });

  it("code 52 = MERCHANT FRAUD", () => {
    expect(DECLINE_REASON_CODES["52"]).toBe("MERCHANT FRAUD");
  });

  it("code 53 = LOST CARD", () => {
    expect(DECLINE_REASON_CODES["53"]).toBe("LOST CARD");
  });

  it("code 90 = UNKNOWN", () => {
    expect(DECLINE_REASON_CODES["90"]).toBe("UNKNOWN");
  });
});

describe("getAuthStatusLabel", () => {
  it("A = Active", () => {
    expect(getAuthStatusLabel("A")).toBe("Active");
  });

  it("C = Closed", () => {
    expect(getAuthStatusLabel("C")).toBe("Closed");
  });

  it("I = Inactive", () => {
    expect(getAuthStatusLabel("I")).toBe("Inactive");
  });

  it("unknown status returns status code", () => {
    expect(getAuthStatusLabel("X")).toBe("X");
  });
});

describe("getMatchStatusLabel", () => {
  it("P = Pending", () => {
    expect(getMatchStatusLabel("P")).toBe("Pending");
  });

  it("D = Declined", () => {
    expect(getMatchStatusLabel("D")).toBe("Declined");
  });

  it("E = Expired", () => {
    expect(getMatchStatusLabel("E")).toBe("Expired");
  });

  it("M = Matched", () => {
    expect(getMatchStatusLabel("M")).toBe("Matched");
  });
});

describe("getFraudStatusLabel", () => {
  it("F = Fraud Confirmed", () => {
    expect(getFraudStatusLabel("F")).toBe("Fraud Confirmed");
  });

  it("R = Fraud Removed", () => {
    expect(getFraudStatusLabel("R")).toBe("Fraud Removed");
  });

  it("null = None", () => {
    expect(getFraudStatusLabel(null)).toBe("None");
  });
});
