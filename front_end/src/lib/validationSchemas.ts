/**
 * Zod validation schemas — mirror COACTUPC field validation paragraphs.
 * Used by react-hook-form for client-side validation matching server rules.
 */

import { z } from "zod";

// ---------------------------------------------------------------------------
// Valid US state codes — mirrors COACTUPC 1270-EDIT-US-STATE-CD
// ---------------------------------------------------------------------------
const VALID_US_STATES = new Set([
  "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA",
  "HI","ID","IL","IN","IA","KS","KY","LA","ME","MD",
  "MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
  "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC",
  "SD","TN","TX","UT","VT","VA","WA","WV","WI","WY",
  "DC","PR","VI","GU","AS","MP",
]);

/** 1265-EDIT-US-SSN */
export const ssnSchema = z.object({
  part1: z
    .string()
    .length(3, "Must be 3 digits")
    .regex(/^\d{3}$/, "Digits only")
    .refine((v) => v !== "000", "Area number cannot be 000")
    .refine((v) => v !== "666", "Area number 666 is not valid")
    .refine((v) => {
      const n = parseInt(v, 10);
      return !(n >= 900 && n <= 999);
    }, "Area numbers 900-999 are not valid"),
  part2: z.string().length(2, "Must be 2 digits").regex(/^\d{2}$/, "Digits only"),
  part3: z.string().length(4, "Must be 4 digits").regex(/^\d{4}$/, "Digits only"),
});

/** 1260-EDIT-US-PHONE-NUM */
export const phoneSchema = z.object({
  area_code: z
    .string()
    .length(3, "Must be 3 digits")
    .regex(/^\d{3}$/, "Digits only")
    .refine((v) => {
      const n = parseInt(v, 10);
      return n >= 200 && n <= 999;
    }, "Invalid NANP area code")
    .refine((v) => !(v[1] === "1" && v[2] === "1"), "N11 area codes are not valid"),
  prefix: z.string().length(3, "Must be 3 digits").regex(/^\d{3}$/, "Digits only"),
  line_number: z.string().length(4, "Must be 4 digits").regex(/^\d{4}$/, "Digits only"),
});

/** Account update form schema */
export const accountUpdateSchema = z.object({
  updated_at: z.string().min(1),

  // Account fields
  acct_active_status: z
    .string()
    .transform((v) => v.toUpperCase())
    .refine((v) => v === "Y" || v === "N", {
      message: "Account Active Status must be Y or N",
    }),
  acct_credit_limit: z.coerce
    .number({ invalid_type_error: "Credit Limit must be a number" })
    .multipleOf(0.01),
  acct_cash_credit_limit: z.coerce.number().multipleOf(0.01),
  acct_curr_bal: z.coerce.number().multipleOf(0.01),
  acct_curr_cyc_credit: z.coerce.number().multipleOf(0.01),
  acct_curr_cyc_debit: z.coerce.number().multipleOf(0.01),
  acct_open_date: z.string().nullable().optional(),
  acct_expiration_date: z.string().nullable().optional(),
  acct_reissue_date: z.string().nullable().optional(),
  acct_group_id: z.string().max(10).nullable().optional(),

  // Customer fields
  cust_first_name: z
    .string()
    .min(1, "First name is required")
    .max(25)
    .refine((v) => /^[A-Za-z ]+$/.test(v.trim()), "Name can only contain alphabets and spaces"),
  cust_middle_name: z
    .string()
    .max(25)
    .nullable()
    .optional()
    .refine(
      (v) => !v || /^[A-Za-z ]*$/.test(v.trim()),
      "Name can only contain alphabets and spaces"
    ),
  cust_last_name: z
    .string()
    .min(1, "Last name is required")
    .max(25)
    .refine((v) => /^[A-Za-z ]+$/.test(v.trim()), "Name can only contain alphabets and spaces"),
  cust_addr_line_1: z.string().min(1, "Address is required").max(50),
  cust_addr_line_2: z.string().max(50).nullable().optional(),
  cust_addr_line_3: z.string().max(50).nullable().optional(),
  cust_addr_state_cd: z
    .string()
    .length(2, "State code must be 2 characters")
    .transform((v) => v.toUpperCase())
    .refine((v) => VALID_US_STATES.has(v), "Invalid US state code"),
  cust_addr_country_cd: z.string().min(2).max(3).default("USA"),
  cust_addr_zip: z
    .string()
    .min(1, "ZIP code is required")
    .regex(/^\d{5}(-\d{4})?$/, "ZIP must be 5 digits")
    .refine((v) => v.replace(/\D/g, "").replace(/^0+/, "") !== "", "ZIP cannot be all zeros"),
  cust_phone_num_1: phoneSchema,
  cust_phone_num_2: phoneSchema.nullable().optional(),
  cust_ssn: ssnSchema,
  cust_govt_issued_id: z.string().max(20).nullable().optional(),
  cust_dob: z
    .string()
    .min(1, "Date of birth is required")
    .refine((v) => new Date(v) <= new Date(), "Date of birth cannot be in the future"),
  cust_eft_account_id: z
    .string()
    .min(1, "EFT Account ID is required")
    .max(10)
    .regex(/^\d+$/, "EFT Account ID must be numeric"),
  cust_pri_card_holder_ind: z
    .string()
    .transform((v) => v.toUpperCase())
    .refine((v) => v === "Y" || v === "N", "Must be Y or N"),
  cust_fico_credit_score: z.coerce
    .number()
    .int()
    .min(300, "FICO score must be at least 300")
    .max(850, "FICO score cannot exceed 850"),
});

export type AccountUpdateFormData = z.infer<typeof accountUpdateSchema>;
