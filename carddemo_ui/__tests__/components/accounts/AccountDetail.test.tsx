import { render, screen, waitFor } from "@testing-library/react";
import AccountDetail from "@/components/accounts/AccountDetail";

// Mock api
jest.mock("@/lib/api", () => ({
  api: {
    get: jest.fn(),
  },
  ApiError: class ApiError extends Error {
    status: number;
    constructor(message: string, status: number) {
      super(message);
      this.status = status;
    }
  },
}));

import { api } from "@/lib/api";

const mockAccount = {
  acct_id: 12345,
  acct_active_status: "Y",
  acct_curr_bal: 5000.5,
  acct_credit_limit: 10000,
  acct_cash_credit_limit: 2000,
  acct_open_date: "2020-01-15",
  acct_expiration_date: "2025-12-31",
  acct_reissue_date: "2024-01-01",
  acct_curr_cyc_credit: 1500,
  acct_curr_cyc_debit: 500,
  acct_addr_zip: "10001",
  acct_group_id: "GRP001",
  cust_id: 100,
  cust_first_name: "John",
  cust_last_name: "Doe",
};

beforeEach(() => {
  (api.get as jest.Mock).mockReset();
});

describe("AccountDetail", () => {
  it("shows loading spinner initially", () => {
    (api.get as jest.Mock).mockReturnValue(new Promise(() => {})); // never resolves
    render(<AccountDetail acctId="12345" />);
    expect(document.querySelector(".animate-spin")).toBeInTheDocument();
  });

  it("displays account information after loading", async () => {
    (api.get as jest.Mock).mockResolvedValueOnce(mockAccount);
    render(<AccountDetail acctId="12345" />);

    await waitFor(() => {
      expect(screen.getByText("12345")).toBeInTheDocument();
    });
    expect(screen.getByText("Active")).toBeInTheDocument();
    expect(screen.getByText("GRP001")).toBeInTheDocument();
    expect(screen.getByText("$5,000.50")).toBeInTheDocument();
    expect(screen.getByText("$10,000.00")).toBeInTheDocument();
  });

  it("displays customer information", async () => {
    (api.get as jest.Mock).mockResolvedValueOnce(mockAccount);
    render(<AccountDetail acctId="12345" />);

    await waitFor(() => {
      expect(screen.getByText("John Doe")).toBeInTheDocument();
    });
    expect(screen.getByText("100")).toBeInTheDocument();
  });

  it("shows error message on API failure", async () => {
    (api.get as jest.Mock).mockRejectedValueOnce(new Error("Account not found"));
    render(<AccountDetail acctId="99999" />);

    await waitFor(() => {
      expect(screen.getByText("Account not found")).toBeInTheDocument();
    });
  });

  it("calls API with correct account ID", async () => {
    (api.get as jest.Mock).mockResolvedValueOnce(mockAccount);
    render(<AccountDetail acctId="12345" />);

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith("/api/accounts/12345");
    });
  });
});
