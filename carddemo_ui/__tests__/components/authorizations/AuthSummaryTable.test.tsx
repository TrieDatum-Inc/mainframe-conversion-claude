import { render, screen, waitFor } from "@testing-library/react";
import AuthSummaryTable from "@/components/authorizations/AuthSummaryTable";

const mockPush = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

jest.mock("@/lib/api", () => ({
  api: {
    get: jest.fn(),
  },
}));

import { api } from "@/lib/api";

const mockResponse = {
  items: [
    {
      pa_acct_id: 12345,
      pa_cust_id: 100,
      pa_auth_status: "00",
      pa_credit_limit: 10000,
      pa_cash_limit: 2000,
      pa_credit_balance: 5000,
      pa_cash_balance: 1000,
      pa_approved_auth_cnt: 15,
      pa_declined_auth_cnt: 2,
    },
  ],
  page: 1,
  page_size: 10,
  total_count: 1,
  has_next_page: false,
};

beforeEach(() => {
  (api.get as jest.Mock).mockReset();
});

describe("AuthSummaryTable", () => {
  it("renders summary data after loading", async () => {
    (api.get as jest.Mock).mockResolvedValueOnce(mockResponse);
    render(<AuthSummaryTable />);

    await waitFor(() => {
      expect(screen.getByText("12345")).toBeInTheDocument();
    });
    expect(screen.getByText("15")).toBeInTheDocument(); // approved count
    expect(screen.getByText("2")).toBeInTheDocument(); // declined count
  });

  it("shows error on failure", async () => {
    (api.get as jest.Mock).mockRejectedValueOnce(new Error("Unauthorized"));
    render(<AuthSummaryTable />);

    await waitFor(() => {
      expect(screen.getByText("Unauthorized")).toBeInTheDocument();
    });
  });
});
