/**
 * Custom hook encapsulating the COACTUPC state machine logic.
 *
 * States (mapping to ACUP-CHANGE-ACTION):
 *  'idle'        → ACUP-DETAILS-NOT-FETCHED
 *  'show'        → ACUP-SHOW-DETAILS
 *  'editing'     → ACUP-CHANGES-NOT-OK (has edits)
 *  'confirmed'   → ACUP-CHANGES-OK-NOT-CONFIRMED
 *  'done'        → ACUP-CHANGES-OKAYED-AND-DONE
 *  'failed'      → ACUP-CHANGES-OKAYED-BUT-FAILED
 */

"use client";

import { useState, useCallback } from "react";
import { getAccount, updateAccount, extractErrorMessage } from "@/lib/api";
import { parsePhone, parseSsn } from "@/lib/utils";
import type { AccountDetailResponse, AccountUpdateRequest } from "@/types/account";
import type { AccountUpdateFormData } from "@/lib/validationSchemas";

export type UpdateState =
  | "idle"
  | "loading"
  | "show"
  | "editing"
  | "confirming"
  | "saving"
  | "done"
  | "failed";

export interface UseAccountUpdateResult {
  state: UpdateState;
  account: AccountDetailResponse | null;
  defaultValues: Partial<AccountUpdateFormData> | null;
  infoMessage: string;
  errorMessage: string | null;
  fetchAccount: (acctId: string) => Promise<void>;
  requestConfirm: () => void;
  cancelConfirm: () => void;
  submitUpdate: (data: AccountUpdateFormData) => Promise<void>;
  reset: () => void;
}

export function useAccountUpdate(): UseAccountUpdateResult {
  const [state, setState] = useState<UpdateState>("idle");
  const [account, setAccount] = useState<AccountDetailResponse | null>(null);
  const [defaultValues, setDefaultValues] = useState<Partial<AccountUpdateFormData> | null>(null);
  const [infoMessage, setInfoMessage] = useState("Enter or update id of account to update");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // -----------------------------------------------------------------------
  // ACUP-DETAILS-NOT-FETCHED → 9000-READ-ACCT
  // -----------------------------------------------------------------------
  const fetchAccount = useCallback(async (acctId: string) => {
    setState("loading");
    setErrorMessage(null);

    try {
      const data = await getAccount(acctId);
      setAccount(data);

      // Pre-populate form with fetched values (ACUP-OLD-DETAILS snapshot)
      const phone1 = parsePhone(data.customer?.cust_phone_num_1 ?? null);
      const phone2 = parsePhone(data.customer?.cust_phone_num_2 ?? null);
      const ssn = parseSsn(data.customer?.cust_ssn ?? null);

      const defaults: Partial<AccountUpdateFormData> = {
        updated_at: data.updated_at,
        acct_active_status: data.acct_active_status,
        acct_credit_limit: Number(data.acct_credit_limit),
        acct_cash_credit_limit: Number(data.acct_cash_credit_limit),
        acct_curr_bal: Number(data.acct_curr_bal),
        acct_curr_cyc_credit: Number(data.acct_curr_cyc_credit),
        acct_curr_cyc_debit: Number(data.acct_curr_cyc_debit),
        acct_open_date: data.acct_open_date ?? undefined,
        acct_expiration_date: data.acct_expiration_date ?? undefined,
        acct_reissue_date: data.acct_reissue_date ?? undefined,
        acct_group_id: data.acct_group_id ?? undefined,
        cust_first_name: data.customer?.cust_first_name ?? "",
        cust_middle_name: data.customer?.cust_middle_name ?? undefined,
        cust_last_name: data.customer?.cust_last_name ?? "",
        cust_addr_line_1: data.customer?.cust_addr_line_1 ?? "",
        cust_addr_line_2: data.customer?.cust_addr_line_2 ?? undefined,
        cust_addr_line_3: data.customer?.cust_addr_line_3 ?? undefined,
        cust_addr_state_cd: data.customer?.cust_addr_state_cd ?? "",
        cust_addr_country_cd: data.customer?.cust_addr_country_cd ?? "USA",
        cust_addr_zip: data.customer?.cust_addr_zip ?? "",
        cust_phone_num_1: phone1 ?? { area_code: "", prefix: "", line_number: "" },
        cust_phone_num_2: phone2 ?? undefined,
        cust_ssn: ssn ?? { part1: "", part2: "", part3: "" },
        cust_govt_issued_id: data.customer?.cust_govt_issued_id ?? undefined,
        cust_dob: data.customer?.cust_dob ?? "",
        cust_eft_account_id: data.customer?.cust_eft_account_id ?? "",
        cust_pri_card_holder_ind: (data.customer?.cust_pri_card_holder_ind ?? "Y") as "Y" | "N",
        cust_fico_credit_score: data.customer?.cust_fico_credit_score ?? 0,
      };

      setDefaultValues(defaults);
      setState("show");
      setInfoMessage("Update account details presented above.");
    } catch (err) {
      setErrorMessage(extractErrorMessage(err));
      setState("idle");
    }
  }, []);

  // -----------------------------------------------------------------------
  // ACUP-CHANGES-OK-NOT-CONFIRMED: user clicked "Review & Save"
  // -----------------------------------------------------------------------
  const requestConfirm = useCallback(() => {
    setState("confirming");
    setInfoMessage("Changes validated. Press F5 to save");
  }, []);

  const cancelConfirm = useCallback(() => {
    setState("show");
    setInfoMessage("Update account details presented above.");
  }, []);

  // -----------------------------------------------------------------------
  // ACUP-CHANGES-OKAYED-AND-DONE / ACUP-CHANGES-OKAYED-BUT-FAILED
  // Equivalent to F5=Save → 9600-WRITE-PROCESSING
  // -----------------------------------------------------------------------
  const submitUpdate = useCallback(
    async (formData: AccountUpdateFormData) => {
      if (!account) return;
      setState("saving");

      const payload: AccountUpdateRequest = {
        ...formData,
        acct_active_status: formData.acct_active_status as "Y" | "N",
        cust_pri_card_holder_ind: formData.cust_pri_card_holder_ind as "Y" | "N",
      };

      try {
        await updateAccount(account.acct_id, payload);
        setState("done");
        setInfoMessage("Changes committed to database");
        setErrorMessage(null);
      } catch (err) {
        const msg = extractErrorMessage(err);
        setErrorMessage(msg);
        setState("failed");
        setInfoMessage("Changes unsuccessful. Please try again");
      }
    },
    [account]
  );

  const reset = useCallback(() => {
    setState("idle");
    setAccount(null);
    setDefaultValues(null);
    setInfoMessage("Enter or update id of account to update");
    setErrorMessage(null);
  }, []);

  return {
    state,
    account,
    defaultValues,
    infoMessage,
    errorMessage,
    fetchAccount,
    requestConfirm,
    cancelConfirm,
    submitUpdate,
    reset,
  };
}
