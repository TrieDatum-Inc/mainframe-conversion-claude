/**
 * Frontend validation schema tests.
 * Mirrors COACTUPC field validation paragraphs — ensures client-side
 * rules match the server-side Pydantic validators exactly.
 */

import { accountUpdateSchema, ssnSchema, phoneSchema } from "@/lib/validationSchemas";

function basePayload(overrides: Record<string, unknown> = {}) {
  return {
    updated_at: "2024-01-01T12:00:00",
    acct_active_status: "Y",
    acct_credit_limit: 10000,
    acct_cash_credit_limit: 2000,
    acct_curr_bal: 1250.75,
    acct_curr_cyc_credit: 500,
    acct_curr_cyc_debit: 1750.75,
    acct_open_date: "2020-01-15",
    acct_expiration_date: "2026-01-31",
    acct_reissue_date: "2024-01-31",
    acct_group_id: "PREMIUM",
    cust_first_name: "James",
    cust_middle_name: "Earl",
    cust_last_name: "Carter",
    cust_addr_line_1: "1600 Pennsylvania Ave NW",
    cust_addr_state_cd: "DC",
    cust_addr_country_cd: "USA",
    cust_addr_zip: "20500",
    cust_phone_num_1: { area_code: "202", prefix: "456", line_number: "1111" },
    cust_ssn: { part1: "123", part2: "45", part3: "6789" },
    cust_dob: "1960-03-15",
    cust_eft_account_id: "1234567890",
    cust_pri_card_holder_ind: "Y",
    cust_fico_credit_score: 780,
    ...overrides,
  };
}

describe("SSN Validation (1265-EDIT-US-SSN)", () => {
  it("accepts valid SSN", () => {
    const result = ssnSchema.safeParse({ part1: "123", part2: "45", part3: "6789" });
    expect(result.success).toBe(true);
  });

  it("rejects part1 of 000", () => {
    const result = ssnSchema.safeParse({ part1: "000", part2: "45", part3: "6789" });
    expect(result.success).toBe(false);
    expect(result.error?.issues[0].message).toContain("000");
  });

  it("rejects part1 of 666", () => {
    const result = ssnSchema.safeParse({ part1: "666", part2: "45", part3: "6789" });
    expect(result.success).toBe(false);
    expect(result.error?.issues[0].message).toContain("666");
  });

  it("rejects part1 in range 900-999", () => {
    const result = ssnSchema.safeParse({ part1: "950", part2: "45", part3: "6789" });
    expect(result.success).toBe(false);
  });

  it("rejects non-numeric part1", () => {
    const result = ssnSchema.safeParse({ part1: "abc", part2: "45", part3: "6789" });
    expect(result.success).toBe(false);
  });
});

describe("Phone Validation (1260-EDIT-US-PHONE-NUM)", () => {
  it("accepts valid NANP number", () => {
    const result = phoneSchema.safeParse({
      area_code: "202",
      prefix: "456",
      line_number: "1111",
    });
    expect(result.success).toBe(true);
  });

  it("rejects area code below 200", () => {
    const result = phoneSchema.safeParse({
      area_code: "100",
      prefix: "456",
      line_number: "1111",
    });
    expect(result.success).toBe(false);
  });

  it("rejects N11 area code", () => {
    const result = phoneSchema.safeParse({
      area_code: "211",
      prefix: "456",
      line_number: "1111",
    });
    expect(result.success).toBe(false);
    expect(result.error?.issues[0].message).toContain("N11");
  });
});

describe("FICO Score Validation (1275-EDIT-FICO-SCORE)", () => {
  it("accepts 300", () => {
    const r = accountUpdateSchema.safeParse(basePayload({ cust_fico_credit_score: 300 }));
    expect(r.success).toBe(true);
  });

  it("accepts 850", () => {
    const r = accountUpdateSchema.safeParse(basePayload({ cust_fico_credit_score: 850 }));
    expect(r.success).toBe(true);
  });

  it("rejects 299", () => {
    const r = accountUpdateSchema.safeParse(basePayload({ cust_fico_credit_score: 299 }));
    expect(r.success).toBe(false);
  });

  it("rejects 851", () => {
    const r = accountUpdateSchema.safeParse(basePayload({ cust_fico_credit_score: 851 }));
    expect(r.success).toBe(false);
  });
});

describe("Name Validation (1225-EDIT-ALPHA-REQD)", () => {
  it("accepts alphabets and spaces", () => {
    const r = accountUpdateSchema.safeParse(
      basePayload({ cust_first_name: "Mary Ann" })
    );
    expect(r.success).toBe(true);
  });

  it("rejects name with digits", () => {
    const r = accountUpdateSchema.safeParse(
      basePayload({ cust_first_name: "Mary1" })
    );
    expect(r.success).toBe(false);
  });

  it("rejects blank first name", () => {
    const r = accountUpdateSchema.safeParse(
      basePayload({ cust_first_name: "   " })
    );
    expect(r.success).toBe(false);
  });
});

describe("US State Code Validation (1270-EDIT-US-STATE-CD)", () => {
  it("accepts valid state NY", () => {
    const r = accountUpdateSchema.safeParse(
      basePayload({ cust_addr_state_cd: "NY" })
    );
    expect(r.success).toBe(true);
  });

  it("accepts DC", () => {
    const r = accountUpdateSchema.safeParse(
      basePayload({ cust_addr_state_cd: "DC" })
    );
    expect(r.success).toBe(true);
  });

  it("rejects ZZ", () => {
    const r = accountUpdateSchema.safeParse(
      basePayload({ cust_addr_state_cd: "ZZ" })
    );
    expect(r.success).toBe(false);
  });
});

describe("Account Active Status (1220-EDIT-YESNO)", () => {
  it("accepts Y", () => {
    const r = accountUpdateSchema.safeParse(
      basePayload({ acct_active_status: "Y" })
    );
    expect(r.success).toBe(true);
  });

  it("accepts N", () => {
    const r = accountUpdateSchema.safeParse(
      basePayload({ acct_active_status: "N" })
    );
    expect(r.success).toBe(true);
  });

  it("rejects X", () => {
    const r = accountUpdateSchema.safeParse(
      basePayload({ acct_active_status: "X" })
    );
    expect(r.success).toBe(false);
  });
});

describe("Date of Birth Validation (EDIT-DATE-OF-BIRTH)", () => {
  it("accepts past date", () => {
    const r = accountUpdateSchema.safeParse(
      basePayload({ cust_dob: "1990-01-01" })
    );
    expect(r.success).toBe(true);
  });

  it("rejects future date", () => {
    const future = new Date();
    future.setFullYear(future.getFullYear() + 1);
    const r = accountUpdateSchema.safeParse(
      basePayload({ cust_dob: future.toISOString().split("T")[0] })
    );
    expect(r.success).toBe(false);
  });
});

describe("ZIP Code Validation (1245-EDIT-NUM-REQD)", () => {
  it("accepts 5-digit ZIP", () => {
    const r = accountUpdateSchema.safeParse(
      basePayload({ cust_addr_zip: "10012" })
    );
    expect(r.success).toBe(true);
  });

  it("rejects non-numeric ZIP", () => {
    const r = accountUpdateSchema.safeParse(
      basePayload({ cust_addr_zip: "ABCDE" })
    );
    expect(r.success).toBe(false);
  });

  it("rejects all-zeros ZIP", () => {
    const r = accountUpdateSchema.safeParse(
      basePayload({ cust_addr_zip: "00000" })
    );
    expect(r.success).toBe(false);
  });
});
