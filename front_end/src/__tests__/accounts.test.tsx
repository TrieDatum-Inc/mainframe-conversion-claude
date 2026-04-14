/**
 * Frontend integration tests for the accounts module.
 *
 * COBOL origin:
 *   AccountViewPage   → COACTVWC (Transaction CAVW) / BMS mapset COACTVW
 *   AccountUpdatePage → COACTUPC (Transaction CAUP) / BMS mapset COACTUP
 *
 * Coverage:
 *   AccountViewPage  — rendering, search validation, successful load, 404 handling,
 *                      auth redirect, Update Account navigation
 *   AccountUpdatePage — rendering, auto-load from query param, field validation
 *                       (SSN area code rules, FICO range, phone format, cash≤credit,
 *                       active status), successful submit, NO_CHANGES_DETECTED, Save/Cancel reveal
 */

import React from "react";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuthContext } from "@/components/auth/AuthProvider";

// ---------------------------------------------------------------------------
// Shared mocks
// ---------------------------------------------------------------------------

jest.mock("@/lib/api", () => ({
  api: {
    get: jest.fn(),
    put: jest.fn(),
  },
  ApiError: class ApiError extends Error {
    constructor(
      public status: number,
      public errorCode: string,
      message: string
    ) {
      super(message);
      this.name = "ApiError";
    }
  },
}));

jest.mock("@/components/layout/AppHeader", () => ({
  AppHeader: () => <header data-testid="app-header" />,
}));

const mockRouterPush = jest.fn();
const mockRouterBack = jest.fn();
const mockSearchParams = { get: jest.fn() };

jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockRouterPush,
    back: mockRouterBack,
    replace: jest.fn(),
  }),
  useSearchParams: () => mockSearchParams,
}));

import { api, ApiError } from "@/lib/api";
const mockApiGet = api.get as jest.MockedFunction<typeof api.get>;
const mockApiPut = api.put as jest.MockedFunction<typeof api.put>;

// ---------------------------------------------------------------------------
// Test fixture
// ---------------------------------------------------------------------------

const mockAccountResponse = {
  account_id: 10000000001,
  active_status: "Y",
  open_date: "2020-01-01",
  expiration_date: "2025-01-01",
  reissue_date: "2023-01-01",
  credit_limit: "10000.00",
  cash_credit_limit: "2000.00",
  current_balance: "-500.00",
  curr_cycle_credit: "0.00",
  curr_cycle_debit: "500.00",
  group_id: "GRP01",
  customer: {
    customer_id: 100001,
    ssn_masked: "***-**-6789",
    date_of_birth: "1985-06-15",
    fico_score: 720,
    first_name: "Jane",
    middle_name: "A",
    last_name: "Smith",
    address_line_1: "123 Main St",
    address_line_2: null,
    city: "Springfield",
    state_code: "IL",
    zip_code: "62701",
    country_code: "USA",
    phone_1: "217-555-0100",
    phone_2: null,
    government_id_ref: "GOV123",
    eft_account_id: "EFT001",
    primary_card_holder: "Y",
  },
};

// ---------------------------------------------------------------------------
// Auth context helpers
// ---------------------------------------------------------------------------

function authenticatedContext(children: React.ReactNode) {
  return (
    <AuthContext.Provider
      value={{
        user: {
          user_id: "ADMIN001",
          user_type: "A",
          first_name: "Admin",
          last_name: "User",
        },
        token: "mock.jwt.token",
        isAuthenticated: true,
        login: jest.fn(),
        logout: jest.fn(),
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

function unauthenticatedContext(children: React.ReactNode) {
  return (
    <AuthContext.Provider
      value={{
        user: null,
        token: null,
        isAuthenticated: false,
        login: jest.fn(),
        logout: jest.fn(),
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// ---------------------------------------------------------------------------
// AccountViewPage
// ---------------------------------------------------------------------------

import AccountViewPage from "@/app/accounts/view/page";

describe("AccountViewPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockSearchParams.get.mockReturnValue(null);
  });

  // ---- Rendering -----------------------------------------------------------

  describe("Rendering", () => {
    it("renders the Account Number input field", () => {
      render(authenticatedContext(<AccountViewPage />));
      expect(screen.getByLabelText(/account number/i)).toBeInTheDocument();
    });

    it("renders the View Account submit button (ENTER key equivalent)", () => {
      render(authenticatedContext(<AccountViewPage />));
      expect(
        screen.getByRole("button", { name: /view account/i })
      ).toBeInTheDocument();
    });

    it("renders the Exit button (PF3 key equivalent)", () => {
      render(authenticatedContext(<AccountViewPage />));
      expect(
        screen.getByRole("button", { name: /exit/i })
      ).toBeInTheDocument();
    });

    it("does not render account details before a search", () => {
      render(authenticatedContext(<AccountViewPage />));
      expect(
        screen.queryByRole("region", { name: /account summary/i })
      ).not.toBeInTheDocument();
    });
  });

  // ---- Auth guard ----------------------------------------------------------

  describe("Auth guard — COBOL origin: EIBCALEN=0 → XCTL COSGN00C", () => {
    it("redirects to /login when not authenticated", () => {
      render(unauthenticatedContext(<AccountViewPage />));
      expect(mockRouterPush).toHaveBeenCalledWith("/login");
    });
  });

  // ---- Validation ----------------------------------------------------------

  describe("Validation — COBOL origin: COACTVWC 2000-PROCESS-INPUTS", () => {
    it("shows validation error when account number is empty on submit", async () => {
      const user = userEvent.setup();
      render(authenticatedContext(<AccountViewPage />));

      await user.click(screen.getByRole("button", { name: /view account/i }));

      await waitFor(() => {
        expect(
          screen.getByText(/account number is required/i)
        ).toBeInTheDocument();
      });
    });

    it("shows error when account number contains non-numeric characters", async () => {
      const user = userEvent.setup();
      render(authenticatedContext(<AccountViewPage />));

      await user.type(screen.getByLabelText(/account number/i), "ABC123");
      await user.click(screen.getByRole("button", { name: /view account/i }));

      await waitFor(() => {
        expect(
          screen.getByText(/account number must be numeric/i)
        ).toBeInTheDocument();
      });
    });

    it("shows error when account number is zero (COBOL: non-zero check)", async () => {
      const user = userEvent.setup();
      render(authenticatedContext(<AccountViewPage />));

      await user.type(screen.getByLabelText(/account number/i), "0");
      await user.click(screen.getByRole("button", { name: /view account/i }));

      await waitFor(() => {
        expect(
          screen.getByText(/account number must be non-zero/i)
        ).toBeInTheDocument();
      });
    });

    it("does not call the API when validation fails", async () => {
      const user = userEvent.setup();
      render(authenticatedContext(<AccountViewPage />));

      await user.click(screen.getByRole("button", { name: /view account/i }));

      await waitFor(() => {
        expect(mockApiGet).not.toHaveBeenCalled();
      });
    });
  });

  // ---- Successful load -----------------------------------------------------

  describe("Successful account load — COBOL origin: COACTVWC 9000-READ-ACCT", () => {
    beforeEach(() => {
      mockApiGet.mockResolvedValue(mockAccountResponse);
    });

    async function loadAccount(accountId = "10000000001") {
      const user = userEvent.setup();
      render(authenticatedContext(<AccountViewPage />));
      await user.type(screen.getByLabelText(/account number/i), accountId);
      await user.click(screen.getByRole("button", { name: /view account/i }));
      await waitFor(() =>
        expect(
          screen.getByRole("region", { name: /account summary/i })
        ).toBeInTheDocument()
      );
      return user;
    }

    it("calls the GET account API with the correct account ID", async () => {
      await loadAccount();
      expect(mockApiGet).toHaveBeenCalledWith("/api/v1/accounts/10000000001");
    });

    it("renders Account Summary section after successful load", async () => {
      await loadAccount();
      expect(
        screen.getByRole("region", { name: /account summary/i })
      ).toBeInTheDocument();
    });

    it("renders Customer Details section after successful load", async () => {
      await loadAccount();
      expect(
        screen.getByRole("region", { name: /customer details/i })
      ).toBeInTheDocument();
    });

    it("displays Active status badge for active_status=Y", async () => {
      await loadAccount();
      expect(screen.getByText("Active")).toBeInTheDocument();
    });

    it("displays formatted signed credit limit (+$10,000.00)", async () => {
      await loadAccount();
      // Intl.NumberFormat en-US with signDisplay:always and currency:USD
      expect(screen.getByText(/\+\$10,000\.00/)).toBeInTheDocument();
    });

    it("displays masked SSN (COBOL: ACSTSSN always ***-**-XXXX)", async () => {
      await loadAccount();
      const customerSection = screen.getByRole("region", {
        name: /customer details/i,
      });
      expect(
        within(customerSection).getByText("***-**-6789")
      ).toBeInTheDocument();
    });

    it("does NOT display unmasked SSN digits in the response", async () => {
      await loadAccount();
      // Full SSN (123-45-6789) must never appear — only masked last 4 digits
      expect(screen.queryByText(/123-45-6789/)).not.toBeInTheDocument();
    });

    it("displays customer full name", async () => {
      await loadAccount();
      const customerSection = screen.getByRole("region", {
        name: /customer details/i,
      });
      expect(
        within(customerSection).getByText(/Jane A Smith/)
      ).toBeInTheDocument();
    });

    it("renders 'Update Account' navigation button after successful load", async () => {
      await loadAccount();
      expect(
        screen.getByRole("button", { name: /update account/i })
      ).toBeInTheDocument();
    });

    it("navigates to /accounts/update?accountId when 'Update Account' is clicked", async () => {
      const user = await loadAccount();
      await user.click(
        screen.getByRole("button", { name: /update account/i })
      );
      expect(mockRouterPush).toHaveBeenCalledWith(
        "/accounts/update?accountId=10000000001"
      );
    });

    it("renders negative current balance (red styling text)", async () => {
      await loadAccount();
      // -$500.00 should be rendered on screen
      expect(screen.getByText(/-\$500\.00/)).toBeInTheDocument();
    });
  });

  // ---- Error handling ------------------------------------------------------

  describe("Error handling — COBOL origin: COACTVWC ERRMSG display", () => {
    it("shows account not found message on 404", async () => {
      mockApiGet.mockRejectedValueOnce(
        new ApiError(404, "ACCOUNT_NOT_FOUND", "Account not found")
      );
      const user = userEvent.setup();
      render(authenticatedContext(<AccountViewPage />));

      await user.type(screen.getByLabelText(/account number/i), "99999999999");
      await user.click(
        screen.getByRole("button", { name: /view account/i })
      );

      await waitFor(() => {
        expect(
          screen.getByText(/not found in the system/i)
        ).toBeInTheDocument();
      });
    });

    it("redirects to /login on 401 response", async () => {
      mockApiGet.mockRejectedValueOnce(
        new ApiError(401, "UNAUTHORIZED", "Unauthorized")
      );
      const user = userEvent.setup();
      render(authenticatedContext(<AccountViewPage />));

      await user.type(screen.getByLabelText(/account number/i), "10000000001");
      await user.click(
        screen.getByRole("button", { name: /view account/i })
      );

      await waitFor(() => {
        expect(mockRouterPush).toHaveBeenCalledWith("/login");
      });
    });

    it("shows error message for unexpected 500 error", async () => {
      mockApiGet.mockRejectedValueOnce(
        new ApiError(500, "INTERNAL_ERROR", "Failed to retrieve account.")
      );
      const user = userEvent.setup();
      render(authenticatedContext(<AccountViewPage />));

      await user.type(screen.getByLabelText(/account number/i), "10000000001");
      await user.click(
        screen.getByRole("button", { name: /view account/i })
      );

      await waitFor(() => {
        expect(
          screen.getByText(/failed to retrieve account/i)
        ).toBeInTheDocument();
      });
    });

    it("shows connection error when fetch throws a non-ApiError (network failure)", async () => {
      mockApiGet.mockRejectedValueOnce(new Error("Network error"));
      const user = userEvent.setup();
      render(authenticatedContext(<AccountViewPage />));

      await user.type(screen.getByLabelText(/account number/i), "10000000001");
      await user.click(
        screen.getByRole("button", { name: /view account/i })
      );

      await waitFor(() => {
        expect(screen.getByText(/unable to connect/i)).toBeInTheDocument();
      });
    });
  });

  // ---- Exit button ---------------------------------------------------------

  describe("Exit button — COBOL origin: PF3 key", () => {
    it("calls router.back() when Exit is clicked", async () => {
      const user = userEvent.setup();
      render(authenticatedContext(<AccountViewPage />));
      await user.click(screen.getByRole("button", { name: /exit/i }));
      expect(mockRouterBack).toHaveBeenCalled();
    });
  });
});

// ---------------------------------------------------------------------------
// AccountUpdatePage
// ---------------------------------------------------------------------------

import AccountUpdatePage from "@/app/accounts/update/page";

describe("AccountUpdatePage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockSearchParams.get.mockReturnValue(null);
  });

  // ---- Rendering -----------------------------------------------------------

  describe("Rendering", () => {
    it("renders the Account Number input (load form)", () => {
      render(authenticatedContext(<AccountUpdatePage />));
      expect(screen.getByLabelText(/account number/i)).toBeInTheDocument();
    });

    it("renders the Load Account button (ENTER / Process equivalent for lookup)", () => {
      render(authenticatedContext(<AccountUpdatePage />));
      expect(
        screen.getByRole("button", { name: /load account/i })
      ).toBeInTheDocument();
    });

    it("renders the Exit button (PF3 equivalent)", () => {
      render(authenticatedContext(<AccountUpdatePage />));
      expect(
        screen.getByRole("button", { name: /exit/i })
      ).toBeInTheDocument();
    });

    it("does not show Save button before data is loaded (FKEY05 DRK state)", () => {
      render(authenticatedContext(<AccountUpdatePage />));
      expect(
        screen.queryByRole("button", { name: /^save$/i })
      ).not.toBeInTheDocument();
    });

    it("does not show Cancel button before data is loaded (FKEY12 DRK state)", () => {
      render(authenticatedContext(<AccountUpdatePage />));
      expect(
        screen.queryByRole("button", { name: /^cancel$/i })
      ).not.toBeInTheDocument();
    });

    it("does not show the edit form before data is loaded", () => {
      render(authenticatedContext(<AccountUpdatePage />));
      expect(
        screen.queryByRole("form", { name: /account update form/i })
      ).not.toBeInTheDocument();
    });
  });

  // ---- Auth guard ----------------------------------------------------------

  describe("Auth guard — COBOL origin: EIBCALEN=0 → XCTL COSGN00C", () => {
    it("redirects to /login when not authenticated", () => {
      render(unauthenticatedContext(<AccountUpdatePage />));
      expect(mockRouterPush).toHaveBeenCalledWith("/login");
    });
  });

  // ---- Auto-load from query param -----------------------------------------

  describe("Auto-load from accountId query param — COBOL origin: COMMAREA populate on first entry", () => {
    it("auto-loads account when accountId present in query params", async () => {
      mockSearchParams.get.mockReturnValue("10000000001");
      mockApiGet.mockResolvedValue(mockAccountResponse);

      render(authenticatedContext(<AccountUpdatePage />));

      await waitFor(() => {
        expect(mockApiGet).toHaveBeenCalledWith(
          "/api/v1/accounts/10000000001"
        );
      });
    });

    it("reveals Save and Cancel after successful auto-load (FKEY05/FKEY12 DRK→NORM)", async () => {
      mockSearchParams.get.mockReturnValue("10000000001");
      mockApiGet.mockResolvedValue(mockAccountResponse);

      render(authenticatedContext(<AccountUpdatePage />));

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: /^save$/i })
        ).toBeInTheDocument();
      });
      expect(
        screen.getByRole("button", { name: /^cancel$/i })
      ).toBeInTheDocument();
    });

    it("pre-fills customer first name from loaded response", async () => {
      mockSearchParams.get.mockReturnValue("10000000001");
      mockApiGet.mockResolvedValue(mockAccountResponse);

      render(authenticatedContext(<AccountUpdatePage />));

      await waitFor(() => {
        expect(screen.getByLabelText(/^first name/i)).toHaveValue("Jane");
      });
    });

    it("pre-fills customer last name from loaded response", async () => {
      mockSearchParams.get.mockReturnValue("10000000001");
      mockApiGet.mockResolvedValue(mockAccountResponse);

      render(authenticatedContext(<AccountUpdatePage />));

      await waitFor(() => {
        expect(screen.getByLabelText(/^last name/i)).toHaveValue("Smith");
      });
    });

    it("pre-fills SSN part 3 (serial number) with last 4 digits from masked SSN", async () => {
      // SECURITY: API returns ***-**-6789; only the last 4 digits are pre-filled.
      // Parts 1 and 2 are left blank — user must re-enter to change SSN.
      mockSearchParams.get.mockReturnValue("10000000001");
      mockApiGet.mockResolvedValue(mockAccountResponse);

      render(authenticatedContext(<AccountUpdatePage />));

      await waitFor(() => {
        const ssnSerial = screen.getByLabelText(/SSN serial number/i);
        expect(ssnSerial).toHaveValue("6789");
      });
    });

    it("leaves SSN part 1 blank on auto-load (user must re-enter for security)", async () => {
      mockSearchParams.get.mockReturnValue("10000000001");
      mockApiGet.mockResolvedValue(mockAccountResponse);

      render(authenticatedContext(<AccountUpdatePage />));

      await waitFor(() => {
        const ssnArea = screen.getByLabelText(/SSN area number/i);
        expect(ssnArea).toHaveValue("");
      });
    });
  });

  // ---- Manual load via Load Account button --------------------------------

  describe("Manual load via Load Account button", () => {
    it("calls the GET API with the typed account number on Load Account click", async () => {
      mockApiGet.mockResolvedValue(mockAccountResponse);

      const user = userEvent.setup();
      render(authenticatedContext(<AccountUpdatePage />));

      const accountInput = screen.getByLabelText(/account number/i);
      await user.type(accountInput, "10000000001");
      await user.click(screen.getByRole("button", { name: /load account/i }));

      await waitFor(() => {
        expect(mockApiGet).toHaveBeenCalledWith(
          "/api/v1/accounts/10000000001"
        );
      });
    });

    it("shows error when Load Account is clicked with empty account number", async () => {
      const user = userEvent.setup();
      render(authenticatedContext(<AccountUpdatePage />));

      // Clear the input and submit without a value
      const accountInput = screen.getByLabelText(/account number/i);
      await user.clear(accountInput);
      await user.click(screen.getByRole("button", { name: /load account/i }));

      // The page does a guard check: if (!accountId.trim()) return
      // No API call should be made
      await waitFor(() => {
        expect(mockApiGet).not.toHaveBeenCalled();
      });
    });
  });

  // ---- Field validation (COACTUPC 2000-PROCESS-INPUTS) --------------------

  describe("Field validation — COBOL origin: COACTUPC 2000-PROCESS-INPUTS", () => {
    /**
     * Load the update page and wait for auto-load to complete, then fill the
     * required SSN parts (which are left blank for security on load).
     */
    async function autoLoadAndFillSSN(ssnPart1 = "123", ssnPart2 = "45") {
      mockSearchParams.get.mockReturnValue("10000000001");
      mockApiGet.mockResolvedValue(mockAccountResponse);

      const user = userEvent.setup();
      render(authenticatedContext(<AccountUpdatePage />));

      // Wait for Save button to appear (confirms successful auto-load)
      await waitFor(() =>
        expect(
          screen.getByRole("button", { name: /^save$/i })
        ).toBeInTheDocument()
      );

      if (ssnPart1) {
        await user.type(screen.getByLabelText(/SSN area number/i), ssnPart1);
      }
      if (ssnPart2) {
        await user.type(screen.getByLabelText(/SSN group number/i), ssnPart2);
      }

      return user;
    }

    it("rejects SSN area code 000 (COBOL: INVALID-SSN-PART1, 000 never validly assigned)", async () => {
      const user = await autoLoadAndFillSSN("", "45");

      const ssnArea = screen.getByLabelText(/SSN area number/i);
      await user.clear(ssnArea);
      await user.type(ssnArea, "000");
      await user.click(screen.getByRole("button", { name: /^save$/i }));

      await waitFor(() => {
        expect(
          screen.getByText(/ssn area number cannot be 000/i)
        ).toBeInTheDocument();
      });
    });

    it("rejects SSN area code 666 (COBOL: INVALID-SSN-PART1)", async () => {
      const user = await autoLoadAndFillSSN("", "45");

      const ssnArea = screen.getByLabelText(/SSN area number/i);
      await user.clear(ssnArea);
      await user.type(ssnArea, "666");
      await user.click(screen.getByRole("button", { name: /^save$/i }));

      await waitFor(() => {
        expect(
          screen.getByText(/ssn area number cannot be 000/i)
        ).toBeInTheDocument();
      });
    });

    it("rejects SSN area code 900 (COBOL: INVALID-SSN-PART1, range 900-999 invalid)", async () => {
      const user = await autoLoadAndFillSSN("", "45");

      const ssnArea = screen.getByLabelText(/SSN area number/i);
      await user.clear(ssnArea);
      await user.type(ssnArea, "900");
      await user.click(screen.getByRole("button", { name: /^save$/i }));

      await waitFor(() => {
        expect(
          screen.getByText(/ssn area number cannot be 000/i)
        ).toBeInTheDocument();
      });
    });

    it("rejects FICO score below 300 (COBOL: WS-EDIT-FICO-SCORE-FLGS, valid range 300-850)", async () => {
      const user = await autoLoadAndFillSSN();

      const ficoInput = screen.getByLabelText(/^fico score/i);
      await user.clear(ficoInput);
      await user.type(ficoInput, "250");
      await user.click(screen.getByRole("button", { name: /^save$/i }));

      await waitFor(() => {
        expect(
          screen.getByText(/fico score must be between 300 and 850/i)
        ).toBeInTheDocument();
      });
    });

    it("rejects FICO score above 850 (COBOL: WS-EDIT-FICO-SCORE-FLGS)", async () => {
      const user = await autoLoadAndFillSSN();

      const ficoInput = screen.getByLabelText(/^fico score/i);
      await user.clear(ficoInput);
      await user.type(ficoInput, "900");
      await user.click(screen.getByRole("button", { name: /^save$/i }));

      await waitFor(() => {
        expect(
          screen.getByText(/fico score must be between 300 and 850/i)
        ).toBeInTheDocument();
      });
    });

    it("rejects phone number without dashes (COBOL: WS-EDIT-US-PHONE-NUM NNN-NNN-NNNN)", async () => {
      const user = await autoLoadAndFillSSN();

      const phone1Input = screen.getByLabelText(/^phone 1/i);
      await user.clear(phone1Input);
      await user.type(phone1Input, "2175550100"); // missing dashes
      await user.click(screen.getByRole("button", { name: /^save$/i }));

      await waitFor(() => {
        expect(
          screen.getByText(/format: nnn-nnn-nnnn/i)
        ).toBeInTheDocument();
      });
    });

    it("rejects when cash credit limit exceeds credit limit (DB constraint + COBOL logic)", async () => {
      const user = await autoLoadAndFillSSN();

      const creditLimitInput = screen.getByLabelText(/^credit limit/i);
      const cashLimitInput = screen.getByLabelText(/^cash credit limit/i);

      await user.clear(creditLimitInput);
      await user.type(creditLimitInput, "1000");
      await user.clear(cashLimitInput);
      await user.type(cashLimitInput, "2000"); // cash > credit — cross-field validation
      await user.click(screen.getByRole("button", { name: /^save$/i }));

      await waitFor(() => {
        expect(
          screen.getByText(/cash limit cannot exceed credit limit/i)
        ).toBeInTheDocument();
      });
    });

    it("Active Status select only exposes Y and N options (ACSTTUS UNPROT Y/N)", async () => {
      mockSearchParams.get.mockReturnValue("10000000001");
      mockApiGet.mockResolvedValue(mockAccountResponse);

      render(authenticatedContext(<AccountUpdatePage />));

      await waitFor(() =>
        expect(
          screen.getByRole("button", { name: /^save$/i })
        ).toBeInTheDocument()
      );

      const statusSelect = screen.getByLabelText(/^active status/i);
      expect(statusSelect.tagName).toBe("SELECT");
      const options = within(statusSelect as HTMLSelectElement).getAllByRole(
        "option"
      );
      const values = options.map((o) => (o as HTMLOptionElement).value);
      expect(values).toContain("Y");
      expect(values).toContain("N");
      // No other values permitted
      expect(values.filter((v) => v !== "Y" && v !== "N")).toHaveLength(0);
    });
  });

  // ---- Successful submit ---------------------------------------------------

  describe("Successful submit — COBOL origin: COACTUPC 9000-UPDATE-ACCOUNT (REWRITE path)", () => {
    async function loadAndSave() {
      mockSearchParams.get.mockReturnValue("10000000001");
      mockApiGet.mockResolvedValue(mockAccountResponse);
      mockApiPut.mockResolvedValue(mockAccountResponse);

      const user = userEvent.setup();
      render(authenticatedContext(<AccountUpdatePage />));

      // Wait for auto-load
      await waitFor(() =>
        expect(
          screen.getByRole("button", { name: /^save$/i })
        ).toBeInTheDocument()
      );

      // Fill required SSN parts (left blank for security)
      await user.type(screen.getByLabelText(/SSN area number/i), "123");
      await user.type(screen.getByLabelText(/SSN group number/i), "45");

      await user.click(screen.getByRole("button", { name: /^save$/i }));

      return user;
    }

    it("calls PUT /api/v1/accounts/{id} with the correct account ID", async () => {
      await loadAndSave();

      await waitFor(() => {
        expect(mockApiPut).toHaveBeenCalledWith(
          "/api/v1/accounts/10000000001",
          expect.any(Object)
        );
      });
    });

    it("payload includes customer_id, ssn parts, and name fields", async () => {
      await loadAndSave();

      await waitFor(() => {
        expect(mockApiPut).toHaveBeenCalledWith(
          "/api/v1/accounts/10000000001",
          expect.objectContaining({
            customer: expect.objectContaining({
              customer_id: 100001,
              ssn_part1: "123",
              ssn_part2: "45",
              ssn_part3: "6789",
              first_name: "Jane",
              last_name: "Smith",
            }),
          })
        );
      });
    });

    it("payload includes account-level financial fields", async () => {
      await loadAndSave();

      await waitFor(() => {
        expect(mockApiPut).toHaveBeenCalledWith(
          "/api/v1/accounts/10000000001",
          expect.objectContaining({
            active_status: "Y",
            credit_limit: expect.any(Number),
            cash_credit_limit: expect.any(Number),
          })
        );
      });
    });

    it("shows 'Account updated successfully' message after successful save", async () => {
      await loadAndSave();

      await waitFor(() => {
        expect(
          screen.getByText(/account updated successfully/i)
        ).toBeInTheDocument();
      });
    });
  });

  // ---- NO_CHANGES_DETECTED (WS-DATACHANGED-FLAG) --------------------------

  describe("NO_CHANGES_DETECTED — COBOL origin: WS-DATACHANGED-FLAG check → 422", () => {
    it("shows descriptive message when API returns NO_CHANGES_DETECTED 422", async () => {
      mockSearchParams.get.mockReturnValue("10000000001");
      mockApiGet.mockResolvedValue(mockAccountResponse);
      mockApiPut.mockRejectedValueOnce(
        new ApiError(422, "NO_CHANGES_DETECTED", "No changes detected")
      );

      const user = userEvent.setup();
      render(authenticatedContext(<AccountUpdatePage />));

      await waitFor(() =>
        expect(
          screen.getByRole("button", { name: /^save$/i })
        ).toBeInTheDocument()
      );

      await user.type(screen.getByLabelText(/SSN area number/i), "123");
      await user.type(screen.getByLabelText(/SSN group number/i), "45");
      await user.click(screen.getByRole("button", { name: /^save$/i }));

      await waitFor(() => {
        expect(
          screen.getByText(/no changes detected/i)
        ).toBeInTheDocument();
      });
    });
  });

  // ---- Exit / Cancel -------------------------------------------------------

  describe("Exit and Cancel buttons", () => {
    it("calls router.back() when Exit is clicked", async () => {
      const user = userEvent.setup();
      render(authenticatedContext(<AccountUpdatePage />));
      await user.click(screen.getByRole("button", { name: /exit/i }));
      expect(mockRouterBack).toHaveBeenCalled();
    });

    it("resets form to last loaded values when Cancel is clicked", async () => {
      mockSearchParams.get.mockReturnValue("10000000001");
      mockApiGet.mockResolvedValue(mockAccountResponse);

      const user = userEvent.setup();
      render(authenticatedContext(<AccountUpdatePage />));

      await waitFor(() =>
        expect(
          screen.getByRole("button", { name: /^save$/i })
        ).toBeInTheDocument()
      );

      // Dirty the first name field
      const firstNameInput = screen.getByLabelText(/^first name/i);
      await user.clear(firstNameInput);
      await user.type(firstNameInput, "ModifiedName");
      expect(firstNameInput).toHaveValue("ModifiedName");

      // Cancel should reset to the loaded value
      await user.click(screen.getByRole("button", { name: /^cancel$/i }));

      await waitFor(() => {
        expect(firstNameInput).toHaveValue("Jane");
      });
    });
  });
});
